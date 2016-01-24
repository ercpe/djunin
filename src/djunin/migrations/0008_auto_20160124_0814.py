# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0007_auto_20160124_0757'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='graphoption',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='graphoption',
            name='graph',
        ),
        migrations.DeleteModel(
            name='GraphOption',
        ),
    ]
