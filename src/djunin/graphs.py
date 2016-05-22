# -*- coding: utf-8 -*-
import os
from collections import OrderedDict
import logging

import rrdtool

from django.conf import settings
from django.db.models import Q

from rpn import RPN

logger = logging.getLogger(__file__)

SCOPE_DAY = 1
SCOPE_WEEK = 2
SCOPE_MONTH = 3
SCOPE_YEAR = 4
SCOPE_RANGE = 5


class GraphDataGenerator(object):

	def __init__(self, node, graph, scope_name):
		self.data_scope_name = scope_name
		if scope_name == 'day':
			self.data_scope = SCOPE_DAY
		elif scope_name == 'week':
			self.data_scope = SCOPE_WEEK
		elif scope_name == 'month':
			self.data_scope = SCOPE_MONTH
		elif scope_name == 'year':
			self.data_scope = SCOPE_YEAR
		else:
			raise ValueError("Unknown scope '%s'" % scope_name)

		self.node = node
		self.graph = graph
		self._datarows = None
		self._datarow_cdefs = None
		self._raw_data = None
		self._start = None
		self._end = None
		self._resolution = None
		self._rrdcached = getattr(settings, 'RRDCACHED', None)
		self._flush_rrdcached_before_fetch = getattr(settings, 'FLUSH_BEFORE_FETCH', False)

	@property
	def raw_data(self):
		if self._raw_data is None:
			self._raw_data = self._read_data()
		return self._raw_data

	@property
	def datarows(self):
		if self._datarows is None:
			self._datarows = self.graph.datarows.all()
		return self._datarows

	@property
	def cdefs(self):
		if self._datarow_cdefs is None:
			self._datarow_cdefs = dict(self.datarows.filter(name__endswith='_mem').exclude(cdef=None).values_list('name', 'cdef'))
		return self._datarow_cdefs

	def _read_data(self):

		d = OrderedDict()
		for dr in self.datarows:
			datafile = str(os.path.join(settings.MUNIN_DATA_DIR, dr.rrdfile))

			if self._flush_rrdcached_before_fetch and self._rrdcached:
				try:
					rrdtool.flushcached(['--daemon', self._rrdcached, datafile])
				except:
					logger.exception("Could not flushrrdcached at %s", self._rrdcached)

			date_range = ""
			if self.data_scope == SCOPE_DAY:
				date_range = "-s -28h"
			elif self.data_scope == SCOPE_WEEK:
				date_range = "-s -176h"
			elif self.data_scope == SCOPE_MONTH:
				date_range = "-s -756h"
			elif self.data_scope == SCOPE_YEAR:
				date_range = "-s -365d"

			(self._start, self._end, self._resolution), (no,), data = rrdtool.fetch([datafile, 'AVERAGE', date_range])

			for dt, value in zip(
					(x * 1000 for x in xrange(self._start, self._end - self._resolution, self._resolution)),
					(x[0] for x in data)
			):

				if dt not in d:
					d[dt] = {}

				d[dt][dr.name] = value

		return d

	def generate(self):
		raise NotImplementedError

