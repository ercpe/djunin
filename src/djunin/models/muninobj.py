# -*- coding: utf-8 -*-
from djunin.models.base import ModelBase
from django.db import models

class Node(ModelBase):
	group = models.CharField(max_length=250)
	name = models.CharField(max_length=250)

	class Meta(ModelBase.Meta):
		unique_together = 'group', 'name'


class Option(ModelBase):
	key = models.CharField(max_length=250, db_index=True)
	value = models.TextField()


class Graph(ModelBase):
	node = models.ForeignKey(Node, related_name='graphs')
	name = models.CharField(max_length=250)

	graph_category = models.CharField(max_length=250, null=True, blank=True)

	parent = models.ForeignKey('Graph', related_name='subgraphs', null=True, blank=True)

	options = models.ManyToManyField(Option)

	def __str__(self):
		if self.parent:
			return "%s/%s" % (self.parent, self.name)
		return self.name

	class Meta(ModelBase.Meta):
		unique_together = 'node', 'name'


class DataRow(ModelBase):
	graph = models.ForeignKey(Graph, related_name='datarows')
	name = models.CharField(max_length=250, db_index=True)

	options = models.ManyToManyField(Option)

	class Meta(ModelBase.Meta):
		unique_together = 'graph', 'name'
