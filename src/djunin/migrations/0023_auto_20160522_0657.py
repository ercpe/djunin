# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0022_graph_graph_args_rigid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datarow',
            name='cdef',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='datarow',
            name='colour',
            field=models.CharField(max_length=7, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='datarow',
            name='critical',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='datarow',
            name='draw',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='datarow',
            name='graph_data_size',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='datarow',
            name='info',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='datarow',
            name='label',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='datarow',
            name='negative',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='datarow',
            name='type',
            field=models.CharField(max_length=200, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='datarow',
            name='warning',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
    ]
