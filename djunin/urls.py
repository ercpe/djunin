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
from django.views.generic.base import RedirectView
from django.contrib.auth import views as auth_views

from djunin.views.management import ManagementPermissionsView, ManagementIndexView, ManagementUpdateView
from djunin.views.nodes import NodesListView, GraphsListView, GraphDataView
from djunin.views.search import SearchView, JumpToView

from opensearch import urls as opensearch_urls

urlpatterns = [
	url(r'^admin/', include(admin.site.urls)),
	url(r'^accounts/login/$', auth_views.login, name='login'),
	url(r'^accounts/logout/$', auth_views.logout, {'next_page': '/'}, name='logout'),
	url(r'^opensearch/', include(opensearch_urls)),
	url(r'^jump$', JumpToView.as_view(), name='jump'),
	url(r'^search$', SearchView.as_view(), name='search'),
	url(r'^nodes/(?P<group>[^/]+)/(?P<node>[^/]+)/(?P<parent_name>[^/]+)/(?P<name>[^/]+)/(?P<scope>day|week|month|year|custom)\.json$', GraphDataView.as_view(), name='graph_data'),
	url(r'^nodes/(?P<group>[^/]+)/(?P<node>[^/]+)/(?P<name>[^/]+)/(?P<scope>day|week|month|year|custom)\.json$', GraphDataView.as_view(), name='graph_data'),
	url(r'^nodes/(?P<group>[^/]+)/(?P<node>[^/]+)/(?P<graph_category>[^/]+)/(?P<graph_name>[^/]+)/(?P<subgraph_name>[^/]+)$', GraphsListView.as_view(), name='graphs_graph'),
	url(r'^nodes/(?P<group>[^/]+)/(?P<node>[^/]+)/(?P<graph_category>[^/]+)/(?P<graph_name>[^/]+)$', GraphsListView.as_view(), name='graphs_graph'),
	url(r'^nodes/(?P<group>[^/]+)/(?P<node>[^/]+)/(?:(?P<graph_category>[^/]+))?$', GraphsListView.as_view(), name='graphs'),
	url(r'^nodes/(?P<group>[^/]+)/?$', NodesListView.as_view(), name='group_nodes'),
	url(r'^nodes/?$', NodesListView.as_view(), name='nodes'),
	url(r'^manage/update$', ManagementUpdateView.as_view(), name='management_update'),
	url(r'^manage/permissions$', ManagementPermissionsView.as_view(), name='management_permissions'),
	url(r'^manage$', ManagementIndexView.as_view(), name='manage'),
	#url(r'^$', DashboardView.as_view(), name='dashboard'),
	url(r'^$', RedirectView.as_view(pattern_name='nodes', permanent=False), name='dashboard'),
]
