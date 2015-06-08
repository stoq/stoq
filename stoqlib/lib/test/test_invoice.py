# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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

import datetime
import os

from stoqdrivers.enum import TaxType

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.invoice import InvoiceLayout, InvoiceField
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.sellable import SellableTaxConstant
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.diffutils import diff_files
from stoqlib.lib.invoice import SaleInvoice
from stoqlib.lib.unittestutils import get_tests_datadir


def compare_invoice_file(invoice, basename):
    expected = basename + '-expected.txt'
    output = basename + '-output.txt'

    fp = open(output, 'w')
    for n, page in enumerate(invoice.generate_pages()):
        fp.write('-- PAGE %d - START ----\n' % (n + 1, ))
        for line in page:
            fp.write(line.tostring())
        fp.write('-- PAGE %d - END ----\n' % (n + 1, ))
    fp.close()
    expected = get_tests_datadir(expected)
    diff = diff_files(expected, output)
    os.unlink(output)
    if diff:
        raise AssertionError('%s\n%s' % ("Files differ, output:", diff))


class InvoiceTest(DomainTest):
    def _add_payments(self, sale):
        method = PaymentMethod.get_by_name(self.store, u'money')
        payment = method.create_payment(Payment.TYPE_IN, sale.group, sale.branch,
                                        sale.get_sale_subtotal())
        payment.due_date = datetime.datetime(2000, 1, 1)

    def _add_product(self, sale, tax=None, price=None, code=None):
        product = self.create_product(price=price)
        sellable = product.sellable
        if code:
            sellable.code = code
        sellable.tax_constant = SellableTaxConstant(
            description=unicode(tax),
            tax_type=int(TaxType.CUSTOM),
            tax_value=tax,
            store=self.store)
        sale.add_sellable(sellable, quantity=1)
        self.create_storable(product, get_current_branch(self.store), stock=100)
        return sellable

    def test_sale_invoice(self):
        sale = self.create_sale()
        for i in range(10):
            price = 50 + i
            code = unicode(1000 + i)
            self._add_product(sale, tax=18, price=price, code=code)

        sale.order()
        self._add_payments(sale)
        sale.confirm()
        sale.client = self.create_client()
        address = self.create_address()
        address.person = sale.client.person

        layout = self.store.find(InvoiceLayout).one()
        layout.continuous_page = False
        invoice = SaleInvoice(sale, layout)
        invoice.today = datetime.datetime(2007, 1, 1, 10, 20, 30)

        try:
            compare_invoice_file(invoice, 'sale-invoice')
        except AssertionError as e:
            self.fail(e)

    def test_sale_invoice_continuous_page(self):
        sale = self.create_sale()
        for i in range(10):
            price = 50 + i
            code = unicode(1000 + i)
            self._add_product(sale, tax=18, price=price, code=code)

        sale.order()
        self._add_payments(sale)
        sale.confirm()
        sale.client = self.create_client()
        address = self.create_address()
        address.person = sale.client.person

        layout = self.store.find(InvoiceLayout).one()
        layout.continuous_page = True
        invoice = SaleInvoice(sale, layout)
        invoice.today = datetime.datetime(2007, 1, 1, 10, 20, 30)

        try:
            compare_invoice_file(invoice, 'sale-invoice-continuous')
        except AssertionError as e:
            self.fail(e)

    def test_invoice_without_client(self):
        sale = self.create_sale()
        for i in range(10):
            price = 50 + i
            code = unicode(1000 + i)
            self._add_product(sale, tax=18, price=price, code=code)
        sale.order()
        self._add_payments(sale)
        sale.confirm()

        layout = self.store.find(InvoiceLayout).one()
        layout.continuous_page = True
        invoice = SaleInvoice(sale, layout)
        invoice.today = datetime.datetime(2007, 1, 1, 10, 20, 30)

        try:
            compare_invoice_file(invoice, 'sale-invoice-without-client')
        except AssertionError as e:
            self.fail(e)

    def test_has_invoice_number(self):
        sale = self.create_sale()
        for i in range(10):
            self._add_product(sale, tax=18, price=50 + i)

        sale.order()
        self._add_payments(sale)
        sale.confirm()
        sale.client = self.create_client()
        address = self.create_address()
        address.person = sale.client.person

        layout = self.store.find(InvoiceLayout).one()
        invoice = SaleInvoice(sale, layout)
        self.assertFalse(invoice.has_invoice_number())

        field = self.store.find(InvoiceField, field_name=u'INVOICE_NUMBER').one()
        if field is None:
            field = InvoiceField(x=0, y=0, width=6, height=1, layout=layout,
                                 field_name=u'INVOICE_NUMBER',
                                 store=self.store)
        else:
            field.layout = layout

        new_invoice = SaleInvoice(sale, layout)
        self.assertTrue(new_invoice.has_invoice_number())
