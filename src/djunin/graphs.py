# -*- coding: utf-8 -*-
import os
from collections import OrderedDict
import logging

import rrdtool

from django.conf import settings
from django.core.urlresolvers import reverse

logger = logging.getLogger(__file__)

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
				yield graph.name, {
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
				}

		return OrderedDict(_gen())


class FlotGraphDataGenerator(GraphDataGenerator):

	def generate(self, node, graph):

		def _gen():
			for dr in graph.datarows.all():
				(start, end, resolution), (no,), data = rrdtool.fetch([str(os.path.join(settings.MUNIN_DATA_DIR, dr.rrdfile)), 'AVERAGE'])
				logger.debug("From %s to %s every %s sec", start, end, resolution)

				dr_opts = dict(((dro.key, dro.value) for dro in dr.options.all()))

				flot_opts = {
					'label': dr_opts.get('label', dr.name),
					'data': zip(xrange(start, end, resolution), (x[0] for x in data)),
				}

				yield flot_opts

		return {
			'graph_name': graph.name,
			'datarows': list(_gen()),
		}
