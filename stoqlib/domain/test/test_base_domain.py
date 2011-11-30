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

from zope.interface import implements, Interface

from stoqlib.database.orm import ORMObjectMoreThanOneResultError, IntCol
from stoqlib.database.runtime import new_transaction
from stoqlib.domain.base import Domain, ModelAdapter

from stoqlib.domain.test.domaintest import DomainTest


class IDong(Interface):
    pass


class Ding(Domain):
    field = IntCol(default=0)

    def __init__(self, connection, field=None):
        Domain.__init__(self, connection=connection, field=field)
        self.called = False

    def facet_IDong_add(self, **kwargs):
        self.called = True
        adapter_klass = self.getAdapterClass(IDong)
        return adapter_klass(self, **kwargs)


class DingAdaptToDong(ModelAdapter):
    implements(IDong)
    facetfield = IntCol(default=0)

Ding.registerFacet(DingAdaptToDong, IDong)

trans = new_transaction()
for table in (Ding, DingAdaptToDong):
    table_name = table.sqlmeta.table
    if trans.tableExists(table_name):
        trans.dropTable(table_name, cascade=True)
    table.createTable(connection=trans)
trans.commit()


class TestFacet(DomainTest):
    def testAdd(self):
        ding = Ding(connection=self.trans)
        self.assertEqual(IDong(ding, None), None)

        dong = ding.addFacet(IDong, connection=self.trans)
        self.assertEqual(IDong(ding), dong)

    def testAddHook(self):
        ding = Ding(connection=self.trans)
        self.assertEqual(ding.called, False)
        ding.addFacet(IDong, connection=self.trans)
        self.assertEqual(ding.called, True)

    def testGetFacets(self):
        ding = Ding(connection=self.trans)
        self.assertEqual(ding.getFacets(), [])

        facet = ding.addFacet(IDong, connection=self.trans)
        self.assertEqual(ding.getFacets(), [facet])

    def testRegisterAndGetTypes(self):
        class IDang(Interface):
            pass

        class DingAdaptToDang(ModelAdapter):
            implements(IDang)

        self.assertEqual(Ding.getFacetTypes(), [DingAdaptToDong])

        Ding.registerFacet(DingAdaptToDang, IDang)

        self.failUnless(len(Ding.getFacetTypes()), 2)
        self.failUnless(DingAdaptToDang in Ding.getFacetTypes())


class TestSelect(DomainTest):
    def testSelectOne(self):
        self.assertEquals(Ding.selectOne(connection=self.trans), None)
        ding1 = Ding(connection=self.trans)
        self.assertEquals(Ding.selectOne(connection=self.trans), ding1)
        Ding(connection=self.trans)
        self.assertRaises(ORMObjectMoreThanOneResultError,
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
            ORMObjectMoreThanOneResultError,
            Ding.selectOneBy, field=1, connection=self.trans)

    def testISelect(self):
        self.assertEqual(Ding.iselect(IDong, connection=self.trans).count(), 0)
        ding = Ding(connection=self.trans)
        ding.addFacet(IDong, connection=self.trans)
        self.assertEqual(Ding.iselect(IDong, connection=self.trans).count(), 1)

    def testISelectOne(self):
        self.assertEqual(Ding.iselectOne(IDong, connection=self.trans), None)
        ding = Ding(connection=self.trans)
        dong = ding.addFacet(IDong, connection=self.trans)

        self.assertEqual(Ding.iselectOne(IDong, connection=self.trans), dong)

        ding2 = Ding(connection=self.trans)
        ding2.addFacet(IDong, connection=self.trans)

        self.assertRaises(
            ORMObjectMoreThanOneResultError,
            Ding.iselectOne, IDong, connection=self.trans)

    def testISelectBy(self):
        ding = Ding(connection=self.trans)
        ding.addFacet(IDong, connection=self.trans)

        results = Ding.iselectBy(IDong, facetfield=1, connection=self.trans)
        self.assertEquals(results.count(), 0)

        ding = Ding(connection=self.trans)
        ding.addFacet(IDong, facetfield=1, connection=self.trans)

        results = Ding.iselectBy(IDong, facetfield=1, connection=self.trans)
        self.assertEquals(results.count(), 1)

    def testISelectOneBy(self):
        ding = Ding(connection=self.trans)
        ding.addFacet(IDong, connection=self.trans)

        self.assertEquals(
            None, Ding.iselectOneBy(IDong, facetfield=1,
                                    connection=self.trans))
        ding1 = Ding(connection=self.trans)
        dong1 = ding1.addFacet(IDong, facetfield=1, connection=self.trans)
        self.assertEquals(
            dong1, Ding.iselectOneBy(IDong, facetfield=1,
                                     connection=self.trans))
        ding2 = Ding(connection=self.trans)
        ding2.addFacet(IDong, facetfield=1, connection=self.trans)
        self.assertRaises(
            ORMObjectMoreThanOneResultError,
            Ding.iselectOneBy, IDong, facetfield=1, connection=self.trans)
