# -*- coding: utf-8 -*-
import os
from collections import OrderedDict
import logging

import rrdtool

import datetime
from django.conf import settings
from django.core.urlresolvers import reverse

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

	def generate(self, node, graphs):
		def _gen():
			for graph in graphs:
				opts = {
					'data_url': reverse('graph_data', args=(node.group, node.name, graph.name)),
					'series': {
						'lines': {
							'show': True
						},
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
					opts['yaxis']['upper'] = graph.graph_args_upper_limit

				yield graph.name, opts

		return OrderedDict(_gen())


class FlotGraphDataGenerator(GraphDataGenerator):

	def generate(self, node, graph, data_scope=SCOPE_DAY):
		def _gen():

			if graph.graph_order:
				db_datarows = list(graph.datarows.all())
				datarows = []
				for dr_name in graph.graph_order.split(' '):
					datarows.append([x for x in db_datarows if x.name == dr_name][0])
			else:
				datarows = graph.datarows.order_by('name')

			for dr in datarows:
				flot_opts = {
					'label': dr.label or None,
					'data': self.get_data(str(os.path.join(settings.MUNIN_DATA_DIR, dr.rrdfile)), data_scope, 'AVERAGE')
				}

				yield flot_opts

		return {
			'graph_name': graph.name,
			'datarows': list(_gen()),
		}

	def get_data(self, datafile, data_scope, *args):
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
			(x[0] for x in data)
		)