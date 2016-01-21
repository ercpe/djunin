# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DataRow',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=250, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Graph',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=250)),
                ('graph_category', models.CharField(max_length=250, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Node',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group', models.CharField(max_length=250)),
                ('name', models.CharField(max_length=250)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Option',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=250, db_index=True)),
                ('value', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterUniqueTogether(
            name='node',
            unique_together=set([('group', 'name')]),
        ),
        migrations.AddField(
            model_name='graph',
            name='node',
            field=models.ForeignKey(related_name='graphs', to='djunin.Node'),
        ),
        migrations.AddField(
            model_name='graph',
            name='options',
            field=models.ManyToManyField(to='djunin.Option'),
        ),
        migrations.AddField(
            model_name='graph',
            name='parent',
            field=models.ForeignKey(related_name='subgraphs', to='djunin.Graph'),
        ),
        migrations.AddField(
            model_name='datarow',
            name='graph',
            field=models.ForeignKey(related_name='datarows', to='djunin.Graph'),
        ),
        migrations.AddField(
            model_name='datarow',
            name='options',
            field=models.ManyToManyField(to='djunin.Option'),
        ),
        migrations.AlterUniqueTogether(
            name='graph',
            unique_together=set([('node', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='datarow',
            unique_together=set([('graph', 'name')]),
        ),
    ]
