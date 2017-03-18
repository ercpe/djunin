# -*- coding: utf-8 -*-

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from django.test import TestCase

from djunin.updater import Updater, Row

class UpdaterTestCase(TestCase):
    maxDiff = None

    def test_root_graph_parsing(self):
        updater = Updater()

        fp = StringIO('\n'.join([
            'version 0',
            'group;node:threads.graph_title Number of threads',
            'group;node:threads.graph_vlabel number of threads',
            'group;node:threads.graph_category processes',
            'group;node:threads.threads.graph_data_size normal',
            'group;node:threads.threads.label threads',
        ]))

        data = list(updater.prepare(fp))

        self.assertListEqual(data, [
            Row('group', 'node', 'threads', None, None, 'graph_title', 'Number of threads'),
            Row('group', 'node', 'threads', None, None, 'graph_vlabel', 'number of threads'),
            Row('group', 'node', 'threads', None, None, 'graph_category', 'processes'),
            Row('group', 'node', 'threads', None, 'threads', 'graph_data_size', 'normal'),
            Row('group', 'node', 'threads', None, 'threads', 'label', 'threads'),
        ])

    def test_subgraph_parsing(self):
        updater = Updater()

        fp = StringIO('\n'.join([
            'version 0',
            'group;node:diskstats_iops.graph_title Disk IOs per device',
            'group;node:diskstats_iops.graph_category disk',
            'group;node:diskstats_iops.xvda2.graph_title IOs for /dev/xvda2',
            'group;node:diskstats_iops.xvda2.avgwrrqsz.draw LINE1',
            'group;node:diskstats_iops.xvda2.avgwrrqsz.graph_data_size normal',
        ]))

        data = list(updater.prepare(fp))

        self.assertListEqual(data, [
            Row('group', 'node', 'diskstats_iops', None, None, 'graph_title', 'Disk IOs per device'),
            Row('group', 'node', 'diskstats_iops', None, None, 'graph_category', 'disk'),
            Row('group', 'node', 'diskstats_iops', 'xvda2', None, 'graph_title', 'IOs for /dev/xvda2'),
            Row('group', 'node', 'diskstats_iops', 'xvda2', 'avgwrrqsz', 'draw', 'LINE1'),
            Row('group', 'node', 'diskstats_iops', 'xvda2', 'avgwrrqsz', 'graph_data_size', 'normal'),
        ])

    def test_parse_graph_args_empty(self):
        updater = Updater()
        d = updater.parse_graph_args(None)
        self.assertEqual(d, {})

        d = updater.parse_graph_args('')
        self.assertEqual(d, {})

    def test_parse_graph_args(self):
        updater = Updater()
        d = updater.parse_graph_args('--base 1000 -r --lower-limit 0 --upper-limit 400')
        self.assertEqual(d, {
            'graph_args_base': '1000',
            'graph_args_lower_limit': '0',
            'graph_args_upper_limit': '400',
            'graph_args_rigid': True,
        })

        d = updater.parse_graph_args('--base 1000')
        self.assertEqual(d, {
            'graph_args_base': '1000',
        })
