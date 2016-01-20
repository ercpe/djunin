# -*- coding: utf-8 -*-
from django.conf import settings
from djunin.objects import MuninDataFile

class BaseViewMixin(object):
	page_title = None

	def __init__(self):
		self._datafile = None

	@property
	def data_file(self):
		if self._datafile is None:
			self._datafile = MuninDataFile(getattr(settings, 'MUNIN_DATA_FILE', '/var/lib/munin/datafile'))
		return self._datafile

	def get_context_data(self, **kwargs):
		d = kwargs
		d.setdefault('page_title', self.get_page_title())
		return super(BaseViewMixin, self).get_context_data(**d)

	def get_page_title(self):
		return self.page_title