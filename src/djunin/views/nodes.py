# -*- coding: utf-8 -*-
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.views.generic.list import ListView

from djunin.models.muninobj import Node, Graph
from djunin.views.base import BaseViewMixin

class NodesListView(BaseViewMixin, TemplateView):
	page_title = _('Nodes')
	template_name = 'nodes.html'
	sidebar_item = 'nodes'

	def get_context_data(self, **kwargs):
		nodes = Node.objects.all()

		if 'group' in kwargs:
			nodes = nodes.filter(group=kwargs['group'])

		return super(NodesListView, self).get_context_data(nodes=nodes, **kwargs)

	def get_page_title(self):
		return self.kwargs.get('group', self.page_title)


class GraphsListView(BaseViewMixin, ListView):
	model = Graph
	context_object_name = 'graphs'
	sidebar_item = 'nodes'

	def get_page_title(self):
		return Node.objects.get(name=self.kwargs['node']).name

	def get_context_data(self, **kwargs):
		return super(GraphsListView, self).get_context_data(**kwargs)

	def get_queryset(self):
		return super(GraphsListView, self).get_queryset().\
			filter(node__name=self.kwargs['node'], parent=None).\
			order_by('graph_category', 'name')
