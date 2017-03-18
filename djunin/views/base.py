# -*- coding: utf-8 -*-
from djunin.models import Node

class BaseViewMixin(object):
    page_title = None
    sidebar_item = None
    brand_title = None
    brand_url = None

    @property
    def all_node_groups(self):
        return Node.objects.for_user(self.request.user).values_list('group', flat=True).order_by('group').distinct()

    @property
    def group_nodes(self):
        if 'group' in self.kwargs:
            return Node.objects.for_user(self.request.user).filter(group=self.kwargs['group'])

    def get_context_data(self, **kwargs):
        d = kwargs
        d.setdefault('page_title', self.get_page_title())
        d.setdefault('sidebar_item', self.get_sidebar_item())
        d.setdefault('node_groups', self.all_node_groups)
        d.setdefault('group_nodes', self.group_nodes)
        d.setdefault('brand_title', self.get_brand_title())
        d.setdefault('brand_url', self.get_brand_url())
        return super(BaseViewMixin, self).get_context_data(**d)

    def get_page_title(self):
        return self.page_title

    def get_sidebar_item(self):
        return self.sidebar_item

    def get_brand_title(self):
        return self.brand_title

    def get_brand_url(self):
        return self.brand_url