# -*- coding: utf-8 -*-
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from djunin.models import Node
from djunin.models.base import ModelBase


class DjuninPermissionManager(models.Manager):
    use_for_related_fields = True

    def user_permissions(self):
        return self.get_queryset().filter(object_ct=ContentType.objects.get_for_model(User))

    def group_permissions(self):
        return self.get_queryset().filter(object_ct=ContentType.objects.get_for_model(Group))


class DjuninNodePermission(ModelBase):
    node = models.ForeignKey(Node, related_name='permissions')
    object_id = models.PositiveIntegerField()
    object_ct = models.ForeignKey(ContentType)
    object = GenericForeignKey('object_ct')

    objects = DjuninPermissionManager()

    class Meta(ModelBase.Meta):
        unique_together = 'node', 'object_ct', 'object_id'
