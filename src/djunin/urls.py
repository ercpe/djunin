"""djunin URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
	https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
	1. Add an import:  from my_app import views
	2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
	1. Add an import:  from other_app.views import Home
	2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
	1. Add an import:  from blog import urls as blog_urls
	2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin

from djunin.views.administration import AdminIndexView
from djunin.views.dashboard import DashboardView
from djunin.views.nodes import NodesListView, GraphsListView, GraphDataView
from djunin.views.search import SearchView

urlpatterns = [
	url(r'^admin/', include(admin.site.urls)),
	url(r'^accounts/login/$', 'django.contrib.auth.views.login'),
	url(r'^accounts/logout/$', 'django.contrib.auth.views.logout'),
	url(r'^administration/$', AdminIndexView.as_view(), name='admin'),
	url(r'^search$', SearchView.as_view(), name='search'),
	url(r'^nodes/(?P<group>[^/]+)/(?P<node>[^/]+)/(?P<name>[^/]+)/(?P<scope>day|week|month|year)\.json$', GraphDataView.as_view(), name='graph_data'),
	url(r'^nodes/(?P<group>[^/]+)/(?P<node>[^/]+)/(?:(?P<graph_category>[^/]+))?$', GraphsListView.as_view(), name='graphs'),
	url(r'^nodes/(?P<group>[^/]+)/?$', NodesListView.as_view(), name='group_nodes'),
	url(r'^nodes/?$', NodesListView.as_view(), name='nodes'),
	url(r'^$', DashboardView.as_view(), name='dashboard'),
]
