# -*- coding: utf-8 -*-

class BaseViewMixin(object):
	page_title = None

	def get_context_data(self, **kwargs):
		return super(BaseViewMixin, self).get_context_data(page_title=self.get_page_title())

	def get_page_title(self):
		return self.page_title