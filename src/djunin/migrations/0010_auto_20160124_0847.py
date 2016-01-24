# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0009_auto_20160124_0844'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='datarowoption',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='datarowoption',
            name='datarow',
        ),
        migrations.DeleteModel(
            name='DataRowOption',
        ),
    ]
