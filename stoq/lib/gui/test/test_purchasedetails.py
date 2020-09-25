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

from stoqlib.domain.purchase import PurchaseOrder
from stoq.lib.gui.dialogs.labeldialog import SkipLabelsEditor
from stoq.lib.gui.dialogs.purchasedetails import PurchaseDetailsDialog
from stoq.lib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localdate
from stoqlib.reporting.purchase import (PurchaseOrderReport,
                                        PurchaseQuoteReport,
                                        PurchaseOrderItemReport)


class TestPurchaseDetailsDialog(GUITest):

    def test_show(self):
        date = localdate(2012, 1, 1).date()
        supplier = self.create_supplier()

        # New purchase
        order = self.create_purchase_order()
        order.identifier = 123
        order.supplier = supplier
        order.open_date = date

        # Product
        purchase_item = self.create_purchase_order_item(order)
        purchase_item.ipi_value = 80

        # New receiving
        receiving_order = self.create_receiving_order(purchase_order=order)
        self.create_receiving_order_item(receiving_order, purchase_item=purchase_item)

        # Payments
        payment = self.add_payments(order, date=date)[0]
        payment.identifier = 999
        payment.group.payer = supplier.person

        dialog = PurchaseDetailsDialog(self.store, order)
        self.check_editor(dialog, 'dialog-purchase-details')

    @mock.patch('stoq.lib.gui.dialogs.purchasedetails.SpreadSheetExporter.export')
    def test_export_spread_sheet(self, export):
        order = self.create_purchase_order()
        dialog = PurchaseDetailsDialog(self.store, order)

        self.click(dialog.export_csv)
        self.assertEqual(export.call_count, 1)

    @mock.patch('stoq.lib.gui.dialogs.purchasedetails.print_report')
    def test_print_details(self, print_report):
        order = self.create_purchase_order()
        dialog = PurchaseDetailsDialog(self.store, order)
        self.assertSensitive(dialog, ['print_button'])

        # Quote order
        self.click(dialog.print_button)
        print_report.assert_called_once_with(PurchaseQuoteReport, order)

        print_report.reset_mock()
        # # Normal order
        order.status = PurchaseOrder.ORDER_PENDING
        self.click(dialog.print_button)
        print_report.assert_called_once_with(PurchaseOrderReport, order)

    @mock.patch('stoq.lib.gui.dialogs.purchasedetails.print_report')
    def test_print_item(self, print_report):
        order = self.create_purchase_order()
        dialog = PurchaseDetailsDialog(self.store, order)
        self.assertSensitive(dialog, ['print_button'])

        order.status = PurchaseOrder.ORDER_PENDING
        self.click(dialog.print_button)
        print_report.assert_called_once_with(PurchaseOrderReport, order)

    @mock.patch('stoq.lib.gui.dialogs.purchasedetails.print_report')
    def test_print_details_simple(self, print_report):
        order = self.create_purchase_order()
        dialog = PurchaseDetailsDialog(self.store, order)
        self.assertSensitive(dialog, ['print_items_button'])

        order.status = PurchaseOrder.ORDER_PENDING
        self.click(dialog.print_items_button)
        print_report.assert_called_once_with(PurchaseOrderItemReport, order)

    @mock.patch('stoq.lib.gui.utils.printing.warning')
    @mock.patch('stoq.lib.gui.dialogs.purchasedetails.run_dialog')
    def test_print_labels(self, run_dialog, warning):
        order = self.create_purchase_order()
        dialog = PurchaseDetailsDialog(self.store, order)

        self.click(dialog.print_labels)
        run_dialog.assert_called_once_with(SkipLabelsEditor, dialog, self.store)
        warning.assert_called_once_with('It was not possible to print the '
                                        'labels. The template file was not '
                                        'found.')


if __name__ == '__main__':
    from stoqlib.api import api
    c = api.prepare_test()
    unittest.main()
