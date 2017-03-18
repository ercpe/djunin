# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def fill_rddfile(apps, schmema_editor):
    DataRow = apps.get_model('djunin', 'DataRow')
    DataRowOption = apps.get_model('djunin', 'DataRowOption')

    datarows = DataRow.objects.filter(rrdfile=None).select_related('graph', 'graph__node', 'graph__parent', 'graph__parent__node')

    for dr in datarows:
        try:
            dr_type = dr.options.get(key='type').value
        except DataRowOption.DoesNotExist:
            dr_type = 'GAUGE'

        dr.rrdfile = "%s/%s-%s-%s-%s.rrd" % (dr.graph.node.group, dr.graph.node.name, dr.graph.name, dr.name, dr_type.lower()[0])
        dr.save()


class Migration(migrations.Migration):

    dependencies = [
        ('djunin', '0004_auto_20160121_0519'),
    ]

    operations = [
        migrations.AddField(
            model_name='datarow',
            name='rrdfile',
            field=models.CharField(max_length=255, unique=True, null=True, blank=True),
        ),
        migrations.RunPython(fill_rddfile),
        migrations.AlterField(
            model_name='datarow',
            name='rrdfile',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
