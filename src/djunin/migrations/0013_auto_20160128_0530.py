# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0012_auto_20160125_0605'),
    ]

    operations = [
        migrations.AlterField(
            model_name='graph',
            name='graph_scale',
            field=models.BooleanField(default=True),
        ),
    ]
