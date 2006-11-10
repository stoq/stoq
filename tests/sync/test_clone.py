# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Henrique Romano  <henrique@async.com.br>
##

from tests.sync.base import SyncTest
from stoqlib.database.policy import get_policy_by_name
from stoqlib.database.synchronization import get_tables
from stoqlib.database.runtime import new_transaction
from stoqlib.domain.transaction import TransactionEntry
from stoqlib.enums import SyncPolicy

class TestClone(SyncTest):
    def testClone(self):
        self.switch_to_shop()
        shop_trans = new_transaction()
        self.switch_to_office()
        office_trans = new_transaction()

        policy = get_policy_by_name("shop")
        for table in get_tables(policy, pfilter=(SyncPolicy.FROM_TARGET, )):
            if table is TransactionEntry:
                continue
            office_count = table.select(connection=office_trans).count()
            shop_count = table.select(connection=shop_trans).count()
            self.failUnlessEquals(office_count, shop_count,
                                  ("The shop should have %d items in the "
                                   "table %s, got %d"
                                   % (office_count, table.sqlmeta.table,
                                      shop_count)))


