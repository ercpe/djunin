# -*- coding: utf-8 -*-
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView


class AdminIndexView(TemplateView):
	template_name = 'admin/index.html'

	@method_decorator(staff_member_required)
	def dispatch(self, request, *args, **kwargs):
		return super(AdminIndexView, self).dispatch(request, *args, **kwargs)