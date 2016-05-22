# -*- coding: utf-8 -*-

import os
import argparse
import shlex
import itertools
import logging
import collections

from django.conf import settings
from django.db import transaction

from pyparsing import Word, alphanums, Suppress, Regex, White, ParseException, Optional, Group, Combine

from djunin.models import Node, Graph, DataRow

chars = alphanums + '-_'
host_service_chars = chars + '.'

# covers group;node:graph.
base_pattern = Word(host_service_chars).setResultsName('group') + Suppress(';') + \
				Word(host_service_chars).setResultsName('host') + Suppress(':') + \
				Word(chars).setResultsName('graph') + Suppress('.')

key_value = Word(chars).setResultsName('attribute') + Suppress(White(' ', exact=1)) + Regex('.*').setResultsName('value')

# Note: subgraph_attributes and root_graph_datarow_attributes are only distinguishable by the fact
#       that root graph attributes start with 'graph_', except for graph_data_size which can be found
#       in subgraph attributes
abc = ~Group('graph_data_size') + Group(Combine(Group('graph_' + Word(chars))))
graph_attribute_key_value = ~Group('graph_data_size') + Combine(Group('graph_' + Word(chars))).setResultsName('attribute') + \
									Suppress(White(' ', exact=1)) + Regex('.*').setResultsName('value')

subgraph_pattern = Word(chars).setResultsName('subgraph') + Suppress('.')
datarow_pattern = Word(chars).setResultsName('datarow') + Suppress('.')

# group;node:graph.attribute value
root_graph_attributes = base_pattern + key_value

# group;node:graph.datarow.attribute value
root_graph_datarow_attributes = base_pattern + datarow_pattern + key_value

# group;node:graph.subgraph.attribute value
subgraph_attributes = base_pattern + subgraph_pattern + graph_attribute_key_value

# group;node:graph.subgraph.datarow.attribute value
subgraph_datarow_attributes = base_pattern + subgraph_pattern + datarow_pattern + key_value

patterns = [
	subgraph_datarow_attributes,
	subgraph_attributes,
	root_graph_datarow_attributes,
	root_graph_attributes,
]

Row = collections.namedtuple('DataRow', ('group', 'node', 'graph', 'subgraph', 'datarow', 'attribute', 'value'))

logger = logging.getLogger(__file__)

