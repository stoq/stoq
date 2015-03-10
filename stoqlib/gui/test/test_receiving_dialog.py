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

import gtk
import mock

from stoqlib.domain.returnedsale import ReturnedSale
from stoqlib.domain.views import PendingReturnedSalesView
from stoqlib.gui.dialogs.labeldialog import SkipLabelsEditor
from stoqlib.gui.dialogs.receivingdialog import (ReceivingOrderDetailsDialog,
                                                 ReturnedSalesDialog)
from stoqlib.gui.test.uitestutils import GUITest


class TestReceivingDialog(GUITest):
    def test_show(self):
        order = self.create_receiving_order()
        self.create_receiving_order_item(receiving_order=order)
        dialog = ReceivingOrderDetailsDialog(self.store, order)
        dialog.invoice_slave.identifier.set_text('333')
        self.check_dialog(dialog, 'dialog-receiving-order-details-show')

    @mock.patch('stoqlib.gui.utils.printing.warning')
    @mock.patch('stoqlib.gui.dialogs.receivingdialog.run_dialog')
    def test_print_labels(self, run_dialog, warning):
        order = self.create_receiving_order()
        self.create_receiving_order_item(receiving_order=order)
        dialog = ReceivingOrderDetailsDialog(self.store, order)

        self.click(dialog.print_labels)
        run_dialog.assert_called_once_with(SkipLabelsEditor, dialog, self.store)
        warning.assert_called_once_with('It was not possible to print the '
                                        'labels. The template file was not '
                                        'found.')


class TestReturnedSalesDialog(GUITest):
    def test_show(self):
        pending_return = self.create_pending_returned_sale()
        pending_return.sale.identifier = 336
        pending_return.identifier = 60
        model = self.store.find(PendingReturnedSalesView).one()
        dialog = ReturnedSalesDialog(self.store, model)
        self.check_dialog(dialog, 'dialog-receive-pending-returned-sale')

    @mock.patch('stoqlib.gui.dialogs.receivingdialog.yesno')
    def test_receive_pending_returned_sale(self, yesno):
        self.create_pending_returned_sale()
        model = self.store.find(PendingReturnedSalesView).one()
        dialog = ReturnedSalesDialog(self.store, model)
        self.assertEquals(dialog.receive_button.get_property('visible'), True)
        self.assertEquals(model.returned_sale.status, ReturnedSale.STATUS_PENDING)
        with mock.patch.object(self.store, 'commit'):
            self.click(dialog.receive_button)
            yesno.assert_called_once_with(u'Receive pending returned sale?',
                                          gtk.RESPONSE_YES,
                                          u'Receive', u"Don't receive")
            self.assertEquals(model.returned_sale.status, ReturnedSale.STATUS_CONFIRMED)

    @mock.patch('stoqlib.gui.dialogs.receivingdialog.print_report')
    def test_print_button(self, print_report):
        self.create_pending_returned_sale()
        model = self.store.find(PendingReturnedSalesView).one()
        dialog = ReturnedSalesDialog(self.store, model)

        self.click(dialog.print_button)
        print_report.assert_called_once_with(dialog.report_class, dialog.model)
