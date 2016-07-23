# -*- coding: utf-8 -*-
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from djunin.models.base import ModelBase
from django.db import models

class MuninObjectManagerBase(models.Manager):
	pass


class MuninOrderMixin(object):
	
	def munin_ordered(self, qs):
		return sorted(list(qs), key=lambda item: (len(item.name.split('_')), item.name.split('_')))

class DjuninPermissionManagerBase(models.Manager):

	prefix = None

	def permission_filter(self, user, prefix=None):
		if prefix:
			object_id_field = "%s__%s" % (prefix, "permissions__object_id")
			object_ct_field = "%s__%s" % (prefix, "permissions__object_ct")
		else:
			object_id_field = "permissions__object_id"
			object_ct_field = "permissions__object_ct"

		return Q(**{
			object_id_field: user.pk,
			object_ct_field: ContentType.objects.get_for_model(user)
		}) | Q(**{
			object_ct_field: ContentType.objects.get_for_model(Group),
			"%s__in" % object_id_field: [g.pk for g in user.groups.all()]
		})

	def for_user(self, user):
		if not user:
			return self.get_queryset().empty()

		if user.is_superuser:
			return self.get_queryset()

		return self.get_queryset().filter(self.permission_filter(user, self.prefix))


class DjuninNodePermissionManager(DjuninPermissionManagerBase):

	def get(self, user, group, node):
		return self.for_user(user).filter(group=group, name=node)


class DjuninGraphPermissionManager(DjuninPermissionManagerBase):

	prefix = 'node'

	def get(self, user, node, name):
		return self.for_user(user).filter(node=node, name=name)

	def get_subgraph(self, user, node, parent_graph, name):
		return self.for_user(user).filter(node=node, parent=parent_graph, name=name)


class DjuninDatarowPermissionManager(DjuninPermissionManagerBase):

	prefix = 'graph__node'


class GraphManager(MuninOrderMixin, DjuninGraphPermissionManager):
	pass


class Node(ModelBase):
	group = models.CharField(max_length=250, db_index=True)
	name = models.CharField(max_length=250, db_index=True)

	objects = DjuninNodePermissionManager()

	def __init__(self, *args, **kwargs):
		super(Node, self).__init__(*args, **kwargs)
		self._graph_categories = None

	@property
	def graph_categories(self):
		if self._graph_categories is None:
			self._graph_categories = self.graphs.filter(parent=None).exclude(graph_category='').values_list('graph_category', flat=True).order_by('graph_category').distinct()
		return self._graph_categories

	class Meta(ModelBase.Meta):
		unique_together = 'group', 'name'
		ordering = 'group', 'name'


class Graph(ModelBase):
	node = models.ForeignKey(Node, related_name='graphs')
	name = models.CharField(max_length=250, db_index=True)

	parent = models.ForeignKey('Graph', related_name='subgraphs', null=True, blank=True)

	graph_args = models.TextField(blank=True)
	graph_args_base = models.IntegerField(null=True, blank=True)
	graph_args_lower_limit = models.BigIntegerField(null=True, blank=True)
	graph_args_upper_limit = models.BigIntegerField(null=True, blank=True)
	graph_args_rigid = models.BooleanField(default=False)
	graph_category = models.CharField(max_length=250)
	graph_info = models.TextField(blank=True)
	graph_order = models.TextField(blank=True)
	graph_period = models.CharField(max_length=150, blank=True, default='second')
	graph_printf = models.CharField(max_length=150, blank=True)
	graph_scale = models.BooleanField(default=True)
	graph_title = models.CharField(max_length=200, blank=True)
	graph_total = models.CharField(max_length=200, blank=True)
	graph_vlabel = models.CharField(max_length=200, blank=True)
	graph_width = models.IntegerField(null=True)

	objects = GraphManager()

	def __str__(self):
		return self.graph_title or self.name

	class Meta(ModelBase.Meta):
		unique_together = 'node', 'parent', 'name'
		ordering = 'node', 'name'


class DataRow(ModelBase):
	graph = models.ForeignKey(Graph, related_name='datarows')
	name = models.CharField(max_length=250, db_index=True)

	rrdfile = models.CharField(max_length=255)

	cdef = models.CharField(max_length=200, null=True, blank=True)
	colour = models.CharField(max_length=7, null=True, blank=True)
	critical = models.CharField(max_length=100, null=True, blank=True)
	draw = models.CharField(max_length=100, null=True, blank=True)
	do_graph = models.BooleanField(default=True)
	graph_data_size = models.CharField(max_length=50, null=True, blank=True)
	info = models.TextField(null=True, blank=True)
	label = models.CharField(max_length=200, null=True, blank=True)
	max = models.IntegerField(null=True, blank=True)
	min = models.IntegerField(null=True, blank=True)
	negative = models.CharField(max_length=200, null=True, blank=True)
	type = models.CharField(max_length=200, null=True, blank=True)
	update_rate = models.IntegerField(null=True, blank=True)
	warning = models.CharField(max_length=100, null=True, blank=True)
	extinfo = models.TextField(null=True, blank=True)

	objects = DjuninDatarowPermissionManager()

	class Meta(ModelBase.Meta):
		unique_together = 'graph', 'name'
		ordering = 'graph', 'name'

