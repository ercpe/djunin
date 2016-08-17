# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0002_auto_20160120_0543'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataRowOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=250, db_index=True)),
                ('value', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GraphOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=250, db_index=True)),
                ('value', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='datarow',
            name='options',
        ),
        migrations.RemoveField(
            model_name='graph',
            name='options',
        ),
        migrations.DeleteModel(
            name='Option',
        ),
        migrations.AddField(
            model_name='graphoption',
            name='graph',
            field=models.ForeignKey(to='djunin.Graph'),
        ),
        migrations.AddField(
            model_name='datarowoption',
            name='datarow',
            field=models.ForeignKey(to='djunin.DataRow'),
        ),
        migrations.AlterUniqueTogether(
            name='graphoption',
            unique_together=set([('graph', 'key')]),
        ),
        migrations.AlterUniqueTogether(
            name='datarowoption',
            unique_together=set([('datarow', 'key')]),
        ),
    ]