class Updater(object):

	def __init__(self, datafile=None):
		self.datafile = datafile or os.path.join(settings.MUNIN_DATA_DIR, 'datafile')
		self.graphs = None
		self.nodes = None

	def run(self):
		with open(self.datafile) as fp:
			data = self.prepare(fp)

			with transaction.atomic():
				self.update(list(data))

	def prepare(self, fp):
		def _read_and_parse():
			for i, line in enumerate((x.strip() for x in fp.readlines())):
				if i == 0:
					continue

				m = None
				for p in patterns:
					try:
						m = p.parseString(line, parseAll=True)

						fields = m['group'], m['host'], m['graph'], m.get('subgraph', None), m.get('datarow', None), \
								m['attribute'], m['value']

						#logging.debug("%-30s%-30s%-30s%-30s%-30s%-30s%s", *fields)
						yield Row(*fields)
						break
					except ParseException:
						continue

				if not m:
					logger.error("No pattern matched line: %s", line)

		for f in _read_and_parse():
			yield f

	def update(self, data):
		# Create nodes
		logger.info("Creating nodes")
		Node.objects.all().delete()

		Node.objects.bulk_create((
			Node(group=group, name=node) for group, node in set([(row.group, row.node) for row in data])
		))
		self.nodes = dict((((n.group, n.name), n) for n in Node.objects.all()))

		# create root graphs
		self.create_root_graphs(data)
		self.graphs = dict((
			((g.node.group, g.node.name, g.name), g) for g in Graph.objects.filter(parent=None).select_related('node')
		))

		# create subgraphs
		logger.info("Creating sub graphs")
		self.create_subgraphs(data)

		self.graphs = dict(
			self.graphs.items() +
			[((g.node.group, g.node.name, g.parent.name, g.name), g) for g in Graph.objects.exclude(parent=None).select_related('node', 'parent')]
		)

		# create datarows
		logger.info("Creating datarows")
		self.create_datarows(data)

	def create_root_graphs(self, data):
		logger.info("Creating root graphs")
		root_graph_filter = lambda row: row.subgraph is None and row.datarow is None
		root_graph_grouped = itertools.groupby(filter(root_graph_filter, data),
											   lambda row: (row.group, row.node, row.graph))

		def _build_root_graphs():
			for group_key, items in root_graph_grouped:
				group, node, graph_name = group_key
				g = Graph(node=self.nodes[(group, node)], name=graph_name)

				for _, _, _, _, _, key, value in items:
					setattr(g, key, value)
					if key == 'graph_args' and value:
						for k, v in self.parse_graph_args(value).items():
							setattr(g, k, v)
				if not g.graph_category:
					g.graph_category = 'other'
				g.graph_category = (g.graph_category or '').lower() or 'other'
				yield g

		Graph.objects.bulk_create(_build_root_graphs())

	def create_subgraphs(self, data):
		# group.node.graph.attribute = value
		# group.node.graph.datarow.attribute = value
		# group.node.graph.subgraph.attribute = value
		# group.node.graph.subgraph.datarow.attribute = value

		subgraph_filter = lambda row: row.subgraph is not None and row.datarow is None
		subgraph_grouped = itertools.groupby(filter(subgraph_filter, data), lambda row: (row.group, row.node, row.graph, row.subgraph))

		def _build_subgraphs():
			for group_key, items in subgraph_grouped:
				group, node, root_graph_name, graph_name = group_key
				g = Graph(node=self.nodes[(group, node)],
						  parent=self.graphs[(group, node, root_graph_name)],
						  name=graph_name)
				g.graph_category = g.parent.graph_category or 'other'

				for _, _, _, _, _, key, value in items:
					setattr(g, key, value)
					if key == 'graph_args' and value:
						for k, v in self.parse_graph_args(value).items():
							setattr(g, k, v)
				yield g

		Graph.objects.bulk_create(_build_subgraphs())

	def create_datarows(self, data):
		datarow_filter = lambda row: row.datarow is not None
		datarow_grouped = itertools.groupby(filter(datarow_filter, data), lambda row: (row.group, row.node, row.graph, row.subgraph, row.datarow))

		def _build_datarows():
			for group_key, items in datarow_grouped:
				group, node, root_graph_name, graph_name, datarow_name = group_key

				graph_key = (group, node, root_graph_name, graph_name) if graph_name else (
				group, node, root_graph_name)
				graph = self.graphs[graph_key]

				dropts = dict(
					(key, value) for _, _, _, _, _, key, value in items
				)

				if 'graph' in dropts:
					dropts['do_graph'] = dropts['graph']
					del dropts['graph']

				# set empty values to None
				for k in dropts.keys():
					dropts[k] = (dropts[k] or '').strip() or None

				dr = DataRow(graph=graph, name=datarow_name,
							 rrdfile=self.get_rrdfilename(graph, datarow_name, dropts),
							 **dropts)

				yield dr

		DataRow.objects.bulk_create(_build_datarows())

	def parse_graph_args(self, args_s):
		if not (args_s or "").strip():
			return {}

		parser = argparse.ArgumentParser(add_help=False)
		parser.add_argument('-s', '--start')
		parser.add_argument('-e', '--end')
		parser.add_argument('-S', '--step')
		parser.add_argument('-t', '--title')
		parser.add_argument('-v', '--vertical-label')
		parser.add_argument('-w', '--width')
		parser.add_argument('-h', '--height')
		parser.add_argument('-j', '--only-graph', action='store_true')
		parser.add_argument('-D', '--full-size-mode', action='store_true')
		parser.add_argument('-u', '--upper-limit')
		parser.add_argument('-l', '--lower-limit')
		parser.add_argument('-r', '--rigid', action='store_true')
		parser.add_argument('-A', '--alt-autoscale', action='store_true')
		parser.add_argument('-J', '--alt-autoscale-min')
		parser.add_argument('-M', '--alt-autoscale-max')
		parser.add_argument('-N', '--no-gridfit')
		parser.add_argument('-x', '--x-grid')
		parser.add_argument('--week-fmt')
		parser.add_argument('-y', '--y-grid')
		parser.add_argument('--left-axis-formatter')
		parser.add_argument('--left-axis-format')
		parser.add_argument('-Y', '--alt-y-grid', action='store_true')
		parser.add_argument('-o', '--logarithmic', action='store_true')
		parser.add_argument('-X', '--units-exponent')
		parser.add_argument('-L', '--units-length')
		parser.add_argument('--units')
		parser.add_argument('--right-axis')
		parser.add_argument('--right-axis-label')
		parser.add_argument('--right-axis-formatter')
		parser.add_argument('--right-axis-format')
		parser.add_argument('-g', '--no-legend', action='store_true')
		parser.add_argument('-F', '--force-rules-legend', action='store_true')
		parser.add_argument('--legend-position')
		parser.add_argument('--legend-direction')
		parser.add_argument('-z', '--lazy', action='store_true')
		parser.add_argument('-d', '--daemon')
		parser.add_argument('-f', '--imginfo')
		parser.add_argument('-c', '--color')
		parser.add_argument('--grid-dash')
		parser.add_argument('--border')
		parser.add_argument('--dynamic-labels', action='store_true')
		parser.add_argument('-m', '--zoom')
		parser.add_argument('-n', '--font')
		parser.add_argument('-R', '--font-render-mode')
		parser.add_argument('-B', '--font-smoothing-threshold')
		parser.add_argument('-P', '--pango-markup', action='store_true')
		parser.add_argument('-G', '--graph-render-mode')
		parser.add_argument('-E', '--slope-mode', action='store_true')
		parser.add_argument('-a', '--imgformat')
		parser.add_argument('-i', '--interlaced', action='store_true')
		parser.add_argument('-T', '--tabwidth')
		parser.add_argument('-b', '--base')
		parser.add_argument('-W', '--watermark')
		parser.add_argument('-Z', '--use-nan-for-all-missing-data', action='store_true')

		try:
			x = parser.parse_args(shlex.split(args_s))

			supported_args = 'base', 'lower_limit', 'upper_limit', 'rigid'
			return dict(("graph_args_%s" % a, getattr(x, a, None)) for a in supported_args if getattr(x, a, None))
		except:
			logger.exception("Could not parse args '%s'", args_s)
			return {}

	def get_rrdfilename(self, graph, datarow_name, datarow_options):
		dr_type_name = datarow_options.get('type', 'GAUGE')

		pattern = "{group}/{node}-{graph}-{datarow}-{datarow_type}.rrd"
		if graph.parent:
			pattern = "{group}/{node}-{graph}-{subgraph}-{datarow}-{datarow_type}.rrd"

		return pattern.format(group=graph.node.group, node=graph.node.name,
							  graph=graph.parent.name if graph.parent else graph.name,
							  subgraph=graph.name if graph.parent else None,
							  datarow=datarow_name, datarow_type=dr_type_name.lower()[0])
