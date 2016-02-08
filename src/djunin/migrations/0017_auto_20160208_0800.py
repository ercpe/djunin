# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0016_auto_20160208_0645'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='graph',
            unique_together=set([('node', 'parent', 'name')]),
        ),
    ]
