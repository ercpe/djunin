# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0015_auto_20160207_1503'),
    ]

    operations = [
        migrations.AlterField(
            model_name='graph',
            name='graph_period',
            field=models.CharField(default=b'second', max_length=150, blank=True),
        ),
        migrations.AlterField(
            model_name='graph',
            name='name',
            field=models.CharField(max_length=250, db_index=True),
        ),
        migrations.AlterField(
            model_name='node',
            name='group',
            field=models.CharField(max_length=250, db_index=True),
        ),
        migrations.AlterField(
            model_name='node',
            name='name',
            field=models.CharField(max_length=250, db_index=True),
        ),
    ]
