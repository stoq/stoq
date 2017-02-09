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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" This module tests all fiscal data"""

__tests__ = 'stoqlib/domain/fiscal.py'


import mock

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.fiscal import CfopData, FiscalBookEntry, Invoice
from stoqlib.domain.test.domaintest import DomainTest


class TestCfopData(DomainTest):
    def test_get_description(self):
        cfop = CfopData(code=u"2365", description=u"blabla",
                        store=self.store)
        full_desc = cfop.get_description()
        self.assertEqual(full_desc, u"%s %s" % (u"2365", u"blabla"))


class TestIcmsIpiBookEntry(DomainTest):

    def test_reverse_entry(self):
        entry = self.create_icms_ipi_book_entry()
        reversal = entry.reverse_entry(100)
        self.assertEquals(reversal.icms_value, 10)
        self.assertEquals(reversal.ipi_value, 10)

    def test_create_product_entry(self):
        sale = self.create_sale()
        sale.add_sellable(self.create_sellable(), price=150)
        book_entry = FiscalBookEntry.create_product_entry(
            self.store,
            sale.group, sale.cfop, sale.coupon_id,
            123)
        self.failUnless(book_entry)
        self.assertEquals(book_entry.icms_value, 123)
        self.assertEquals(book_entry.entry_type,
                          FiscalBookEntry.TYPE_PRODUCT)

    def test_has_entry_by_payment_group(self):
        payment_group = self.create_payment_group()
        entry = self.create_icms_ipi_book_entry()

        self.failUnless(entry.has_entry_by_payment_group(
            self.store, entry.payment_group, entry.entry_type))
        self.failIf(entry.has_entry_by_payment_group(
            self.store, payment_group, entry.entry_type))

    def test_get_entry_by_payment_group(self):
        payment_group = self.create_payment_group()
        entry = self.create_icms_ipi_book_entry()

        self.failIf(entry.get_entry_by_payment_group(
            self.store, payment_group,
            entry.entry_type))


class TestIssBookEntry(DomainTest):

    def test_reverse_entry(self):
        entry = self.create_iss_book_entry()
        reversal = entry.reverse_entry(201)
        self.assertEquals(reversal.iss_value, 10)

    def test_create_service_entry(self):
        sale = self.create_sale()
        sale.add_sellable(self.create_sellable(), price=150)
        book_entry = FiscalBookEntry.create_service_entry(
            self.store,
            sale.group,
            sale.cfop,
            sale.service_invoice_number,
            123)
        self.failUnless(book_entry)
        self.assertEquals(book_entry.iss_value, 123)
        self.assertEquals(book_entry.entry_type,
                          FiscalBookEntry.TYPE_SERVICE)

    def test_has_entry_by_payment_group(self):
        payment_group = self.create_payment_group()
        entry = self.create_iss_book_entry()

        self.failUnless(entry.has_entry_by_payment_group(
            self.store, entry.payment_group, entry.entry_type))
        self.failIf(entry.has_entry_by_payment_group(
            self.store, payment_group, entry.entry_type))

    def test_get_entry_by_payment_group(self):
        payment_group = self.create_payment_group()
        entry = self.create_iss_book_entry()

        self.failIf(entry.get_entry_by_payment_group(
            self.store, payment_group,
            entry.entry_type))


class TestInvoice(DomainTest):
    def test_get_next_invoice_number(self):
        with mock.patch('stoqlib.lib.pluginmanager.PluginManager.is_active') as is_active:
            is_active.return_value = True
            main_branch = get_current_branch(self.store)
            sale = self.create_sale(branch=main_branch)
            sale.invoice.series = 1
            sale.invoice.invoice_number = 1234
            self.add_product(sale)
            self.add_payments(sale, u'money')
            sale.order()
            sale.confirm()

            last_invoice_number = Invoice.get_last_invoice_number(self.store,
                                                                  series=1)
            next_invoice_number = Invoice.get_next_invoice_number(self.store,
                                                                  series=1)
            self.assertEquals(last_invoice_number, 1234)
            self.assertEquals(next_invoice_number, 1235)

            # Creating a transfer order on same branch.
            transfer = self.create_transfer_order(source_branch=main_branch)
            transfer.invoice.series = 1
            transfer.invoice.invoice_number = next_invoice_number
            self.create_transfer_order_item(transfer)
            transfer.send()
            next_invoice_number = Invoice.get_next_invoice_number(self.store, series=1)
            self.assertEquals(transfer.invoice.invoice_number, 1235)
            self.assertEquals(next_invoice_number, 1236)

            # Creating a new sale and new tranfer on a different branch
            with mock.patch('stoqlib.domain.fiscal.get_current_branch') as get_branch:
                new_branch = self.create_branch()
                get_branch.return_value = new_branch
                new_sale = self.create_sale(branch=new_branch)
                new_sale.invoice.series = 1
                new_sale.invoice.invoice_number = 1234
                last_invoice_number = Invoice.get_last_invoice_number(self.store, series=1)
                next_invoice_number = Invoice.get_next_invoice_number(self.store, series=1)
                self.assertEquals(last_invoice_number, 1234)
                self.assertEquals(next_invoice_number, 1235)

                new_transfer = self.create_transfer_order(source_branch=new_branch)
                new_transfer.invoice.series = 1
                new_transfer.invoice.invoice_number = next_invoice_number
                self.create_transfer_order_item(new_transfer)
                new_transfer.send()
                next_invoice_number = Invoice.get_next_invoice_number(self.store, series=1)
                self.assertEquals(new_transfer.invoice.invoice_number, 1235)
                self.assertEquals(next_invoice_number, 1236)

    def test_nfe_invoice(self):
        branch = self.create_branch()
        current_mode = Invoice.NFE_MODE
        sale = self.create_sale(branch=branch)
        invoice_exists = sale.invoice.check_unique_invoice_number_by_branch(
            1, branch, current_mode)
        self.assertFalse(invoice_exists)
        sale.invoice.invoice_number = 1
        sale.invoice.series = 1
        sale.invoice.mode = current_mode
        sale.invoice.on_create()
        sale.invoice.invoice_number = 2
        sale.invoice.on_update()
