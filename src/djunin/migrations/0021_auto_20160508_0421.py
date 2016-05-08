# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0020_datarow_extinfo'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='datarow',
            options={'ordering': ('graph', 'name')},
        ),
        migrations.AlterModelOptions(
            name='graph',
            options={'ordering': ('node', 'name')},
        ),
        migrations.AlterModelOptions(
            name='node',
            options={'ordering': ('group', 'name')},
        ),
    ]
