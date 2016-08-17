# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0018_auto_20160208_0811'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datarow',
            name='rrdfile',
            field=models.CharField(max_length=255),
        ),
    ]
