# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

__tests__ = 'plugins/optical/opticalplugin.py'

from stoq.gui.test.baseguitest import BaseGUITest

from ..opticalplugin import OpticalPlugin


class TestOpticalUI(BaseGUITest):

    def test_migration(self):
        plugin = OpticalPlugin()
        migration = plugin.get_migration()
        self.assertEquals(migration.plugin_name, u'optical')
        self.assertEquals(migration.patch_resource_domain, u'optical')
        self.assertEquals(migration.patch_resource, u'sql')
        self.assertEquals(migration.patch_patterns, ['*.sql', '*.py'])

    def test_get_tables(self):
        plugin = OpticalPlugin()
        self.assertEquals(plugin.get_tables(), [
            ('opticaldomain', ['OpticalMedic',
                               'OpticalProduct',
                               'OpticalWorkOrder',
                               'OpticalPatientHistory',
                               'OpticalPatientMeasures',
                               'OpticalPatientTest',
                               'OpticalPatientVisualAcuity'])])

    def test_active(self):
        plugin = OpticalPlugin()
        self.assertIsNone(plugin.ui)
        plugin.activate()
        self.assertIsNotNone(plugin.ui)

    def test_get_server_tasks(self):
        plugin = OpticalPlugin()
        self.assertEquals(plugin.get_server_tasks(), [])

    def test_get_dbadmin_commands(self):
        plugin = OpticalPlugin()
        self.assertEquals(plugin.get_dbadmin_commands(), [])
