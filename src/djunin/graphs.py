# -*- coding: utf-8 -*-
import os
from collections import OrderedDict
import logging

import rrdtool

from django.conf import settings
from django.db.models import Q

logger = logging.getLogger(__file__)

SCOPE_DAY = 1
SCOPE_WEEK = 2
SCOPE_MONTH = 3
SCOPE_YEAR = 4
SCOPE_RANGE = 5


class GraphDataGenerator(object):

	def generate(self, node, graph):
		raise NotImplementedError


class FlotGraphDataGenerator(GraphDataGenerator):

	def __init__(self):
		super(FlotGraphDataGenerator, self).__init__()
		self._start = None
		self._end = None
		self._resolution = None

	def generate(self, node, graph, data_scope=SCOPE_DAY):
		if data_scope == 'day':
			scope = SCOPE_DAY
		elif data_scope == 'week':
			scope = SCOPE_WEEK
		else:
			raise ValueError("Unknown scope '%s'" % data_scope)

		d = {
			'graph_name': graph.name,
			'options': self.generate_graph_options(node, graph, scope),
			'datarows': list(self.generate_datarows(node, graph, scope)),
			'_meta': self.get_meta_options(node, graph, scope),
		}
		d['_meta']['scope'] = data_scope

		return d, self._start, self._end, self._resolution

	def generate_graph_options(self, node, graph, scope):
		#stack = any(((dr.draw or '') in ('STACK', 'AREASTACK') for dr in graph.datarows.all()))
		opts = {
			'series': {
		#		'stack': stack,
				'lines': {
					'show': True,
		#			'fill': stack,
		#			'steps': stack,
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
				'axisLabelColour': 'rgb(84, 84, 84)'
			}
		}

		if graph.graph_args_lower_limit is not None:
			opts['yaxis']['min'] = graph.graph_args_lower_limit
		if graph.graph_args_upper_limit is not None:
			opts['yaxis']['max'] = graph.graph_args_upper_limit

		if graph.graph_vlabel:
			opts['yaxis']['axisLabel'] = graph.graph_vlabel.replace('${graph_period}', graph.graph_period or 'second')

		return opts

	def generate_datarows(self, node, graph, data_scope):
		invert_datarows = graph.datarows.filter(do_graph=True).exclude(negative='').values_list('negative', flat=True)
		graph_datarows = graph.datarows.filter(Q(do_graph=True) | Q(do_graph=False, name__in=invert_datarows)).order_by('name')

		if graph.graph_order:
			db_datarows = list(graph_datarows)
			datarows = OrderedDict()
			for dr_name in graph.graph_order.split(' '):
				if dr_name not in datarows:
					try:
						datarows[dr_name] = [x for x in db_datarows if x.name == dr_name][0]
					except IndexError:
						logger.info("Datarow '%s' not found in %s", dr_name, db_datarows)
			datarows = datarows.values()
		else:
			datarows = graph_datarows

		for dr in datarows:
			flot_opts = {
				'label': dr.label or None,
				'data': self.get_data(dr, str(os.path.join(settings.MUNIN_DATA_DIR, dr.rrdfile)), data_scope, dr.name in invert_datarows, 'AVERAGE'),
				'color': "#" + dr.colour if dr.colour else None,
			}
			if dr.draw and dr.draw in ('AREA', 'STACK'):
				flot_opts['lines'] = {
					'show': True,
					'fill': True,
					'steps': True,
				}
				if dr.draw == 'STACK':
					flot_opts['stack'] = True

			yield flot_opts

	def get_meta_options(self, node, graph, data_scope):
		d = {
			'autoscale': graph.graph_scale,
			'base': graph.graph_args_base or None,
			'scope': data_scope,
		}

		return d

	def get_data(self, datarow, datafile, data_scope, invert, *args):
		date_range = ""
		if data_scope == SCOPE_DAY:
			date_range = "-s -28h"
		elif data_scope == SCOPE_WEEK:
			date_range = "-s -176h"
		elif data_scope == SCOPE_MONTH:
			date_range = "-s -756h"

		(self._start, self._end, self._resolution), (no,), data = rrdtool.fetch([datafile, 'AVERAGE', date_range])
		return zip(
			(x * 1000 for x in xrange(self._start, self._end, self._resolution)),
			self.apply_cdef(datarow, (x[0] for x in data), invert)
		)

	def apply_cdef(self, datarow, data_gen, invert):
		cdef_func = self.parse_rpn(datarow.cdef)

		for raw_value in data_gen:
			if raw_value is None:
				yield raw_value
			else:
				yield round(cdef_func(raw_value) * (-1 if invert else 1), 5)

	def parse_rpn(self, cdef):
		if not cdef:
			return lambda x: x

		chunks = cdef.split(',')
		if len(chunks) != 3:
			logger.error("Don't know what to do with %s" % cdef)

		field, value, operator = chunks

		if operator == '/':
			return lambda x: x / float(value)
		if operator == '*':
			return lambda x: x * float(value)

		raise Exception("Unknown operator: %s" % operator)
