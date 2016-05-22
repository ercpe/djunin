# -*- coding: utf-8 -*-
from djunin.models.base import ModelBase
from django.db import models

class MuninObjectManagerBase(models.Manager):
	pass

class Node(ModelBase):
	group = models.CharField(max_length=250, db_index=True)
	name = models.CharField(max_length=250, db_index=True)

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

	def __str__(self):
		if self.parent:
			return "%s/%s" % (self.parent, self.name)
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

	class Meta(ModelBase.Meta):
		unique_together = 'graph', 'name'
		ordering = 'graph', 'name'

