# -*- coding: utf-8 -*-
import logging
from django.core.management.base import BaseCommand
from django.db import transaction

from djunin.models import Node, Graph, Option, DataRow
from djunin.objects import MuninDataFile

logger = logging.getLogger(__file__)

class Command(BaseCommand):

	def handle(self, *args, **options):

		with transaction.atomic():
			datafile = MuninDataFile()

			def _save_graph(n, g, parent=None):
				graph, graph_created = Graph.objects.get_or_create(node=n, name=g.name, defaults={
					'parent': parent
				})

				for dr_name, dr_values in g.datarows.items():
					logger.debug("Creating datarow %s on %s/%s", dr_name, graph.parent, graph)
					datarow, datarow_created = DataRow.objects.get_or_create(graph=graph, name=dr_name)

				if not graph_created:
					DataRow.objects.filter(graph=graph).exclude(name__in=g.datarows.keys()).delete()

				return graph, graph_created

			for munin_node in datafile.nodes:
				logger.info("Creating/Updating node %s", munin_node)
				if munin_node.name != "web.not-your-server.de":
					continue
				node, node_created = Node.objects.get_or_create(group=munin_node.group, name=munin_node.name)

				for munin_graph in munin_node.graphs:
					if not munin_graph.name.startswith('disk'):
						continue
					logger.debug("Creating/Updating graph %s on %s", munin_graph, munin_node)
					graph, graph_created = _save_graph(node, munin_graph)

					if munin_graph.subgraphs:
						for munin_subgraph in munin_graph.subgraphs.values():
							logger.debug("Creating/Updating graph %s/%s on %s", munin_graph, munin_subgraph, munin_node)
							_save_graph(node, munin_subgraph, parent=graph)

						if not graph_created:
							q = Graph.objects.filter(node=node, parent=graph).exclude(name__in=[sg.name for sg in munin_graph.subgraphs.values()])
							q.delete()

				if not node_created:
					q = Graph.objects.filter(node=node, parent=None).exclude(name__in=[g.name for g in munin_node.graphs])
					q.delete()