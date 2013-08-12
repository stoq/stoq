# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

import itertools
import unittest

import mock

from stoqlib.database.orm import ORMObject
from stoqlib.database.tables import get_table_types, _tables_cache
from stoqlib.domain.plugin import InstalledPlugin
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.introspection import get_all_classes


def _introspect_tables():
    for klass in itertools.chain(get_all_classes('stoqlib/domain'),
                                 get_all_classes('plugins')):
        try:
            if not issubclass(klass, ORMObject):
                continue
        except TypeError:
            continue

        if getattr(klass, '__storm_table__', 'invalid') == 'invalid':
            continue

        yield klass


class TableTypeTest(DomainTest):
    @mock.patch('stoqlib.lib.pluginmanager.get_default_store')
    def test(self, get_default_store):
        # FIXME: get_table_types need plugins to be installed to get the
        # plugin's tables. PluginManager.installed_plugins_names will use the
        # default store to get the installed plugins, so mock it to the tests'
        # store, create all the missing InstalledPlugin. Change this to a mock
        # on installed_plugins_names when we can use newer versions of
        # python-mock (which suports properly property mocking)
        get_default_store.return_value = self.store
        for p_name in self.get_oficial_plugins_names():
            if self.store.find(InstalledPlugin, plugin_name=p_name).is_empty():
                InstalledPlugin(store=self.store,
                                plugin_name=p_name, plugin_version=1)

        # Depending on the order this test is runned, the cache will be
        # already filled. Clear it so it imports again and get plugins too
        _tables_cache.clear()
        expected = set(t.__name__ for t in get_table_types())
        introspected = set(t.__name__ for t in _introspect_tables())

        # Tables in either expected or introspected but not both
        difference = expected ^ introspected
        if difference:
            self.fail("Missing tables: %s\n"
                      "Please add them to stoqlib.database.tables or to the "
                      "plugin's get_tables" % (', '.join(sorted(difference), )))


if __name__ == '__main__':
    unittest.main()
