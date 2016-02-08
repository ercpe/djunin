# -*- coding: utf-8 -*-
import argparse
import logging
import shlex

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.fields import NOT_PROVIDED, CharField, TextField

from djunin.models import Node, Graph, DataRow
from djunin.objects import MuninDataFile

from bulk_update.helper import bulk_update

logger = logging.getLogger(__file__)

class Command(BaseCommand):

	def handle(self, *args, **options):
		with transaction.atomic():
			datafile = MuninDataFile()

			for munin_node in datafile.nodes:
				logger.info("Updating node %s", munin_node)
				node, node_created = Node.objects.get_or_create(group=munin_node.group, name=munin_node.name)

				for munin_graph in munin_node.graphs:
					graph, graph_created = self._save_graph(node, munin_graph)

					if munin_graph.subgraphs:
						for munin_subgraph in munin_graph.subgraphs.values():
							self._save_graph(node, munin_subgraph, parent=graph)

						if not graph_created:
							q = Graph.objects.filter(node=node, parent=graph).exclude(name__in=[sg.name for sg in munin_graph.subgraphs.values()])
							q.delete()

				if not node_created:
					q = Graph.objects.filter(node=node, parent=None).exclude(name__in=[g.name for g in munin_node.graphs])
					q.delete()

				logger.info("------------------------------------")

	def _save_graph(self, node, munin_graph, parent=None):
		logger.debug("Updating graph %s on %s", munin_graph, node)
		# Set None as default value for all graph options to reset them if they aren't set in munins datafile
		opts = self._get_model_attributes(Graph, lambda f: not f.name.startswith('graph_'))
		opts['parent'] = parent
		opts.update(munin_graph.options)
		opts.update(self.parse_graph_args(munin_graph.options.get('graph_args', '')))

		if 'host_name' in opts:
			del opts['host_name']

		opts['graph_category'] = (opts.get('graph_category', 'other') or 'other').lower()
		if not isinstance(opts['graph_scale'], bool):
			opts['graph_scale'] = opts.get('graph_scale', 'yes').lower() == "yes"

		graph, graph_created = Graph.objects.update_or_create(node=node, name=munin_graph.name, defaults=opts)

		datarow_field_names = [f.name for f in DataRow._meta.fields]
		existing_datarow_names = graph.datarows.values_list('name', flat=True)
		existing_datarows = graph.datarows.all()

		create_datarows = []
		update_datarows = []

		for dr_name, dr_values in munin_graph.datarows.items():
			logger.debug("Saving datarow %s on %s/%s", dr_name, graph.parent, graph)

			dr_opts = self._get_model_attributes(DataRow, lambda f: f.name in ('graph', 'name', 'rrdfile'))
			dr_opts['rrdfile'] = self.get_rrdfilename(graph, dr_name, dr_values)
			dr_opts.update(dr_values)

			if 'graph' in dr_opts:
				dr_opts['do_graph'] = dr_opts['graph'].lower() == "yes"
				del dr_opts['graph']

			for k in dr_opts.keys():
				if k not in datarow_field_names:
					logger.warning("Ignoring field '%s' on %s/%s/%s", k, node, munin_graph, dr_name)
					del dr_opts[k]

			if dr_name in existing_datarow_names:
				dr = [x for x in existing_datarows if x.name == dr_name][0]
				for k, v in dr_opts.items():
					setattr(dr, k, v)
				update_datarows.append(dr)
			else:
				create_datarows.append(DataRow(graph=graph, name=dr_name, **dr_opts))

		# bulk create new datarows
		DataRow.objects.bulk_create(create_datarows)
		# bulk update datarows
		bulk_update(update_datarows)
		# delete other datarows
		DataRow.objects.filter(graph=graph).exclude(name__in=munin_graph.datarows.keys()).exclude(name__in=(dr.name for dr in create_datarows)).delete()

		return graph, graph_created

	def _get_model_attributes(self, clazz, exclude=None):

		def _gen():
			for field in clazz._meta.fields:
				if exclude and exclude(field):
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