# class FlotGraphDataGenerator(GraphDataGenerator):
#
# 	def __init__(self, scope_name):
# 		super(FlotGraphDataGenerator, self).__init__(scope_name)
#
# 		self.datarows = None
#
# 	def generate(self, node, graph):
# 		d = {
# 			'graph_name': graph.name,
# 			'options': self.generate_graph_options(node, graph),
# 			'datarows': list(self.generate_datarows(node, graph)),
# 			'_meta': self.get_meta_options(node, graph),
# 		}
#
# 		if graph.graph_args_rigid or (graph.graph_args_lower_limit and all([dr['min_value'] > graph.graph_args_lower_limit for dr in d['datarows']])):
# 			d['options']['yaxis']['min'] = graph.graph_args_lower_limit
# 		if graph.graph_args_rigid or (graph.graph_args_upper_limit and all([dr['max_value'] < graph.graph_args_upper_limit for dr in d['datarows']])):
# 			d['options']['yaxis']['max'] = graph.graph_args_upper_limit
#
# 		return d, self._start, self._end, self._resolution
#
# 	def generate_graph_options(self, node, graph):
# 		opts = {
# 			'series': {
# 				'lines': {
# 					'show': True,
# 					'lineWidth': 1,
# 				},
# 				'points': {
# 					'show': False,
# 					'lineWidth': 1,
# 				}
# 			},
# 			'grid': {
# 				'backgroundColor': {
# 					'colors': [ "#fff", "#eee" ]
# 				},
# 				'borderWidth': {
# 					'top': 1,
# 					'right': 1,
# 					'bottom': 2,
# 					'left': 2
# 				}
# 			},
# 			'xaxis': {
# 				'mode': "time",
# 			},
# 			'yaxis': {
# 				'axisLabelFontSizePixels': 12,
# 				'axisLabelColour': 'rgb(84, 84, 84)',
# 			}
# 		}
#
# 		if graph.graph_vlabel:
# 			opts['yaxis']['axisLabel'] = graph.graph_vlabel.replace('${graph_period}', graph.graph_period or 'second')
#
# 		return opts
#
# 	def generate_datarows(self, node, graph):
# 		invert_datarows_names = graph.datarows.filter(do_graph=True).exclude(negative='').values_list('negative', flat=True)
# 		self.datarows = graph.datarows.all()
#
# 		for dr in self.datarows.filter(Q(do_graph=True) | Q(name__in=invert_datarows_names)):
# 			invert = dr.name in invert_datarows_names
# 			fill = bool(dr.draw and dr.draw in ('AREASTACK', 'AREA', 'STACK'))
#
# 			# set stack to True if this is an AREASTACK oder STACK
# 			# if it's an AREA, set it only to stack=True if there is at least another stackable data row
# 			stack = dr.draw in ('AREASTACK', 'STACK') or \
# 						(dr.draw == 'AREA' and self.datarows.exclude(pk=dr.pk).filter(draw__in=('AREASTACK', 'STACK')).exists())
#
# 			data, min_value, max_value = self.get_boundaries(self.get_data(dr))
#
# 			flot_opts = {
# 				'label': dr.label or None,
# 				'color': "#" + dr.colour if dr.colour else None,
# 				'stack': stack,
# 				'lines': {
# 					'show': True,
# 					'steps': False,  # make the graph less blurry
# 					'fill': fill,
# 				},
# 				'invert': invert,
# 				'internal_name': dr.name,
# 				'description': dr.info,
# 				'long_description': dr.extinfo
# 			}
# 			flot_opts.update({
# 				'min_value': min_value,
# 				'max_value': max_value,
# 				'data': data
# 			})
#
# 			yield flot_opts
#
# 	def get_meta_options(self, node, graph):
# 		return {
# 			'autoscale': graph.graph_scale,
# 			'base': graph.graph_args_base or None,
# 			'scope': self.data_scope_name,
# 		}
#
# 	def get_data(self, datarow, *args):
# 		def _build_data():
# 			for k in self.raw_data:
# 				value = self.raw_data[k].get(datarow.name, None)
# 				if value is None:
# 					yield k, value
# 				else:
# 					if datarow.cdef:
# 						r = RPN()
# 						value = r.calc(datarow.cdef.split(','), self.raw_data[k])
# 					yield k, round(value, 5)
#
# 		return list(_build_data())
#
# 	def get_boundaries(self, iterable):
# 		min_value = None
# 		max_value = None
#
# 		for _, value in iterable:
# 			if value is None:
# 				continue
#
# 			if min_value is None or value < min_value:
# 				min_value = value
# 			if max_value is None or value > max_value:
# 				max_value = value
#
# 		return iterable, min_value, max_value


