# -*- coding: utf-8 -*-
import os
from collections import OrderedDict
import logging

from django.conf import settings

import rrdtool
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


class D3GraphDataGenerator(GraphDataGenerator):

	def __init__(self, *args, **kwargs):
		super(D3GraphDataGenerator, self).__init__(*args, **kwargs)
		self._y_min = None
		self._y_max = None
		self._datarow_max_value = None
		self._datarow_min_value = None
		self._graph_data = None
		self._datarow_options = None
		self._invert_datarow_names = None

	def generate(self):
		return {
			'datarows': self.datarows_options,
			'yaxis': self.yaxis_opts(),
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
	def datarows_max_value(self):
		if self._datarow_max_value is None:
			max_values = []

			line_datarows = [k for k, v in self.datarows_options.items() if v['draw'] in ('LINE2')]
			for _, datarow_values in self.graph_data:
				line_values = [v for k, v in datarow_values.items() if k in line_datarows and v is not None]
				if line_values:
					max_values.append(max(line_values))
				other_values = [v for k, v in datarow_values.items() if k not in line_datarows and v is not None]
				if other_values:
					max_values.append(sum(other_values))

			if max_values:
				self._datarow_max_value = max(max_values)

		return self._datarow_max_value

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

	@property
	def datarows_options(self):
		if self._datarow_options is None:
			all_datarows = self.datarows.filter(do_graph=True)

			opts = {}

			for dr in all_datarows:
				d = {
					'min': dr.min,
					'max': dr.max,
					'draw': dr.draw or 'LINE2',
					'label': dr.label,
					'info': dr.info,
				}

				if dr.negative:
					d['sameas'] = dr.negative

				if dr.colour:
					d['color'] = '#%s' % dr.colour

				datarow_values = [v[dr.name] for t, v in self.raw_data.items() if v.get(dr.name, None) is not None]
				d['value_min'] = round(min(datarow_values), 2) if datarow_values else None
				d['value_max'] = round(max(datarow_values), 2) if datarow_values else None
				d['value_current'] = round(datarow_values[-1], 2) if datarow_values else None

				opts[dr.name] = dict(((k, v) for k, v in d.items() if v))

			# get the graph datarow order
			order_names = [x.strip() for x in (self.graph.graph_order or '').split()]
			# add all missing datarow names to the end of the list
			order_names.extend(set(opts.keys()) - set(order_names))

			# create sorted dict according to the order
			self._datarow_options = OrderedDict(sorted(opts.items(), cmp=lambda a, b: cmp(order_names.index(a[0]), order_names.index(b[0]))))

		return self._datarow_options

	def yaxis_opts(self):
		opts = {}

		if self.graph.graph_vlabel:
			opts['label'] = self.graph.graph_vlabel.replace('${graph_period}', self.graph.graph_period or 'second')

		any_stacked = any([dr.draw in ('STACK', 'AREASTACK') for dr in self.datarows])
		opts['value_max'] = self.datarows_max_value # self._apply_graph_data_values_func(max, sum if any_stacked else max)
		opts['value_min'] = self._apply_graph_data_values_func(min, sum if any_stacked else min)

		#logger.info("Value max: %s vs %s", opts['value_max'], self.datarows_max_value)

		if self.graph.graph_args_rigid or (self.graph.graph_args_lower_limit is not None and self.y_min >= self.graph.graph_args_lower_limit):
			opts['graph_min'] = self.graph.graph_args_lower_limit
		else:
			any_area = any([dr.draw in ('AREA', 'STACK', 'AREASTACK') for dr in self.datarows])
			if any_area:
				datarows_min = list(self.datarows.exclude(min=None).values_list('min', flat=True))
				if datarows_min:
					opts['graph_min'] = min(datarows_min)

		if self.graph.graph_args_rigid or (self.graph.graph_args_upper_limit is not None and self.y_max <= self.graph.graph_args_upper_limit):
			opts['graph_max'] = self.graph.graph_args_upper_limit

		return opts
