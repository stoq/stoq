# -*- coding: utf-8 -*-
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
""" Test case for stoqlib/domain/system.py module.  """

import mock

from stoqlib.domain.system import SystemTable
from stoqlib.domain.test.domaintest import DomainTest

__tests__ = 'stoqlib/domain/system.py'


class TestSystemTable(DomainTest):
    def test_is_available(self):
        self.assertTrue(SystemTable.is_available(self.store))

        store = mock.Mock()
        store.table_exists.return_value = False
        self.assertFalse(SystemTable.is_available(store))

        self.assertEquals(store.find.call_count, 0)

        store.table_exists.return_value = True
        store.find.return_value = False
        self.assertFalse(SystemTable.is_available(store))

        store.find.assert_called_once_with(SystemTable)
