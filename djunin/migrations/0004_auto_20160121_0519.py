# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0003_auto_20160121_0512'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datarowoption',
            name='datarow',
            field=models.ForeignKey(related_name='options', to='djunin.DataRow'),
        ),
        migrations.AlterField(
            model_name='graphoption',
            name='graph',
            field=models.ForeignKey(related_name='options', to='djunin.Graph'),
        ),
    ]
