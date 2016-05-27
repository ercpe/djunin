# -*- coding: utf-8 -*-
import datetime
import time
import pytz
from django.core.urlresolvers import reverse
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
		nodes = Node.objects.all()

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

	def __init__(self, *args, **kwargs):
		super(GraphsListView, self).__init__(*args, **kwargs)
		self._node = None
		self._current_graph = None

	def get_page_title(self):
		return self.current_graph or self.node.name

	@property
	def node(self):
		if self._node is None:
			logger.debug("Searching node: %s/%s", self.kwargs['group'], self.kwargs['node'])
			self._node = get_object_or_404(Node.objects.filter(group=self.kwargs['group'], name=self.kwargs['node']))
		return self._node

	@property
	def current_category(self):
		return self.kwargs['graph_category']

	@property
	def current_graph(self):
		graph_name = self.kwargs.get('graph_name', None)
		if graph_name:
			if not self._current_graph:
				self._current_graph = get_object_or_404(Graph.objects.filter(node=self.node, name=graph_name))
			return self._current_graph

		return graph_name

	def get_context_data(self, **kwargs):
		kwargs.setdefault('node', self.node)
		kwargs.setdefault('selected_group', self.node.group)
		kwargs.setdefault('current_category', self.current_category)
		kwargs.setdefault('current_graph', self.current_graph)
		kwargs.setdefault('detailed', 'graph_name' in self.kwargs)
		return super(GraphsListView, self).get_context_data(nodes=super(GraphsListView, self).get_queryset(), **kwargs)

	def get_queryset(self):
		logger.debug("Filter by category: %s", self.current_category)
		q = super(ListView, self).get_queryset().\
			filter(node=self.node, parent=None, graph_category=self.current_category)

		if self.current_graph:
			logger.debug("Filter by graph: %s", self.current_graph)
			q = q.filter(pk=self.current_graph.pk)

		return q.select_related('node').order_by('graph_category', 'name')

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
		return Graph.objects.filter(node=self.node, name=self.kwargs['name'])

	def render_to_response(self, context, **response_kwargs):
		try:
			scope_name = self.kwargs['scope']

			range_start = self.request.GET.get('start', None) or None
			range_end = self.request.GET.get('end', None) or None
			if scope_name == "custom":
				if range_start is None:
					raise HttpResponseBadRequest()
				range_start = int(range_start)
				if range_end is not None:
					range_end = int(range_end)

			data, start, end, resolution = D3GraphDataGenerator(self.node, self.object, scope_name, range_start, range_end).generate()

			return JsonResponse(data)
		except:
			logger.exception("Error rendering graph data for %s on %s", self.object, self.node)
			raise
