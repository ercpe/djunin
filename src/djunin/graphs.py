# -*- coding: utf-8 -*-
import os
from collections import OrderedDict
import logging

import rrdtool

import datetime
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q

logger = logging.getLogger(__file__)

SCOPE_DAY = 1
SCOPE_WEEK = 2
SCOPE_MONTH = 3
SCOPE_YEAR = 4
SCOPE_RANGE = 5


class GraphOptsGenerator(object):

	def generate(self, node, graphs):
		raise NotImplementedError


class GraphDataGenerator(object):

	def generate(self, node, graph):
		raise NotImplementedError


class FlotGraphOptsGenerator(GraphOptsGenerator):

	def generate(self, node, graph):
		stack = any(((dr.draw or '') == 'STACK' for dr in graph.datarows.all()))
		opts = {
			'series': {
				'stack': stack,
				'lines': {
					'show': True,
					'fill': stack,
					'steps': stack,
				},
				# 'bars': {
				# 	'show': stack and False,
				# 	'barWidth': 0,
				# },
				'points': {
					'show': False
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
				'mode': "time"
			},
			'yaxis': {}
		}

		if graph.graph_args_lower_limit is not None:
			opts['yaxis']['min'] = graph.graph_args_lower_limit
		if graph.graph_args_upper_limit is not None:
			opts['yaxis']['max'] = graph.graph_args_upper_limit

		return opts


class FlotGraphDataGenerator(GraphDataGenerator):

	def generate(self, node, graph, data_scope=SCOPE_DAY):
		def _gen():
			invert_datarows = graph.datarows.filter(do_graph=True).exclude(negative='').values_list('negative', flat=True)
			graph_datarows = graph.datarows.filter(Q(do_graph=True) | Q(do_graph=False, name__in=invert_datarows)).order_by('name')

			if graph.graph_order:
				db_datarows = list(graph_datarows)
				datarows = OrderedDict()
				for dr_name in graph.graph_order.split(' '):
					if dr_name not in datarows:
						datarows[dr_name] = [x for x in db_datarows if x.name == dr_name][0]
				datarows = datarows.values()
			else:
				datarows = graph_datarows

			logger.debug("Sorted datarows: %s", [dr.name for dr in datarows])
			logger.debug("Graph order:     %s", graph.graph_order)

			for dr in datarows:
				flot_opts = {
					'label': dr.label or None,
					'data': self.get_data(dr, str(os.path.join(settings.MUNIN_DATA_DIR, dr.rrdfile)), data_scope, dr.name in invert_datarows, 'AVERAGE'),
					'color': "#" + dr.colour if dr.colour else None,
				}

				yield flot_opts

		return list(_gen())

	def get_data(self, datarow, datafile, data_scope, invert, *args):
		date_range = ""
		if data_scope == SCOPE_DAY:
			date_range = "-s -28h"
		elif data_scope == SCOPE_WEEK:
			date_range = "-s -176h"
		elif data_scope == SCOPE_MONTH:
			date_range = "-s -756h"

		(start, end, resolution), (no,), data = rrdtool.fetch([datafile, 'AVERAGE', date_range])
		return zip(
			(x * 1000 for x in xrange(start, end, resolution)),
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