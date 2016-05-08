# -*- coding: utf-8 -*-
from django.contrib.admin.views.decorators import staff_member_required
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic.edit import FormView

from djunin.forms import ManagementUpdateForm
from djunin.updater import Updater
from djunin.views.base import BaseViewMixin
from django.contrib import messages

class ManagementView(BaseViewMixin, FormView):
	template_name = 'djunin/management/index.html'
	page_title = _('Management')
	form_class = ManagementUpdateForm
	success_url = reverse_lazy('manage')

	@method_decorator(staff_member_required)
	def dispatch(self, request, *args, **kwargs):
		return super(ManagementView, self).dispatch(request, *args, **kwargs)

	def form_valid(self, form):
		Updater().run()
		messages.add_message(self.request, messages.INFO, 'Nodes and graphs successfully updated')
		return super(ManagementView, self).form_valid(form)
