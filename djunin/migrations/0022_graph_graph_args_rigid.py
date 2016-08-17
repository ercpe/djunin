# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0021_auto_20160508_0421'),
    ]

    operations = [
        migrations.AddField(
            model_name='graph',
            name='graph_args_rigid',
            field=models.BooleanField(default=False),
        ),
    ]
