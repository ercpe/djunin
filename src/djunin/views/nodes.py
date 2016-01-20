# -*- coding: utf-8 -*-
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from djunin.views.base import BaseViewMixin

class NodesListView(BaseViewMixin, TemplateView):
	page_title = _('Nodes')
	template_name = 'nodes.html'

	def get_context_data(self, **kwargs):
		return super(NodesListView, self).get_context_data(nodes=self.data_file.nodes, **kwargs)


class GraphsListView(BaseViewMixin, TemplateView):
	page_title = _('Graphs')
	template_name = 'graphs.html'

	def get_context_data(self, **kwargs):
		node_graphs = [n.graphs for n in self.data_file.nodes][0]
		return super(GraphsListView, self).get_context_data(graphs=node_graphs, **kwargs)