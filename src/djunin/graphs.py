# -*- coding: utf-8 -*-
from collections import OrderedDict
from django.core.urlresolvers import reverse


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
					}
				}

		return OrderedDict(_gen())


class FlotGraphDataGenerator(GraphDataGenerator):

	def generate(self, node, graph):

		def _gen():
			for i, dr in enumerate(graph.datarows.all()):
				dr_opts = dict(((dro.key, dro.value) for dro in dr.options.all()))

				flot_opts = {
					'label': dr_opts.get('label', dr.name),
					'data': [[x, i*x] for x in range(1, 50)],
				}

				yield flot_opts

		return {
			'graph_name': graph.name,
			'datarows': list(_gen()),
		}
