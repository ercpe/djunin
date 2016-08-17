# -*- coding: utf-8 -*-

from django.contrib import admin
from djunin.models import Node, Graph, DataRow
from djunin.models.permissions import DjuninNodePermission

admin.site.register([Node, Graph, DataRow, DjuninNodePermission])