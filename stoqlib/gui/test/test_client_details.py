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

import unittest

import mock

from stoqlib.database.runtime import StoqlibStore
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.sale import SaleView
from stoqlib.domain.workorder import WorkOrder
from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.editors.paymenteditor import InPaymentEditor
from stoqlib.gui.editors.personeditor import ClientEditor
from stoqlib.gui.editors.workordereditor import WorkOrderEditor
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localtoday


class TestClientDetails(GUITest):

    def test_show(self):
        today = localtoday().date()
        client = self.create_client()
        # Nova venda
        sale = self.create_sale()
        sale.identifier = 123
        sale.client = client
        sale.open_date = today

        # Product
        sellable = self.create_sellable(description=u'Normal',
                                        storable=True, price=100)
        sale.add_sellable(sellable)
        # Service
        sellable2 = self.create_sellable(description=u'Service', product=False,
                                         price=100)
        item = sale.add_sellable(sellable2)
        item.estimated_fix_date = today
        # Payments
        payment = self.add_payments(sale, date=today)[0]
        payment.identifier = 999
        payment.group.payer = client.person
        # Call
        self.create_call(client.person)

        dialog = ClientDetailsDialog(self.store, client)
        self.check_editor(dialog, 'dialog-client-details')

    @mock.patch('stoqlib.gui.dialogs.clientdetails.run_person_role_dialog')
    def test_further_details(self, run_dialog):
        client = self.create_client()

        dialog = ClientDetailsDialog(self.store, client)
        new_store = 'stoqlib.gui.dialogs.clientdetails.api.new_store'
        with mock.patch(new_store) as new_store:
            with mock.patch.object(self.store, 'close'):
                new_store.return_value = self.store
                self.click(dialog.further_details_button)

        args, kwargs = run_dialog.call_args
        editor, d, store, model = args
        self.assertEquals(editor, ClientEditor)
        self.assertEquals(d, dialog)
        self.assertEquals(model, dialog.model)
        self.assertTrue(isinstance(store, StoqlibStore))
        self.assertEquals(kwargs.pop('visual_mode'), True)
        self.assertEquals(kwargs, {})

    @mock.patch('stoqlib.gui.dialogs.clientdetails.run_dialog')
    @mock.patch('stoqlib.gui.dialogs.clientdetails.api.new_store')
    @mock.patch('stoqlib.gui.slaves.saleslave.return_sale')
    def test_tab_details(self, return_sale, new_store, run_dialog):
        new_store.return_value = self.store
        client = self.create_client()
        sale = self.create_sale(client=client)
        self.create_sale_item(sale, product=True)
        self.create_payment(payment_type=Payment.TYPE_IN, group=sale.group)
        sale.order()
        sale.confirm()

        sale2 = self.create_sale(client=client)
        item = self.create_sale_item(sale2, product=True)
        returned_sale = self.create_returned_sale(sale2)
        self.create_returned_sale_item(returned_sale, item)

        self.create_workorder(client=client)
        dialog = ClientDetailsDialog(self.store, client)

        # Test Sales tab details button
        sales_tab = dialog.details_notebook.get_nth_page(0)
        sales_tab.klist.select(sales_tab.klist[0])
        self.click(sales_tab.button_box.details_button)
        args, kwargs = run_dialog.call_args
        self.assertEquals(args[0], SaleDetailsDialog)
        self.assertTrue(isinstance(kwargs['model'], SaleView))

        # Test Sales tab return button
        sales_tab = dialog.details_notebook.get_nth_page(0)
        sales_tab.klist.select(sales_tab.klist[0])
        sale_view = sales_tab.klist[0]
        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.click(sales_tab.button_box.return_button)
                return_sale.assert_called_once_with(sales_tab.get_toplevel(),
                                                    sale_view.sale, self.store)

        # Test Returned Sales tab details button
        returned_sales_tab = dialog.details_notebook.get_nth_page(1)
        returned_sales_tab.klist.select(returned_sales_tab.klist[0])
        self.click(returned_sales_tab.button_box.details_button)
        args, kwargs = run_dialog.call_args
        self.assertEquals(args[0], SaleDetailsDialog)
        self.assertTrue(isinstance(kwargs['model'], SaleView))

        # Test Work Orders tab details button
        work_orders_tab = dialog.details_notebook.get_nth_page(4)
        work_orders_tab.klist.select(work_orders_tab.klist[0])
        self.click(work_orders_tab.button_box.details_button)
        args, kwargs = run_dialog.call_args
        self.assertEquals(args[0], WorkOrderEditor)
        self.assertTrue(isinstance(kwargs['model'], WorkOrder))

        # Test Payment tab details button
        payments_tab = dialog.details_notebook.get_nth_page(5)
        payments_tab.klist.select(payments_tab.klist[0])
        self.click(payments_tab.button_box.details_button)
        args, kwargs = run_dialog.call_args
        self.assertEquals(args[0], InPaymentEditor)
        self.assertTrue(isinstance(kwargs['model'], Payment))


if __name__ == '__main__':
    from stoqlib.api import api
    c = api.prepare_test()
    unittest.main()
