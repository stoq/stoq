# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
## Author(s):  Lincoln Molica           <lincoln@async.com.br>
##             Johan Dahlin             <jdahlin@async.com.br>
##
""" This module tests all fiscal data"""

from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.payment.group import AbstractPaymentGroup

from stoqlib.domain.test.domaintest import DomainTest

class TestCfopData(DomainTest):
    def testGetDescription(self):
        cfop = CfopData(code=u"2365", description=u"blabla",
                        connection=self.trans)
        full_desc = cfop.get_description()
        self.assertEqual(full_desc, u"%s %s" % (u"2365", u"blabla"))


class TestAbstractFiscalBookEntry(DomainTest):

    def testReverseEntry(self):
        entry = self.create_abstract_fiscal_book_entry()
        self.assertRaises(NotImplementedError, entry.reverse_entry, 0xdeadbeef)

    def testHasEntryByPaymentGroup(self):
        new_payment_group = AbstractPaymentGroup.select(
            connection=self.trans)[0]

        entry = self.create_abstract_fiscal_book_entry()
        self.failUnless(entry.has_entry_by_payment_group(
            self.trans, entry.payment_group))
        self.failIf(entry.has_entry_by_payment_group(
            self.trans, new_payment_group))

    def test_get_entry_by_payment_group(self):
        new_payment_group = AbstractPaymentGroup.select(
            connection=self.trans)[0]

        entry = self.create_abstract_fiscal_book_entry()

        self.failIf(entry.get_entry_by_payment_group(
                        self.trans, new_payment_group))


class TestIcmsIpiBookEntry(DomainTest):
    def testReverseEntry(self):
       icmsipibookentry = self.create_icms_ipi_book_entry()
       reversal = icmsipibookentry.reverse_entry(100)
       self.assertEquals(reversal.icms_value, 10)
       self.assertEquals(reversal.ipi_value, 10)


class TestIssBookEntry(DomainTest):
    def testReverseEntry(self):
       issbookentry = self.create_iss_book_entry()
       reversal = issbookentry.reverse_entry(201)
       self.assertEquals(reversal.iss_value, 10)
