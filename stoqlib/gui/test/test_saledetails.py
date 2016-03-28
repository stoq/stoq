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
import unittest

import mock
from kiwi.ui.objectlist import ObjectTree

from stoqlib.database.runtime import StoqlibStore, get_current_branch
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.sale import SaleView, SaleComment
from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localdate
from stoqlib.reporting.boleto import BillReport
from stoqlib.reporting.booklet import BookletReport
from stoqlib.reporting.sale import SaleOrderReport


class TestSaleDetails(GUITest):

    def _create_sale(self):
        today = localdate(2010, 12, 1)
        client = self.create_client()

        # new sale
        sale = self.create_sale(branch=get_current_branch(self.store))
        sale.identifier = 123
        sale.client = client
        sale.open_date = today
        sale.discount_value = Decimal('15')
        sale.surcharge_value = Decimal('8')

        # Product
        item_ = self.create_sale_item(sale, product=True)
        self.create_storable(item_.sellable.product, sale.branch, 1)
        # Service
        item = self.create_sale_item(sale, product=False)
        item.estimated_fix_date = today

        # Payments
        payment = self.add_payments(sale, date=today)[0]
        payment.identifier = 999
        payment.group.payer = client.person

        sale.order()
        sale.confirm()
        sale.group.pay()

        payment.paid_date = today

        return sale

    def test_show(self):
        sale = self._create_sale()
        # SaleDetailsDialog needs a SaleView model
        model = self.store.find(SaleView, id=sale.id).one()
        dialog = SaleDetailsDialog(self.store, model)
        self.assertTrue(isinstance(dialog.items_list, ObjectTree))
        self.check_editor(dialog, 'dialog-sale-details')

    @mock.patch('stoqlib.gui.dialogs.saledetails.print_report')
    def test_show_with_returns_and_comments(self, print_report):
        date = localdate(2010, 12, 10).date()

        sale = self._create_sale()
        returned_sale = sale.create_sale_return_adapter()
        returned_sale.return_()
        returned_sale.return_date = date

        # payments[0] is the sale's payment created on self._create_sale
        returned_payment = returned_sale.group.payments.find(
            Payment.identifier != 999).one()
        returned_payment.identifier = 666
        returned_payment.due_date = date
        returned_payment.paid_date = date

        comment = self.create_sale_comment(sale)
        comment.date = date

        model = self.store.find(SaleView, id=sale.id).one()

        dialog = SaleDetailsDialog(self.store, model)
        self.click(dialog.print_return_report)

        self.check_editor(dialog, 'dialog-sale-details-with-returns')

    def test_show_package_product(self):
        sale = self.create_sale()
        package = self.create_product(description=u'Package', is_package=True)
        component1 = self.create_product(description=u'Component 1', stock=3)
        component2 = self.create_product(description=u'Component 2', stock=2)
        self.create_product_component(product=package, component=component1)
        self.create_product_component(product=package, component=component2)
        parent = sale.add_sellable(package.sellable, quantity=1)
        sale.add_sellable(component1.sellable, quantity=1, parent=parent)
        sale.add_sellable(component2.sellable, quantity=1, parent=parent)

        sale.create_sale_return_adapter()

        model = self.store.find(SaleView, id=sale.id).one()
        dialog = SaleDetailsDialog(self.store, model)
        self.assertEquals(len(list(dialog.items_list)), 3)

    @mock.patch('stoqlib.gui.dialogs.saledetails.run_dialog')
    def test_client_details(self, run_dialog):
        sale = self.create_sale()
        sale.client = self.create_client()
        self.create_sale_item(sale, product=True)
        model = self.store.find(SaleView, id=sale.id).one()

        dialog = SaleDetailsDialog(self.store, model)
        self.click(dialog.details_button)

        args, kwargs = run_dialog.call_args
        editor, parent, store, model = args
        self.assertEquals(editor, ClientDetailsDialog)
        self.assertEquals(parent, dialog)
        self.assertEquals(model, sale.client)
        self.assertTrue(isinstance(store, StoqlibStore))

    @mock.patch('stoqlib.gui.dialogs.saledetails.BillReport.check_printable')
    @mock.patch('stoqlib.gui.dialogs.saledetails.print_report')
    def test_print_bill(self, print_report, check_printable):
        sale = self.create_sale()
        sale.client = self.create_client()
        self.create_sale_item(sale, product=True)
        payment = self.add_payments(sale, u'bill')[0]
        model = self.store.find(SaleView, id=sale.id).one()

        dialog = SaleDetailsDialog(self.store, model)
        self.assertSensitive(dialog, ['print_bills'])
        self.assertNotVisible(dialog, ['print_booklets'])

        # Just make sure we can print the bill
        check_printable.return_value = True
        self.click(dialog.print_bills)

        print_report.assert_called_once_with(BillReport, [payment])

    @mock.patch('stoqlib.gui.dialogs.saledetails.print_report')
    def test_print_booklet(self, print_report):
        sale = self.create_sale()
        sale.client = self.create_client()
        self.create_sale_item(sale, product=True)
        payment = self.add_payments(sale, u'store_credit')[0]
        model = self.store.find(SaleView, id=sale.id).one()

        dialog = SaleDetailsDialog(self.store, model)
        self.assertSensitive(dialog, ['print_booklets'])
        self.assertNotVisible(dialog, ['print_bills'])

        self.click(dialog.print_booklets)
        print_report.assert_called_once_with(BookletReport, [payment])

    @mock.patch('stoqlib.gui.dialogs.saledetails.print_report')
    def test_print_details(self, print_report):
        sale = self.create_sale()
        sale.client = self.create_client()
        self.create_sale_item(sale, product=True)
        model = self.store.find(SaleView, id=sale.id).one()

        dialog = SaleDetailsDialog(self.store, model)
        self.assertSensitive(dialog, ['print_button'])

        self.click(dialog.print_button)
        print_report.assert_called_once_with(SaleOrderReport, sale)

    @mock.patch('stoqlib.gui.dialogs.saledetails.api.new_store')
    @mock.patch('stoqlib.gui.dialogs.saledetails.run_dialog')
    def test_add_note(self, run_dialog, new_store):
        new_store.return_value = self.store
        run_dialog.return_value = False

        sale = self.create_sale()
        sale.client = self.create_client()
        self.create_sale_item(sale, product=True)
        model = self.store.find(SaleView, id=sale.id).one()

        dialog = SaleDetailsDialog(self.store, model)
        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.click(dialog.comment_add)

        args, kwargs = run_dialog.call_args
        editor, parent, store, model, prop_name = args
        self.assertEquals(editor, NoteEditor)
        self.assertEquals(parent, dialog)
        self.assertTrue(isinstance(model, SaleComment))
        self.assertTrue(isinstance(store, StoqlibStore))
        self.assertEquals(prop_name, 'comment')
        self.assertEquals(kwargs['title'], 'New Sale Comment')


if __name__ == '__main__':
    from stoqlib.api import api
    c = api.prepare_test()
    unittest.main()
