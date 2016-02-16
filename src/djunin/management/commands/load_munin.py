# -*- coding: utf-8 -*-
import argparse
import logging
import shlex

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.db.models.fields import NOT_PROVIDED, CharField, TextField

from djunin.models import Node, Graph, DataRow
from djunin.objects import MuninDataFile

from bulk_update.helper import bulk_update

logger = logging.getLogger(__file__)

class Command(BaseCommand):

	def handle(self, *args, **options):
		with transaction.atomic():
			datafile = MuninDataFile()

			self._process_nodes(datafile)

			self._process_graphs(datafile)

			self._process_datarows(datafile)

	def _process_nodes(self, datafile):
		logger.info("Processing nodes")
		logger.info("Creating nodes")
		# first, create missing nodes
		existing_nodes = Node.objects.values_list('group', 'name')
		Node.objects.bulk_create((
			Node(group=n.group, name=n.name) for n in datafile.nodes if (n.group, n.name) not in existing_nodes
		))

		logger.info("Removing nodes")
		# then remove all other nodes
		q_filter = None
		for g, n in existing_nodes:
			f = Q(group=g, name=n)
			if q_filter is None:
				q_filter = f
			else:
				q_filter = q_filter | f
		Node.objects.exclude(q_filter).delete()

	def _process_graphs(self, datafile):
		logger.info("Processing graphs")

		existing_nodes = Node.objects.all()

		logger.info("Creating root graphs")
		existing_parent_graphs = Graph.objects.filter(parent=None).values_list('node__group', 'node__name', 'name')
		Graph.objects.bulk_create((
			Graph(node=[n for n in existing_nodes if n.group == group_name and n.name == node_name][0], name=graph_name)
			for group_name, nodes in datafile.raw.items()
			for node_name, graphs in nodes.items()
			for graph_name, graph_data in graphs.items()
			if (group_name, node_name, graph_name) not in existing_parent_graphs
		))

		logger.info("Creating subgraphs")
		parent_graphs = Graph.objects.filter(parent=None).select_related('node')
		existing_subgraphs = Graph.objects.exclude(parent=None).values_list('node__group', 'node__name', 'parent__name', 'name')
		Graph.objects.bulk_create((
			Graph(
				node=[n for n in existing_nodes if n.group == group_name and n.name == node_name][0],
				parent=[p for p in parent_graphs if p.node.group == group_name and p.node.name == node_name and p.name == graph_name][0],
				name=subgraph_name)
			for group_name, nodes in datafile.raw.items()
			for node_name, graphs in nodes.items()
			for graph_name, graph_data in graphs.items()
			for subgraph_name, subgraph_data in graph_data.get('subgraphs', {}).items()
			if (group_name, node_name, graph_name, subgraph_name) not in existing_subgraphs
		))

		logger.info("Updating all graphs")
		all_graphs = Graph.objects.select_related('node', 'parent')
		for graph in all_graphs:
			if graph.parent:
				graph_options = datafile.raw[graph.node.group][graph.node.name][graph.parent.name]['subgraphs'][graph.name]['options']
			else:
				graph_options = datafile.raw[graph.node.group][graph.node.name][graph.name]['options']

			opts = self._get_model_attributes(Graph, lambda f: not f.name.startswith('graph_'))
			opts.update(graph_options)
			opts.update(self.parse_graph_args(graph_options.get('graph_args', '')))

			if 'host_name' in opts:
				del opts['host_name']

			opts['graph_category'] = (opts.get('graph_category', 'other') or 'other').lower()
			if not isinstance(opts['graph_scale'], bool):
				opts['graph_scale'] = opts.get('graph_scale', 'yes').lower() == "yes"

			for k, v in opts.items():
				setattr(graph, k, v)

		bulk_update(all_graphs)

		logger.info("Deleting graphs")
		q_filter = None
		for g, n, p, name in all_graphs.values_list('node__group', 'node__name', 'parent__id', 'name'):
			f = Q(node__group=g, node__name=n, parent__id=p, name=name)
			if q_filter is None:
				q_filter = f
			else:
				q_filter = q_filter | f
		Graph.objects.exclude(q_filter).delete()

	def _process_datarows(self, datafile):
		logger.info("Processing datarows")

		logger.info("... for root graphs")
		parent_graphs = Graph.objects.filter(parent=None).select_related('node')
		existing_parent_graph_datarows = DataRow.objects.filter(graph__in=parent_graphs).values_list('graph__node__group', 'graph__node__name', 'graph__name', 'name')
		x = (
			DataRow(
				graph=[p for p in parent_graphs if p.node.group == group_name and p.node.name == node_name and p.name == graph_name][0],
				name=datarow_name
			)
			for group_name, nodes in datafile.raw.items()
			for node_name, graphs in nodes.items()
			for graph_name, graph_data in graphs.items()
			for datarow_name, datarow_data in graph_data.get('datarows', {}).items()
			if (group_name, node_name, graph_name, datarow_name) not in existing_parent_graph_datarows
		)
		DataRow.objects.bulk_create(x)

		logger.info("... for subgraphs")
		subgraphs = Graph.objects.exclude(parent=None).select_related('node', 'parent')
		existing_subgraph_datarows = DataRow.objects.filter(graph__in=subgraphs).values_list('graph__node__group', 'graph__node__name', 'graph__parent__name', 'graph__name', 'name')
		DataRow.objects.bulk_create((
			DataRow(
				graph=[sg for sg in subgraphs if sg.node.group == group_name and sg.node.name == node_name and sg.parent.name == graph_name and sg.name == subgraph_name][0],
				name=datarow_name,
			)
			for group_name, nodes in datafile.raw.items()
			for node_name, graphs in nodes.items()
			for graph_name, graph_data in graphs.items()
			for subgraph_name, subgraph_data in graph_data.get('subgraphs', {}).items()
			for datarow_name, datarow_data in subgraph_data.get('datarows', {}).items()
			if (group_name, node_name, graph_name, subgraph_name, datarow_name) not in existing_subgraph_datarows
		))

		logger.info("Updating all datarows")
		all_datarows = DataRow.objects.select_related('graph', 'graph__parent', 'graph__node')
		for datarow in all_datarows:
			try:
				if datarow.graph.parent:
					datarow_options = datafile.raw[datarow.graph.node.group][datarow.graph.node.name][datarow.graph.parent.name]['subgraphs'][datarow.graph.name]['datarows'][datarow.name]
				else:
					datarow_options = datafile.raw[datarow.graph.node.group][datarow.graph.node.name][datarow.graph.name]['datarows'][datarow.name]
			except KeyError:
				logger.info("Missing datarow: %s", datarow.name)

			opts = self._get_model_attributes(DataRow, lambda f: f.name in ('graph', 'name'))
			opts.update(datarow_options)
			opts['rrdfile'] = self.get_rrdfilename(datarow.graph, datarow.name, datarow_options)

			if 'graph' in opts:
				opts['do_graph'] = opts['graph'].lower() == "yes"
				del opts['graph']

			#for k, v in opts.items():
			#	setattr(datarow, k, v)
			#datarow.save()
			DataRow.objects.filter(pk=datarow.pk).update(**opts)

		#bulk_update(all_datarows)
		#raise Exception()

		logger.info("Removing datarows")
		q_filter = None
		for g, n, pid, gid, name in all_datarows.values_list('graph__node__group', 'graph__node__name', 'graph__parent__id', 'graph__id', 'name'):
			f = Q(graph__node__group=g, graph__node__name=n, graph__parent__id=pid, graph__id=gid, name=name)
			if q_filter is None:
				q_filter = f
			else:
				q_filter = q_filter | f
		DataRow.objects.exclude(q_filter).delete()

	def _get_model_attributes(self, clazz, exclude=None):
		def _gen():
			for field in clazz._meta.fields:
				if field.name == 'id' or (exclude and exclude(field)):
					continue

				default_value = field.default

				if default_value == NOT_PROVIDED:
					if isinstance(field, (CharField, TextField)) and field.blank:
						default_value = ''
					else:
						default_value = None

				yield field.name, default_value

		return dict(_gen())

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

			supported_args = 'base', 'lower_limit', 'upper_limit'
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
