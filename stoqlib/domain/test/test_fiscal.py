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
## Author(s): Lincoln Molica  lincoln@async.com.br
##
""" This module tests all fiscal data"""

from stoqlib.domain.person import Person
from stoqlib.domain.payment.payment import AbstractPaymentGroup
from stoqlib.domain.fiscal import (CfopData,
                                   AbstractFiscalBookEntry,
                                   IcmsIpiBookEntry, IssBookEntry)
from stoqlib.exceptions import DatabaseInconsistency, StoqlibError
from stoqlib.database.runtime import get_current_branch

from stoqlib.domain.test.domaintest import DomainTest

def get_cfopdata(conn):
    return CfopData(code=u"2365", description=u"blabla", connection=conn)

def get_branch(conn):
    return get_current_branch(conn)

def get_drawee(conn):
    people = Person.select(connection=conn)
    assert people
    return people[0]

def get_payment_group(conn):
    groups = AbstractPaymentGroup.select(connection=conn)
    assert groups
    return groups[0]

def get_new_payment_group(conn):
    return AbstractPaymentGroup(connection=conn)


def get_abstract_fiscal_book_entry(conn, identifier):
    print identifier
    cfop = get_cfopdata(conn)
    branch = get_branch(conn)
    drawee = get_drawee(conn)
    payment_group = AbstractPaymentGroup(connection=conn)
    return AbstractFiscalBookEntry(identifier=identifier, invoice_number=2,
                                   cfop=cfop, branch=branch,
                                   drawee=drawee,
                                   payment_group=payment_group,
                                   connection=conn)

def get_IcmsIpiBookEntry(conn, identifier):
    cfop = get_cfopdata(conn)
    branch = get_branch(conn)
    drawee = get_drawee(conn)
    payment_group = AbstractPaymentGroup(connection=conn)
    return IcmsIpiBookEntry(connection=conn, cfop=cfop, branch=branch,
                            drawee=drawee, payment_group=payment_group,
                            icms_value=10, ipi_value=10, invoice_number=200,
                            identifier=identifier)

def get_IssBookEntry(conn, identifier):
    cfop = get_cfopdata(conn)
    branch = get_branch(conn)
    drawee = get_drawee(conn)
    payment_group = AbstractPaymentGroup(connection=conn)
    return IssBookEntry(connection=conn, cfop=cfop, branch=branch,
                        drawee=drawee, payment_group=payment_group,
                        iss_value=10, invoice_number=201,
                        identifier=identifier)


class TestCfopData(DomainTest):

    def test_get_description(self):
        cfop = get_cfopdata(self.trans)
        full_desc = cfop.get_description()
        assert full_desc == u"%s %s" % (u"2365", u"blabla")


class TestAbstractFiscalBookEntry(DomainTest):

    def get_foreign_key_data(self):
        cfop = get_cfopdata(self.trans)
        branch = get_branch(self.trans)
        drawee = get_drawee(self.trans)
        payment_group = AbstractPaymentGroup(connection=self.trans)
        return cfop, branch, drawee, payment_group

    def test_reverse_entry(self):
        afbe = get_abstract_fiscal_book_entry(self.trans, 11)
        self.assertRaises(NotImplementedError, afbe.reverse_entry, 11)

    def test_get_reversal_clone(self):
        afbe = get_abstract_fiscal_book_entry(self.trans, 12)
        afbe_reversal = afbe.get_reversal_clone(invoice_number=13)
        self.assertEquals(afbe_reversal.invoice_number, 13)

    def test_get_entries_by_payment_group(self):
        afbe = get_abstract_fiscal_book_entry(self.trans, 13)
        assert afbe._get_entries_by_payment_group(self.trans,
                                                  afbe.payment_group)
        almost_same_afbe = get_abstract_fiscal_book_entry(self.trans, 14)
        almost_same_afbe.payment_group = afbe.payment_group
        self.assertRaises(DatabaseInconsistency,
                          afbe._get_entries_by_payment_group,
                          self.trans, afbe.payment_group)

    def test_has_entry_by_payment_group(self):
        new_payment_group = get_new_payment_group(self.trans)
        afbe = get_abstract_fiscal_book_entry(self.trans, 15)
        assert afbe.has_entry_by_payment_group(self.trans,
                                               afbe.payment_group)
        assert not afbe.has_entry_by_payment_group(self.trans,
                                                   new_payment_group)

    def test_get_entry_by_payment_group(self):
        afbe = get_abstract_fiscal_book_entry(self.trans, 16)
        new_payment_group = get_new_payment_group(self.trans)
        self.assertRaises(StoqlibError, afbe.get_entry_by_payment_group,
                          self.trans, new_payment_group)


class TestIcmsIpiBookEntry(DomainTest):

    def test_reverse_entry(self):
       icmsipibookentry = get_IcmsIpiBookEntry(self.trans, 17)
       reversal = icmsipibookentry.reverse_entry(100)
       self.assertEquals(reversal.icms_value, -10)
       self.assertEquals(reversal.ipi_value, -10)


class TestIssBookEntry(DomainTest):

    def test_reverse_entry(self):
       issbookentry = get_IssBookEntry(self.trans, 18)
       reversal = issbookentry.reverse_entry(201)
       self.assertEquals(reversal.iss_value, -10)
