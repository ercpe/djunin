# -*- coding: utf-8 -*-
from django.contrib.admin.views.decorators import staff_member_required
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from djunin.forms import ManagementUpdateForm
from djunin.models import Node
from djunin.updater import Updater
from djunin.views.base import BaseViewMixin
from django.contrib import messages


class ManagementBaseViewMixin(BaseViewMixin):
	brand_title = _('Management')
	brand_url = reverse_lazy('manage')

	@method_decorator(staff_member_required)
	def dispatch(self, request, *args, **kwargs):
		return super(ManagementBaseViewMixin, self).dispatch(request, *args, **kwargs)


class ManagementIndexView(ManagementBaseViewMixin, TemplateView):
	template_name = 'djunin/management/index.html'
	page_title = _('Management')


class ManagementUpdateView(ManagementBaseViewMixin, FormView):
	template_name = 'djunin/management/update.html'
	sidebar_item = 'management_update'
	page_title = _('Management')
	form_class = ManagementUpdateForm
	success_url = reverse_lazy('management_update')

	@method_decorator(staff_member_required)
	def dispatch(self, request, *args, **kwargs):
		return super(ManagementUpdateView, self).dispatch(request, *args, **kwargs)

	def form_valid(self, form):
		Updater().run()
		messages.add_message(self.request, messages.INFO, 'Nodes and graphs successfully updated')
		return super(ManagementUpdateView, self).form_valid(form)


class ManagementPermissionsView(ManagementBaseViewMixin, FormView):
	template_name = 'djunin/management/permissions.html'
	sidebar_item = 'management_permissions'
	page_title = _('Permissions')
	form_class = ManagementUpdateForm
	success_url = reverse_lazy('management_permissions')

	def get_context_data(self, **kwargs):
		kwargs.setdefault('nodes', Node.objects.for_user(self.request.user).all())
		return super(ManagementPermissionsView, self).get_context_data(**kwargs)
