# -*- coding: utf-8 -*-
import itertools
import os
import re

from django.conf import settings

line_re = re.compile("^(?P<group_name>.+);(?P<node_name>[^:]+):(?P<graph>[^\.]+)\.(?P<key>[^\s]+?) (?P<value>.*)$")

class Node(object):

	def __init__(self, group, name, graphs=None):
		self.group = group
		self.name = name
		self.graphs = graphs or []

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.__str__()


class Graph(object):
	def __init__(self, name, options=None, data_rows=None, subgraphs=None):
		self.name = name
		self.options = options or {}
		self.datarows = data_rows or {}
		self.subgraphs = subgraphs or {}

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.__str__()


class MuninDataFile(object):

	def __init__(self):
		self._nodes = None

		with open(os.path.join(settings.MUNIN_DATA_DIR, 'datafile'), 'r') as f:
			self.parse(f.readlines()[1:])

	def parse(self, lines):
		self._nodes = []

		d = {}

		for line in lines:
			m = line_re.match(line)

			key = m.group('key')
			key_chunks = key.split('.')
			group_name, node_name, graph_name, value = m.group('group_name'), m.group('node_name'), m.group('graph'), m.group('value')

			if group_name not in d:
				d[group_name] = {}

			if node_name not in d[group_name]:
				d[group_name][node_name] = {}

			if graph_name not in d[group_name][node_name]:
				d[group_name][node_name][graph_name] = {
					'options': {},
					'datarows': {},
					'subgraphs': {}
				}

			if len(key_chunks) == 1:
				assert key.startswith('graph_') or key == 'host_name', "Key should start with 'graph_': %s" % key
				d[group_name][node_name][graph_name]['options'][key] = value
			elif len(key_chunks) == 2:
				a, b = key_chunks

				if b.startswith('graph_') and b != 'graph_data_size':
					# this is a graph option for a subgraph

					if a not in d[group_name][node_name][graph_name]['subgraphs']:
						d[group_name][node_name][graph_name]['subgraphs'][a] = {
							'options': {},
							'datarows': {}
						}

					d[group_name][node_name][graph_name]['subgraphs'][a]['options'][b] = value
				else:
					# this this is an option of a datarow of a parent graph
					if a not in d[group_name][node_name][graph_name]['datarows']:
						d[group_name][node_name][graph_name]['datarows'][a] = {}
					d[group_name][node_name][graph_name]['datarows'][a][b]= value

			elif len(key_chunks) == 3:
				subgraph, datarow, key = key_chunks
				if subgraph not in d[group_name][node_name][graph_name]['subgraphs']:
					d[group_name][node_name][graph_name]['subgraphs'] = {
						subgraph: {
							'options': {},
							'datarows': {}
						}
					}
				if datarow not in d[group_name][node_name][graph_name]['subgraphs'][subgraph]['datarows']:
					d[group_name][node_name][graph_name]['subgraphs'][subgraph]['datarows'][datarow] = {}
				d[group_name][node_name][graph_name]['subgraphs'][subgraph]['datarows'][datarow][key] = value

		for group_name, nodes in d.items():
			for node_name, graphs in nodes.items():

				node_graphs = []

				for graph_name, graph_data in graphs.items():
					subgraphs = {}
					for subgraph_name, subgraph_data in graph_data.get('subgraphs', {}).items():
						subgraphs[subgraph_name] = Graph(subgraph_name, subgraph_data['options'], subgraph_data['datarows'])
					g = Graph(graph_name, graph_data['options'], graph_data['datarows'], subgraphs)
					node_graphs.append(g)

				n = Node(group_name, node_name, graphs=node_graphs)
				self._nodes.append(n)

	@property
	def nodes(self):
		return sorted(self._nodes, key=lambda x: (x.group, x.name))
