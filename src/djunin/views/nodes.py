# -*- coding: utf-8 -*-
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from djunin.models.muninobj import Node, Graph
from djunin.views.base import BaseViewMixin

class NodesListView(BaseViewMixin, TemplateView):
	page_title = _('Nodes')
	template_name = 'nodes.html'

	def get_context_data(self, **kwargs):
		nodes = Node.objects.all()
		return super(NodesListView, self).get_context_data(nodes=nodes, **kwargs)


class GraphsListView(BaseViewMixin, TemplateView):
	page_title = _('Graphs')
	template_name = 'graphs.html'

	def get_context_data(self, **kwargs):
		graphs = Graph.objects.filter(node__name=self.kwargs['node'], parent=None)
		return super(GraphsListView, self).get_context_data(graphs=graphs, **kwargs)