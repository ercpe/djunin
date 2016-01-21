# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='graph',
            name='parent',
            field=models.ForeignKey(related_name='subgraphs', blank=True, to='djunin.Graph', null=True),
        ),
    ]
