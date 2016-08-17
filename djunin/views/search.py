# -*- coding: utf-8 -*-
import itertools

from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http.response import JsonResponse, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template.response import TemplateResponse
from django.views.generic import View
import logging

from djunin.models import Node, Graph

logger = logging.getLogger(__name__)


class SearchView(View):

	def get(self, request):
		query_string = request.GET.get('query', '')
		logger.debug("Suggestions for %s", query_string)

		def _search():
			chunks = [x.strip().lower() for x in query_string.split() if x.strip()]

			def _make_filter(*field_name):
				q = None
				for c in chunks:
					for fname in field_name:
						f = Q(**{'%s__contains' % fname: c})
						q = f if q is None else q | f
				return q

			results = []

			# group
			group_q = Node.objects.filter(_make_filter('group')).values_list('group', flat=True).distinct()
			results.extend((
				(group_name, reverse('group_nodes', args=(group_name, )), 2 if any((group_name.startswith(c) for c in chunks)) else 1)
				for group_name in set(group_q)
			))

			# nodes
			node_q = Node.objects.filter(_make_filter('name')).values_list('group', 'name').distinct()
			results.extend((
				(node_name, reverse('graphs', args=(group_name, node_name, )), sum([
					1 if any((group_name.startswith(c) for c in chunks)) else 0,
					1 if any((node_name.startswith(c) for c in chunks)) else 0,
				]))
				for group_name, node_name in node_q
			))

			# graph category
			graph_category_q = Graph.objects.filter(_make_filter('graph_category')).values_list('node__group', 'node__name', 'graph_category').distinct()
			results.extend((
				("%s / %s" % (graph_category, node_name), reverse('graphs', args=(group_name, node_name, graph_category)), sum([
					1 if any((group_name.startswith(c) for c in chunks)) else 0,
					1 if any((node_name.startswith(c) for c in chunks)) else 0,
					1 if any((graph_category.startswith(c) for c in chunks)) else 0,
				]))
				for group_name, node_name, graph_category in set(graph_category_q)
			))

			# graphs
			graph_category_q = Graph.objects.filter(_make_filter('name', 'graph_title')).\
									values_list('name', 'graph_title', 'node__group', 'node__name', 'graph_category').\
									distinct()
			results.extend((
				("%s / %s" % (graph_title or graph_name, node_name),
					reverse('graphs', args=(group_name, node_name, graph_category)) + '#%s' % graph_name, sum([
					1 if any((c in graph_name for c in chunks)) else 0,
					1 if any((c in graph_title for c in chunks)) else 0,
					1 if any((group_name.startswith(c) for c in chunks)) else 0,
					1 if any((node_name.startswith(c) for c in chunks)) else 0,
					1 if any((graph_category.startswith(c) for c in chunks)) else 0,
				]))
				for graph_name, graph_title, group_name, node_name, graph_category in set(graph_category_q)
			))

			return [
				{
					'value': value,
					'data': data
				} for value, data, _ in sorted(results, key=lambda x: x[2], reverse=True)
			]

		d = {
			'query': query_string,
			'suggestions': list(itertools.chain(_search()))
		}
		return JsonResponse(d)


class JumpToView(View):

	def get(self, request):
		q = (request.GET.get('query', '') or request.GET.get('q', '')).strip()
		return self.handle(request, q)

	def post(self, request):
		q = (request.POST.get('query', '') or request.POST.get('q', '')).strip()
		return self.handle(request, q)

	def handle(self, request, q):
		node_q = Node.objects.filter(name=q)
		if node_q.count() == 1:
			return HttpResponseRedirect(reverse('graphs', args=(node_q[0].group, node_q[0].name)))

		node_q = Node.objects.filter(name__startswith=q)
		if node_q.count() == 1:
			return HttpResponseRedirect(reverse('graphs', args=(node_q[0].group, node_q[0].name)))

		group_q = Node.objects.filter(group=q)
		if group_q.exists():
			return HttpResponseRedirect(reverse('group_nodes', args=(group_q[0].group, )))

		response = render_to_response('not_found.html', {}, RequestContext(request))
		response.status_code = 404
		return response