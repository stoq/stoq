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
from stoqlib.domain.interfaces import (IPaymentGroup,
                                       ISellable,
                                       IStorable)
from stoqlib.domain.invoice import InvoiceLayout
from stoqlib.domain.payment.methods import MoneyPM
from stoqlib.domain.sellable import SellableTaxConstant
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.diffutils import diff_files
from stoqlib.lib.invoice import SaleInvoice
from stoqlib.lib import test


def compare_invoice_file(invoice, basename):
    expected = basename + '-expected.txt'
    output = basename + '-output.txt'

    fp = open(output, 'w')
    for n, page in enumerate(invoice.generate_pages()):
        fp.write('-- PAGE %d - START ----\n' % (n + 1,))
        for line in page:
            fp.write(line.tostring())
        fp.write('-- PAGE %d - END ----\n' % (n + 1,))
    fp.close()
    expected = os.path.join(test.__path__[0], expected)
    retval = diff_files(expected, output)
    os.unlink(output)
    if retval:
        raise AssertionError("Files differ, check output above")

class InvoiceTest(DomainTest):
    def _add_payments(self, sale, method_type=MoneyPM):
        group = IPaymentGroup(sale, None)
        if group is None:
            group = sale.addFacet(IPaymentGroup, connection=self.trans)

        method = method_type.selectOne(connection=self.trans)
        payment = method.create_inpayment(group,
                                          sale.get_sale_subtotal())
        payment.get_adapted().due_date = datetime.datetime(2000, 1, 1)

    def _add_product(self, sale, tax=None, price=None):
        product = self.create_product(price=price)
        sellable = ISellable(product)
        sellable.tax_constant = SellableTaxConstant(
            description=str(tax),
            tax_type=int(TaxType.CUSTOM),
            tax_value=tax,
            connection=self.trans)
        sale.add_sellable(sellable, quantity=1)
        storable = product.addFacet(IStorable, connection=self.trans)
        storable.increase_stock(100, get_current_branch(self.trans))
        return sellable

    def testSaleInvoice(self):
        sale = self.create_sale()
        for i in range(10):
            self._add_product(sale, tax=18, price=50+i)

        sale.order()
        self._add_payments(sale)
        sale.confirm()
        sale.client = self.create_client()
        address = self.create_address()
        address.person = sale.client.person

        layout = InvoiceLayout.selectOne(connection=self.trans)
        invoice = SaleInvoice(sale, layout)
        invoice.today = datetime.datetime(2007, 1, 1, 10, 20, 30)

        for n, sale_item in enumerate(sale.products):
            sale_item.sellable.id = 1000 + n

        compare_invoice_file(invoice, 'sale-invoice')
