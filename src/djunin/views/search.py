# -*- coding: utf-8 -*-
import itertools

from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http.response import JsonResponse
from django.views.generic import View
import logging

from djunin.models import Node, Graph

logger = logging.getLogger(__name__)

class SearchView(View):

	def get(self, request):
		query_string = request.GET.get('query', '')
		logger.debug("Suggestions for %s", query_string)

		def _search():
			chunks = [x.strip() for x in query_string.split() if x.strip()]

			def _make_filter(field_name):
				q = None
				for c in chunks:
					f = Q(**{'%s__contains' % field_name: c})
					q = f if q is None else q | f
				return q

			# groups
			for group_name in Node.objects.filter(_make_filter('group')).values_list('group', flat=True).distinct():
				yield {
					'value': group_name,
					'data': reverse('group_nodes', args=(group_name, )),
				}

			# nodes
			for group_name, node_name in Node.objects.filter(_make_filter('name')).values_list('group', 'name').distinct():
				yield {
					'value': node_name,
					'data': reverse('graphs', args=(group_name, node_name, )),
				}

			# graph category
			for group_name, node_name, graph_category in Graph.objects.filter(_make_filter('graph_category')).values_list('node__group', 'node__name', 'graph_category').distinct():
				yield {
					'value': "%s / %s" % (graph_category, node_name),
					'data': reverse('graphs', args=(group_name, node_name, graph_category)),
				}

		d = {
			'query': query_string,
			'suggestions': list(itertools.chain(_search()))
		}
		return JsonResponse(d)