# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0008_auto_20160124_0814'),
    ]

    operations = [
        migrations.AddField(
            model_name='datarow',
            name='cdef',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='datarow',
            name='colour',
            field=models.CharField(max_length=7, blank=True),
        ),
        migrations.AddField(
            model_name='datarow',
            name='critical',
            field=models.CharField(max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='datarow',
            name='draw',
            field=models.CharField(max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='datarow',
            name='graph_args',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='datarow',
            name='graph_category',
            field=models.CharField(max_length=250, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='datarow',
            name='graph_data_size',
            field=models.CharField(max_length=50, blank=True),
        ),
        migrations.AddField(
            model_name='datarow',
            name='graph_info',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='datarow',
            name='graph_order',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='datarow',
            name='graph_scale',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='datarow',
            name='graph_title',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='datarow',
            name='graph_vlabel',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='datarow',
            name='info',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='datarow',
            name='label',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='datarow',
            name='max',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='datarow',
            name='min',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='datarow',
            name='negative',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='datarow',
            name='type',
            field=models.CharField(max_length=200, blank=True),
        ),
        migrations.AddField(
            model_name='datarow',
            name='update_rate',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='datarow',
            name='warning',
            field=models.CharField(max_length=100, blank=True),
        ),
    ]
