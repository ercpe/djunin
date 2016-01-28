# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0013_auto_20160128_0530'),
    ]

    operations = [
        migrations.RunSQL(['UPDATE djunin_datarow SET graph_scale = 1 WHERE graph_scale IS NULL']),
        migrations.AlterField(
            model_name='datarow',
            name='graph_scale',
            field=models.BooleanField(default=2),
            preserve_default=False,
        ),
    ]
