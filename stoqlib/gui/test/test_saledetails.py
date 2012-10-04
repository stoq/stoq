# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

from decimal import Decimal
import datetime
import unittest

import mock
from stoqlib.gui.uitestutils import GUITest

from stoqlib.database.runtime import StoqlibTransaction, get_current_branch
from stoqlib.domain.sale import Sale, SaleView
from stoqlib.domain.product import Storable
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
from stoqlib.reporting.boleto import BillReport
from stoqlib.reporting.booklet import BookletReport
from stoqlib.reporting.sale import SaleOrderReport


class TestSaleDetails(GUITest):

    def _create_sale(self):
        today = datetime.date(2010, 12, 1)
        client = self.create_client()

        # new sale
        sale = self.create_sale(branch=get_current_branch(self.trans))
        sale.identifier = 123
        sale.client = client
        sale.open_date = today
        sale.discount_value = Decimal('15')
        sale.surcharge_value = Decimal('8')

        # Product
        item_ = self.create_sale_item(sale, product=True)
        storable = Storable(connection=self.trans,
                            product=item_.sellable.product)
        storable.increase_stock(1, sale.branch)
        # Service
        item = self.create_sale_item(sale, product=False)
        item.estimated_fix_date = today
        item.sellable.can_sell()

        # Payments
        payment = self.add_payments(sale, date=today)[0]
        payment.identifier = 999
        payment.group.payer = client.person

        sale.order()
        sale.confirm()
        sale.set_paid()

        payment.paid_date = today

        return sale

    def testShow(self):
        sale = self._create_sale()
        # SaleDetailsDialog needs a SaleView model
        model = SaleView.select(Sale.q.id == sale.id, connection=self.trans)[0]
        dialog = SaleDetailsDialog(self.trans, model)
        self.check_editor(dialog, 'dialog-sale-details')

    def testShowWithReturns(self):
        date = datetime.date(2010, 12, 10)

        sale = self._create_sale()
        returned_sale = sale.create_sale_return_adapter()
        returned_sale.return_()
        returned_sale.return_date = date
        # payments[0] is the sale's payment created on self._create_sale
        returned_payment = returned_sale.group.payments[1]
        returned_payment.identifier = 666
        returned_payment.due_date = date
        returned_payment.paid_date = date

        model = SaleView.select(Sale.q.id == sale.id, connection=self.trans)[0]
        dialog = SaleDetailsDialog(self.trans, model)
        self.check_editor(dialog, 'dialog-sale-details-with-returns')

    @mock.patch('stoqlib.gui.dialogs.saledetails.run_dialog')
    def testClientDetails(self, run_dialog):
        sale = self.create_sale()
        sale.client = self.create_client()
        self.create_sale_item(sale, product=True)
        model = SaleView.select(Sale.q.id == sale.id, connection=self.trans)[0]

        dialog = SaleDetailsDialog(self.trans, model)
        self.click(dialog.details_button)

        args, kwargs = run_dialog.call_args
        editor, parent, trans, model = args
        self.assertEquals(editor, ClientDetailsDialog)
        self.assertEquals(parent, dialog)
        self.assertEquals(model, sale.client)
        self.assertTrue(isinstance(trans, StoqlibTransaction))

    @mock.patch('stoqlib.gui.dialogs.saledetails.BillReport.check_printable')
    @mock.patch('stoqlib.gui.dialogs.saledetails.print_report')
    def testPrintBill(self, print_report, check_printable):
        sale = self.create_sale()
        sale.client = self.create_client()
        self.create_sale_item(sale, product=True)
        payment = self.add_payments(sale, 'bill')[0]
        model = SaleView.select(Sale.q.id == sale.id, connection=self.trans)[0]

        dialog = SaleDetailsDialog(self.trans, model)
        self.assertSensitive(dialog, ['print_bills'])
        self.assertNotVisible(dialog, ['print_booklets'])

        # Just make sure we can print the bill
        check_printable.return_value = True
        self.click(dialog.print_bills)

        print_report.assert_called_once_with(BillReport, [payment])

    @mock.patch('stoqlib.gui.dialogs.saledetails.print_report')
    def testPrintBooklet(self, print_report):
        sale = self.create_sale()
        sale.client = self.create_client()
        self.create_sale_item(sale, product=True)
        payment = self.add_payments(sale, 'store_credit')[0]
        model = SaleView.select(Sale.q.id == sale.id, connection=self.trans)[0]

        dialog = SaleDetailsDialog(self.trans, model)
        self.assertSensitive(dialog, ['print_booklets'])
        self.assertNotVisible(dialog, ['print_bills'])

        self.click(dialog.print_booklets)
        print_report.assert_called_once_with(BookletReport, [payment])

    @mock.patch('stoqlib.gui.dialogs.saledetails.print_report')
    def testPrintDetails(self, print_report):
        sale = self.create_sale()
        sale.client = self.create_client()
        self.create_sale_item(sale, product=True)
        model = SaleView.select(Sale.q.id == sale.id, connection=self.trans)[0]

        dialog = SaleDetailsDialog(self.trans, model)
        self.assertSensitive(dialog, ['print_button'])

        self.click(dialog.print_button)
        print_report.assert_called_once_with(SaleOrderReport, sale)


if __name__ == '__main__':
    from stoqlib.api import api
    c = api.prepare_test()
    unittest.main()
