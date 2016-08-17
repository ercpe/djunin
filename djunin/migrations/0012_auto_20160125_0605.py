# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0011_datarow_do_graph'),
    ]

    operations = [
        migrations.AlterField(
            model_name='graph',
            name='graph_category',
            field=models.CharField(default='other', max_length=250),
            preserve_default=False,
        ),
    ]
