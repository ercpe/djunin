# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0014_auto_20160128_0531'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='datarow',
            name='graph_args',
        ),
        migrations.RemoveField(
            model_name='datarow',
            name='graph_category',
        ),
        migrations.RemoveField(
            model_name='datarow',
            name='graph_info',
        ),
        migrations.RemoveField(
            model_name='datarow',
            name='graph_order',
        ),
        migrations.RemoveField(
            model_name='datarow',
            name='graph_scale',
        ),
        migrations.RemoveField(
            model_name='datarow',
            name='graph_title',
        ),
        migrations.RemoveField(
            model_name='datarow',
            name='graph_vlabel',
        ),
    ]
