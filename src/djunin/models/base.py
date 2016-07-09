# -*- coding: utf-8 -*-
from django.db import models

class ModelBase(models.Model):
	def __str__(self):
		if hasattr(self, 'name') and self.name:
			return self.name
		return super(ModelBase, self).__str__()

	class Meta:
		abstract = True
		app_label = 'djunin'