class D3GraphDataGenerator(GraphDataGenerator):

	def __init__(self, *args, **kwargs):
		super(D3GraphDataGenerator, self).__init__(*args, **kwargs)
		self._y_min = None
		self._y_max = None
		self._graph_data = None
		self._invert_datarow_names = None

	def generate(self):
		return {
			'yaxis': self.yaxis_opts(),
			'datarows': self.get_datarows_options(),
			'values': self.graph_data,
		}, self._start, self._end, self._resolution

	@property
	def graph_data(self):
		if self._graph_data is None:
			self._graph_data = self.build_graph_data()
		return self._graph_data

	@property
	def y_min(self):
		if self._y_min is None:
			self._y_min = self._apply_graph_data_values_func(min)
		return self._y_min

	@property
	def y_max(self):
		if self._y_max is None:
			self._y_max = max([max(v.values()) for _, v in self.graph_data])
		return self._y_max

	@property
	def invert_datarow_names(self):
		if self._invert_datarow_names is None:
			self._invert_datarow_names = list(
				self.datarows.filter(name__in=self.datarows.exclude(negative='').values_list('negative', flat=True)).values_list('name', flat=True)
			)
		return self._invert_datarow_names

	def _apply_graph_data_values_func(self, func, inner_func=None):
		def _func_wrapper(f, values):
			try:
				return f(values)
			except ValueError:
				return None

		outer_func = func
		inner_func = inner_func or func

		outer = lambda v: _func_wrapper(outer_func, v)
		inner = lambda v: _func_wrapper(inner_func, v)

		return outer([x for x in
							  	[inner([x for x in v.values() if x is not None]) for _, v in self.graph_data]
							 if x is not None])

	def build_graph_data(self):
		def _inner():
			for t, datarows in self.raw_data.items():
				for k, v in datarows.items():
					value = v

					if value is not None:
						if k in self.cdefs:
							cdef = self.cdefs[k]
							value = RPN().calc(cdef.split(','), {
								k: value
							})
							value = round(value, 5)

						value = value * -1 if k in self.invert_datarow_names else value

					datarows[k] = value
				yield t, datarows

		return list(_inner())

	def get_datarows_options(self):
		all_datarows = self.datarows.filter(do_graph=True)

		datarows = {}

		for dr in all_datarows:
			d = {
				'min': dr.min,
				'max': dr.max,
				'draw': dr.draw,
				'label': dr.label,
				'info': dr.info,
			}

			if dr.negative:
				d['sameas'] = dr.negative

			if dr.colour:
				d['color'] = '#%s' % dr.colour

			datarows[dr.name] = dict(((k, v) for k, v in d.items() if v))

		return datarows

	def yaxis_opts(self):
		opts = {}

		if self.graph.graph_vlabel:
			opts['label'] = self.graph.graph_vlabel.replace('${graph_period}', self.graph.graph_period or 'second')

		any_stacked = any([dr.draw in ('STACK', 'AREASTACK') for dr in self.datarows])
		opts['value_max'] = self._apply_graph_data_values_func(max, sum if any_stacked else max)
		opts['value_min'] = self._apply_graph_data_values_func(min, sum if any_stacked else min)

		if self.graph.graph_args_rigid or (self.graph.graph_args_lower_limit is not None and self.y_min > self.graph.graph_args_lower_limit):
			opts['graph_min'] = self.graph.graph_args_lower_limit
		else:
			any_area = any([dr.draw in ('AREA', 'STACK', 'AREASTACK') for dr in self.datarows])
			if any_area:
				datarows_min = list(self.datarows.exclude(min=None).values_list('min', flat=True))
				if datarows_min:
					opts['graph_min'] = min(datarows_min)

		if self.graph.graph_args_rigid or (self.graph.graph_args_upper_limit is not None and self.y_max < self.graph.graph_args_upper_limit):
			opts['graph_max'] = self.graph.graph_args_upper_limit

		return opts
