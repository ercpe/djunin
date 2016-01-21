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

		def _gen(lines):
			for line in sorted(lines):
				m = line_re.match(line)

				key = m.group('key')
				key_chunks = key.split('.')
				key = key_chunks[-1]
				chunks_len = len(key_chunks)
				datarow = key_chunks[-2] if chunks_len >= 2 else None
				subgraph = key_chunks[-3] if chunks_len >= 3 else None
				value = m.group('value')

				yield (m.group('group_name'), m.group('node_name'), m.group('graph'), subgraph or None, datarow, key, value)

		for group_name, group_lines in itertools.groupby(sorted(_gen(lines)), lambda item: item[0]):
			group_lines = sorted([x[1:] for x in group_lines])

			for node_name, node_lines in itertools.groupby(group_lines, lambda item: item[0]):
				node_lines = [x[1:] for x in node_lines]

				graphs = []

				for graph_name, graph_lines in itertools.groupby(node_lines, lambda item: item[0]):
					graph_lines = sorted([x[1:] for x in graph_lines])

					graph = Graph(graph_name)

					for subgraph_name, subgraph_lines in itertools.groupby(graph_lines, lambda item: item[0]):
						subgraph_lines = sorted([x[1:] for x in subgraph_lines])

						for datarow, key, value in subgraph_lines:
							if subgraph_name:
								if subgraph_name not in graph.subgraphs:
									graph.subgraphs[subgraph_name] = Graph(subgraph_name)

								if datarow:
									if datarow not in graph.subgraphs[subgraph_name].datarows:
										graph.subgraphs[subgraph_name].datarows[datarow] = {}
									graph.subgraphs[subgraph_name].datarows[datarow][key] = value
								else:
									graph.subgraphs[subgraph_name].options[key] = value
							else:
								if datarow:
									if datarow not in graph.datarows:
										graph.datarows[datarow] = {}
									graph.datarows[datarow][key] = value
								else:
									graph.options[key] = value

					graphs.append(graph)

				self._nodes.append(Node(group_name, node_name, graphs))

	@property
	def nodes(self):
		return sorted(self._nodes, key=lambda x: (x.group, x.name))
