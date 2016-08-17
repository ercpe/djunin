# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('djunin', '0023_auto_20160522_0657'),
    ]

    operations = [
        migrations.CreateModel(
            name='DjuninNodePermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('node', models.ForeignKey(related_name='permissions', to='djunin.Node')),
                ('object_ct', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterUniqueTogether(
            name='djuninnodepermission',
            unique_together=set([('node', 'object_ct', 'object_id')]),
        ),
    ]
