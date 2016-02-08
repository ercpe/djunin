# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0017_auto_20160208_0800'),
    ]

    operations = [
        migrations.AlterField(
            model_name='graph',
            name='graph_args_lower_limit',
            field=models.BigIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='graph',
            name='graph_args_upper_limit',
            field=models.BigIntegerField(null=True, blank=True),
        ),
    ]
