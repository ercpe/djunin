# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0005_datarow_rrdfile'),
    ]

    operations = [
        migrations.AddField(
            model_name='graph',
            name='graph_args',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='graph',
            name='graph_args_base',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='graph',
            name='graph_info',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='graph',
            name='graph_order',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='graph',
            name='graph_period',
            field=models.CharField(max_length=150, blank=True),
        ),
        migrations.AddField(
            model_name='graph',
            name='graph_printf',
            field=models.CharField(max_length=150, blank=True),
        ),
        migrations.AddField(
            model_name='graph',
            name='graph_scale',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='graph',
            name='graph_title',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='graph',
            name='graph_total',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='graph',
            name='graph_vlabel',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='graph',
            name='graph_width',
            field=models.IntegerField(null=True),
        ),
    ]
