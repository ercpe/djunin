# -*- coding: utf-8 -*-
import datetime
import time
import pytz
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http.response import JsonResponse, HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.utils.http import http_date
from django.utils.translation import ugettext as _
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from djunin.graphs import D3GraphDataGenerator
from djunin.models.muninobj import Node, Graph
from djunin.views.base import BaseViewMixin
import logging

logger = logging.getLogger(__file__)

class NodesListView(BaseViewMixin, ListView):
	model = Node
	context_object_name = 'nodes'
	sidebar_item = 'nodes'
	page_title = _('Nodes')

	def get_page_title(self):
		return self.kwargs.get('group', self.page_title)

	def get_queryset(self):
		nodes = Node.objects.for_user(self.request.user).all()

		if 'group' in self.kwargs:
			nodes = nodes.filter(group=self.kwargs['group'])

		return nodes

	def get_context_data(self, **kwargs):
		kwargs.setdefault('selected_group', self.kwargs.get('group', None))
		return super(NodesListView, self).get_context_data(**kwargs)


class GraphsListView(NodesListView):
	model = Graph
	context_object_name = 'graphs'
	sidebar_item = 'nodes'
	template_name = 'djunin/graph_list.html'

	def __init__(self, *args, **kwargs):
		super(GraphsListView, self).__init__(*args, **kwargs)
		self._node = None
		self._current_graph = None
		self._subgraphs = None

		self._parent_graph = None
		self._subgraph = None

	def get_page_title(self):
		if self.subgraph:
			return "%s &raquo; %s" % (self.parent_graph.graph_title or self.parent_graph.name,
									  self.subgraph.graph_title or self.subgraph.name)
		return self.graph or self.node.name

	@property
	def node(self):
		if self._node is None:
			logger.debug("Searching node: %s/%s", self.kwargs['group'], self.kwargs['node'])
			self._node = get_object_or_404(Node.objects.get(self.request.user, self.kwargs['group'], self.kwargs['node']))
		return self._node

	@property
	def parent_graph(self):
		if self._parent_graph is None and self.kwargs.get('graph_name', None):
			#Graph.objects.filter(node=self.node, name=self.kwargs['graph_name'])
			self._parent_graph = get_object_or_404(Graph.objects.get(self.request.user, self.node, self.kwargs['graph_name']))
		return self._parent_graph

	@property
	def subgraph(self):
		if self._subgraph is None and self.kwargs.get('subgraph_name', None):
			self._subgraph = get_object_or_404(Graph.objects.get_subgraph(self.request.user, self.node, self.parent_graph, self.kwargs['subgraph_name']))
		return self._subgraph

	@property
	def graph(self):
		return self.subgraph or self.parent_graph

	@property
	def current_category(self):
		return self.kwargs['graph_category']

	@property
	def subgraphs(self):
		if self._subgraphs is None:
			self._subgraphs = Graph.objects.for_user(self.request.user).filter(parent=self.parent_graph)
		return self._subgraphs

	def get_context_data(self, **kwargs):
		kwargs.setdefault('node', self.node)
		kwargs.setdefault('selected_group', self.node.group)
		kwargs.setdefault('current_category', self.current_category)
		kwargs.setdefault('parent_graph', self.parent_graph)
		kwargs.setdefault('current_graph', self.graph)
		kwargs.setdefault('subgraph_name', self.kwargs.get('subgraph_name', None))
		kwargs.setdefault('detailed', 'graph_name' in self.kwargs)
		kwargs.setdefault('subgraphs', self.subgraphs)
		return super(GraphsListView, self).get_context_data(nodes=super(GraphsListView, self).get_queryset(), **kwargs)

	def get_queryset(self):
		logger.debug("Filter by category: %s", self.current_category)
		q = super(ListView, self).get_queryset().\
			filter(node=self.node, graph_category=self.current_category)

		if not self.subgraph:
			q = q.filter(parent=None)

		if self.graph:
			logger.debug("Filter by graph: %s", self.graph)
			q = q.filter(pk=self.graph.pk)

		q = q.select_related('node').order_by('graph_category', 'name')
		
		return self.model.objects.munin_ordered(q)

	def get(self, request, *args, **kwargs):
		if not self.kwargs.get('graph_category', None):
			kw = self.kwargs
			kw['graph_category'] = self.node.graph_categories[0]
			logger.debug("Redirect to first category: %s", kw['graph_category'])
			return HttpResponseRedirect(reverse('graphs', kwargs=kw))

		return super(GraphsListView, self).get(request, *args, **kwargs)


class GraphDataView(BaseViewMixin, DetailView):
	model = Graph
	slug_url_kwarg = 'name'
	slug_field = 'name'

	def __init__(self, *args, **kwargs):
		super(GraphDataView, self).__init__(*args, **kwargs)
		self._node = None

	@property
	def node(self):
		if self._node is None:
			self._node = get_object_or_404(Node.objects.filter(group=self.kwargs['group'], name=self.kwargs['node']))
		return self._node

	def get_queryset(self):
		if 'parent_name' in self.kwargs:
			return Graph.objects.filter(node=self.node,
										parent__name=self.kwargs['parent_name'])
		else:
			return Graph.objects.filter(node=self.node, name=self.kwargs['name'])

	def render_to_response(self, context, **response_kwargs):
		try:
			scope_name = self.kwargs['scope']

			range_start = self.request.GET.get('start', None) or None
			range_end = self.request.GET.get('end', None) or None
			if scope_name == "custom":
				if range_start is None:
					return HttpResponseBadRequest()
				range_start = int(range_start)
				if range_end is not None:
					range_end = int(range_end)

			data, start, end, resolution = D3GraphDataGenerator(self.node, self.object, scope_name, range_start, range_end).generate()

			return JsonResponse(data)
		except:
			logger.exception("Error rendering graph data for %s on %s", self.object, self.node)
			raise
