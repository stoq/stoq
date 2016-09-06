# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2016 Stoq Tecnologia <http://stoq.link>
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
__tests__ = 'stoqlib/domain/plugin.py'

from stoqlib.lib.pluginmanager import PluginError
from stoqlib.domain.plugin import InstalledPlugin
from stoqlib.domain.test.domaintest import DomainTest


class TestCityLocation(DomainTest):
    """Tests for CityLocation class"""

    def test_create(self):
        # Creating the Plugin, setting its version to None and then creating it
        # again should just change the plugin_version to 0
        foo = InstalledPlugin.create(self.store, u'foo')
        foo.plugin_version = None

        foo = InstalledPlugin.create(self.store, u'foo')
        self.assertEquals(foo.plugin_version, 0)

        self.assertRaises(PluginError, InstalledPlugin.create,
                          self.store, u'foo')
