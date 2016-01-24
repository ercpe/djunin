# -*- coding: utf-8 -*-
from djunin.models.base import ModelBase
from django.db import models

class MuninObjectManagerBase(models.Manager):
	pass

class Node(ModelBase):
	group = models.CharField(max_length=250)
	name = models.CharField(max_length=250)

	class Meta(ModelBase.Meta):
		unique_together = 'group', 'name'


class Graph(ModelBase):
	node = models.ForeignKey(Node, related_name='graphs')
	name = models.CharField(max_length=250)

	parent = models.ForeignKey('Graph', related_name='subgraphs', null=True, blank=True)

	graph_args = models.TextField(blank=True)
	graph_args_base = models.IntegerField(null=True, blank=True)
	graph_args_lower_limit = models.IntegerField(null=True, blank=True)
	graph_args_upper_limit = models.IntegerField(null=True, blank=True)
	graph_category = models.CharField(max_length=250, null=True, blank=True)
	graph_info = models.TextField(blank=True)
	graph_order = models.TextField(blank=True)
	graph_period = models.CharField(max_length=150, blank=True)
	graph_printf = models.CharField(max_length=150, blank=True)
	graph_scale = models.NullBooleanField()
	graph_title = models.CharField(max_length=200, blank=True)
	graph_total = models.CharField(max_length=200, blank=True)
	graph_vlabel = models.CharField(max_length=200, blank=True)
	graph_width = models.IntegerField(null=True)

	def __str__(self):
		if self.parent:
			return "%s/%s" % (self.parent, self.name)
		return self.graph_title or self.name

	class Meta(ModelBase.Meta):
		unique_together = 'node', 'name'


class DataRow(ModelBase):
	graph = models.ForeignKey(Graph, related_name='datarows')
	name = models.CharField(max_length=250, db_index=True)

	rrdfile = models.CharField(unique=True, max_length=255)

	cdef = models.CharField(max_length=200, blank=True)
	colour = models.CharField(max_length=7, blank=True)
	critical = models.CharField(max_length=100, blank=True)
	draw = models.CharField(max_length=100, blank=True)
	do_graph = models.BooleanField(default=True)
	graph_args = models.TextField(blank=True)
	graph_category = models.CharField(max_length=250, null=True, blank=True)
	graph_data_size = models.CharField(max_length=50, blank=True)
	graph_info = models.TextField(blank=True)
	graph_order = models.TextField(blank=True)
	graph_scale = models.NullBooleanField()
	graph_title = models.CharField(max_length=200, blank=True)
	graph_vlabel = models.CharField(max_length=200, blank=True)
	info = models.TextField(blank=True)
	label = models.CharField(max_length=200, blank=True)
	max = models.IntegerField(null=True, blank=True)
	min = models.IntegerField(null=True, blank=True)
	negative = models.CharField(max_length=200, blank=True)
	type = models.CharField(max_length=200, blank=True)
	update_rate = models.IntegerField(null=True, blank=True)
	warning = models.CharField(max_length=100, blank=True)

	class Meta(ModelBase.Meta):
		unique_together = 'graph', 'name'
