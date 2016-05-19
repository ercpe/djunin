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

	def __init__(self, scope_name):
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

		self._datarows = None
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
			pass

		return self._datarows

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

	def generate(self, node, graph):
		raise NotImplementedError


class FlotGraphDataGenerator(GraphDataGenerator):

	def __init__(self, scope_name):
		super(FlotGraphDataGenerator, self).__init__(scope_name)

		self.datarows = None

	def generate(self, node, graph):
		d = {
			'graph_name': graph.name,
			'options': self.generate_graph_options(node, graph),
			'datarows': list(self.generate_datarows(node, graph)),
			'_meta': self.get_meta_options(node, graph),
		}

		if graph.graph_args_rigid or (graph.graph_args_lower_limit and all([dr['min_value'] > graph.graph_args_lower_limit for dr in d['datarows']])):
			d['options']['yaxis']['min'] = graph.graph_args_lower_limit
		if graph.graph_args_rigid or (graph.graph_args_upper_limit and all([dr['max_value'] < graph.graph_args_upper_limit for dr in d['datarows']])):
			d['options']['yaxis']['max'] = graph.graph_args_upper_limit

		return d, self._start, self._end, self._resolution

	def generate_graph_options(self, node, graph):
		opts = {
			'series': {
				'lines': {
					'show': True,
					'lineWidth': 1,
				},
				'points': {
					'show': False,
					'lineWidth': 1,
				}
			},
			'grid': {
				'backgroundColor': {
					'colors': [ "#fff", "#eee" ]
				},
				'borderWidth': {
					'top': 1,
					'right': 1,
					'bottom': 2,
					'left': 2
				}
			},
			'xaxis': {
				'mode': "time",
			},
			'yaxis': {
				'axisLabelFontSizePixels': 12,
				'axisLabelColour': 'rgb(84, 84, 84)',
			}
		}

		if graph.graph_vlabel:
			opts['yaxis']['axisLabel'] = graph.graph_vlabel.replace('${graph_period}', graph.graph_period or 'second')

		return opts

	def generate_datarows(self, node, graph):
		invert_datarows_names = graph.datarows.filter(do_graph=True).exclude(negative='').values_list('negative', flat=True)
		self.datarows = graph.datarows.all()

		for dr in self.datarows.filter(Q(do_graph=True) | Q(name__in=invert_datarows_names)):
			invert = dr.name in invert_datarows_names
			fill = bool(dr.draw and dr.draw in ('AREASTACK', 'AREA', 'STACK'))

			# set stack to True if this is an AREASTACK oder STACK
			# if it's an AREA, set it only to stack=True if there is at least another stackable data row
			stack = dr.draw in ('AREASTACK', 'STACK') or \
						(dr.draw == 'AREA' and self.datarows.exclude(pk=dr.pk).filter(draw__in=('AREASTACK', 'STACK')).exists())

			data, min_value, max_value = self.get_boundaries(self.get_data(dr))

			flot_opts = {
				'label': dr.label or None,
				'color': "#" + dr.colour if dr.colour else None,
				'stack': stack,
				'lines': {
					'show': True,
					'steps': False,  # make the graph less blurry
					'fill': fill,
				},
				'invert': invert,
				'internal_name': dr.name,
				'description': dr.info,
				'long_description': dr.extinfo
			}
			flot_opts.update({
				'min_value': min_value,
				'max_value': max_value,
				'data': data
			})

			yield flot_opts

	def get_meta_options(self, node, graph):
		return {
			'autoscale': graph.graph_scale,
			'base': graph.graph_args_base or None,
			'scope': self.data_scope_name,
		}

	def get_data(self, datarow, *args):
		def _build_data():
			for k in self.raw_data:
				value = self.raw_data[k].get(datarow.name, None)
				if value is None:
					yield k, value
				else:
					if datarow.cdef:
						r = RPN()
						value = r.calc(datarow.cdef.split(','), self.raw_data[k])
					yield k, round(value, 5)

		return list(_build_data())

	def get_boundaries(self, iterable):
		min_value = None
		max_value = None

		for _, value in iterable:
			if value is None:
				continue

			if min_value is None or value < min_value:
				min_value = value
			if max_value is None or value > max_value:
				max_value = value

		return iterable, min_value, max_value


class D3GraphDataGenerator(GraphDataGenerator):

	def __init__(self, *args, **kwargs):
		super(D3GraphDataGenerator, self).__init__(*args, **kwargs)
		self._y_min = None
		self._y_max = None
		self._graph_data = None

	def generate(self, node, graph):
		self._datarows = graph.datarows.all() # FIXME

		return {
			'yaxis': self.yaxis_opts(graph),
			'datarows': [dr.name for dr in self.datarows],
			'values': self.graph_data,
		}, self._start, self._end, self._resolution

	@property
	def graph_data(self):
		if self._graph_data is None:
			self._graph_data = list(self.raw_data.items())
		return self._graph_data

	@property
	def y_min(self):
		if self._y_min is None:
			self._y_min = min([min(v.values()) for _, v in self.graph_data])
		return self._y_min

	@property
	def y_max(self):
		if self._y_max is None:
			self._y_max = max([max(v.values()) for _, v in self.graph_data])
		return self._y_max

	def yaxis_opts(self, graph):
		opts = {}

		if graph.graph_vlabel:
			opts['label'] = graph.graph_vlabel.replace('${graph_period}', graph.graph_period or 'second')

		if graph.graph_args_rigid or (graph.graph_args_lower_limit and self.y_min > graph.graph_args_lower_limit):
			opts['min'] = graph.graph_args_lower_limit
		if graph.graph_args_rigid or (graph.graph_args_upper_limit and self.y_max < graph.graph_args_upper_limit):
			opts['max'] = graph.graph_args_upper_limit

		return opts
