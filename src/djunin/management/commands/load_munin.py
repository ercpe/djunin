# -*- coding: utf-8 -*-
import argparse
import logging
import shlex

from django.core.management.base import BaseCommand
from django.db import transaction

from djunin.models import Node, Graph, DataRow
from djunin.objects import MuninDataFile

logger = logging.getLogger(__file__)

class Command(BaseCommand):

	def handle(self, *args, **options):
		with transaction.atomic():
			datafile = MuninDataFile()

			for munin_node in datafile.nodes:
				logger.info("Creating/Updating node %s", munin_node)
				node, node_created = Node.objects.get_or_create(group=munin_node.group, name=munin_node.name)

				for munin_graph in munin_node.graphs:
					logger.debug("Creating/Updating graph %s on %s", munin_graph, munin_node)
					graph, graph_created = self._save_graph(node, munin_graph)

					if munin_graph.subgraphs:
						for munin_subgraph in munin_graph.subgraphs.values():
							logger.debug("Creating/Updating graph %s/%s on %s", munin_graph, munin_subgraph, munin_node)
							self._save_graph(node, munin_subgraph, parent=graph)

						if not graph_created:
							q = Graph.objects.filter(node=node, parent=graph).exclude(name__in=[sg.name for sg in munin_graph.subgraphs.values()])
							q.delete()

				if not node_created:
					q = Graph.objects.filter(node=node, parent=None).exclude(name__in=[g.name for g in munin_node.graphs])
					q.delete()

	def _save_graph(self, n, g, parent=None):
		opts = {
			'parent': parent,
		}
		opts.update(g.options)
		opts.update(self.parse_graph_args(g.options.get('graph_args', '')))

		if 'host_name' in opts:
			del opts['host_name']
		opts['graph_category'] = opts.get('graph_category', 'other').lower()

		# todo: fill opts with None to be able to remove options from the database
		graph, graph_created = Graph.objects.update_or_create(node=n, name=g.name, defaults=opts)

		for dr_name, dr_values in g.datarows.items():
			logger.debug("Creating datarow %s on %s/%s", dr_name, graph.parent, graph)

			# todo: fill opts with None to be able to remove options from the database
			dr_opts = {
				'rrdfile': self.get_rrdfilename(graph, dr_name, dr_values)
			}
			dr_opts.update(dr_values)
			if 'host_name' in dr_opts:
				del dr_opts['host_name']

			if 'graph' in dr_opts:
				dr_opts['do_graph'] = dr_opts['graph'].lower() == "yes"
				del dr_opts['graph']

			DataRow.objects.update_or_create(graph=graph, name=dr_name, defaults=dr_opts)

		if not graph_created:
			DataRow.objects.filter(graph=graph).exclude(name__in=g.datarows.keys()).delete()

		return graph, graph_created

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
