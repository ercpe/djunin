# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0019_auto_20160208_0828'),
    ]

    operations = [
        migrations.AddField(
            model_name='datarow',
            name='extinfo',
            field=models.TextField(null=True, blank=True),
        ),
    ]
