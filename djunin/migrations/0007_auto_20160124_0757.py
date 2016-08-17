# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0006_auto_20160124_0705'),
    ]

    operations = [
        migrations.AddField(
            model_name='graph',
            name='graph_args_lower_limit',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='graph',
            name='graph_args_upper_limit',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
