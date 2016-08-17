# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0010_auto_20160124_0847'),
    ]

    operations = [
        migrations.AddField(
            model_name='datarow',
            name='do_graph',
            field=models.BooleanField(default=True),
        ),
    ]
