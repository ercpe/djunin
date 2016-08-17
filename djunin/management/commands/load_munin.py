# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from djunin.updater import Updater


class Command(BaseCommand):

	def handle(self, *args, **options):
		Updater().run()
