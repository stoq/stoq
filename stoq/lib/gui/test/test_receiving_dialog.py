# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012-2016 Async Open Source <http://www.async.com.br>
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

import mock

from stoq.lib.gui.dialogs.labeldialog import SkipLabelsEditor
from stoq.lib.gui.dialogs.receivingdialog import ReceivingOrderDetailsDialog
from stoq.lib.gui.test.uitestutils import GUITest
from stoq.lib.gui.wizards.stockdecreasewizard import StockDecreaseWizard


class TestReceivingDialog(GUITest):
    def test_show(self):
        order = self.create_receiving_order(
            invoice_key=u'43161103852995000107650010000001821299676414')
        self.create_receiving_order_item(receiving_order=order)
        dialog = ReceivingOrderDetailsDialog(self.store, order)
        dialog.invoice_slave.identifier.set_text('333')
        self.check_dialog(dialog, 'dialog-receiving-order-details-show')

    def test_show_without_invoice(self):
        order = self.create_receiving_order()
        order.receiving_invoice = None
        dialog = ReceivingOrderDetailsDialog(self.store, order)
        self.check_dialog(dialog, 'dialog-receiving-order-details-no-invoice')

    def test_show_package_product(self):
        package = self.create_product(description=u'Package', is_package=True)
        component = self.create_product(description=u'component', stock=2)
        self.create_product_component(product=package, component=component)
        purchase = self.create_purchase_order()

        parent = purchase.add_item(package.sellable)
        child = purchase.add_item(component.sellable, parent=parent)
        receiving = self.create_receiving_order(purchase_order=purchase)
        receiving_item = self.create_receiving_order_item(receiving_order=receiving,
                                                          purchase_item=parent,
                                                          quantity=1)
        self.create_receiving_order_item(receiving_order=receiving,
                                         purchase_item=child,
                                         quantity=1,
                                         parent_item=receiving_item)
        dialog = ReceivingOrderDetailsDialog(self.store, receiving)
        dialog.invoice_slave.identifier.set_text('333')
        self.check_dialog(dialog, 'dialog-receiving-order-package-details-show')

    @mock.patch('stoq.lib.gui.utils.printing.warning')
    @mock.patch('stoq.lib.gui.dialogs.receivingdialog.run_dialog')
    def test_print_labels(self, run_dialog, warning):
        order = self.create_receiving_order()
        self.create_receiving_order_item(receiving_order=order)
        dialog = ReceivingOrderDetailsDialog(self.store, order)

        self.click(dialog.print_labels)
        run_dialog.assert_called_once_with(SkipLabelsEditor, dialog, self.store)
        warning.assert_called_once_with('It was not possible to print the '
                                        'labels. The template file was not '
                                        'found.')

    @mock.patch('stoq.lib.gui.dialogs.receivingdialog.run_dialog')
    @mock.patch('stoq.lib.gui.dialogs.receivingdialog.api.new_store')
    def test_return_receiving(self, new_store, run_dialog):
        run_dialog.return_value = True
        new_store.return_value = self.store
        order = self.create_receiving_order()
        self.create_receiving_order_item(receiving_order=order)
        dialog = ReceivingOrderDetailsDialog(self.store, order)
        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.click(dialog.return_btn)
                run_dialog.assert_called_once_with(StockDecreaseWizard, dialog,
                                                   self.store, receiving_order=order)
