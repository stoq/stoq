# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from stoqlib.database.runtime import new_transaction
from stoqlib.database.orm import ORMObjectIntegrityError, IntCol
from stoqlib.domain.base import Domain

from stoqlib.domain.test.domaintest import DomainTest


class Ding(Domain):
    field = IntCol(default=0)

    def __init__(self, connection, field=None):
        Domain.__init__(self, connection=connection, field=field)
        self.called = False


trans = new_transaction()
for table in (Ding,):
    table_name = table.sqlmeta.table
    if trans.tableExists(table_name):
        trans.dropTable(table_name, cascade=True)
    table.createTable(connection=trans)
trans.commit()


class TestSelect(DomainTest):
    def testSelectOne(self):
        self.assertEquals(Ding.selectOne(connection=self.trans), None)
        ding1 = Ding(connection=self.trans)
        self.assertEquals(Ding.selectOne(connection=self.trans), ding1)
        Ding(connection=self.trans)
        self.assertRaises(ORMObjectIntegrityError,
                          Ding.selectOne, connection=self.trans)

    def testSelectOneBy(self):
        Ding(connection=self.trans)

        self.assertEquals(
            None, Ding.selectOneBy(field=1, connection=self.trans))
        ding1 = Ding(connection=self.trans, field=1)
        self.assertEquals(
            ding1, Ding.selectOneBy(field=1, connection=self.trans))
        Ding(connection=self.trans, field=1)
        self.assertRaises(
            ORMObjectIntegrityError,
            Ding.selectOneBy, field=1, connection=self.trans)
