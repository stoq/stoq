# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012-2015 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import gtk
import mock

from stoqlib.api import api
from stoqlib.domain.person import Branch
from stoqlib.domain.transfer import TransferOrder
from stoqlib.gui.dialogs.transferorderdialog import TransferOrderDetailsDialog
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localdatetime


class TestTransferOrderDetailsDialog(GUITest):
    def test_show(self):
        transfer = self.create_transfer_order()
        self.create_transfer_order_item(order=transfer)

        dialog = TransferOrderDetailsDialog(self.store, transfer)
        self.check_dialog(dialog, 'dialog-transfer-order-details-show')

    def test_show_received(self):
        transfer = self.create_transfer_order()
        self.create_transfer_order_item(order=transfer)

        transfer.send()
        transfer.receive(self.create_employee())
        dialog = TransferOrderDetailsDialog(self.store, transfer)
        self.check_dialog(dialog, 'dialog-cancelled-order-details-show')

    @mock.patch('stoqlib.gui.dialogs.transferorderdialog.yesno')
    @mock.patch('stoqlib.gui.dialogs.transferorderdialog.print_report')
    def test_receive_order(self, print_report, yesno):
        yesno.retval = True

        source_branch = Branch.get_active_remote_branches(self.store)[0]
        dest_branch = api.get_current_branch(self.store)

        # Created and sent the order.
        order = self.create_transfer_order(source_branch=source_branch,
                                           dest_branch=dest_branch)
        self.create_transfer_order_item(order=order)
        order.identifier = 28474
        order.open_date = localdatetime(2012, 2, 2)
        order.send()

        dialog = TransferOrderDetailsDialog(self.store, order)
        self.click(dialog.print_button)
        print_report.assert_called_once_with(dialog.report_class, dialog.model)
        self.assertSensitive(dialog, ['receive_button'])
        with mock.patch.object(self.store, 'commit'):
            self.click(dialog.receive_button)

        yesno.assert_called_once_with(u'Receive the order?', gtk.RESPONSE_YES,
                                      u'Receive', u"Don't receive")

        self.assertEquals(order.status, order.STATUS_RECEIVED)
        self.assertEquals(order.cancel_date, None)

    @mock.patch('stoqlib.gui.dialogs.transferorderdialog.yesno')
    def test_cancel_order(self, yesno):
        dest_branch = Branch.get_active_remote_branches(self.store)[0]
        source_branch = api.get_current_branch(self.store)

        order = self.create_transfer_order(source_branch=source_branch,
                                           dest_branch=dest_branch)
        self.create_transfer_order_item(order=order)
        order.identifier = 28474
        order.open_date = localdatetime(2012, 2, 2)
        order.send()

        dialog = TransferOrderDetailsDialog(self.store, order)
        self.assertSensitive(dialog, ['cancel_button'])
        yesno.retval = True
        with mock.patch.object(self.store, 'commit'):
            self.click(dialog.cancel_button)
            yesno.assert_called_once_with(u'Cancel the order?', gtk.RESPONSE_YES,
                                          u'Cancel transfer', u"Don't cancel")
        self.assertEquals(order.status, TransferOrder.STATUS_CANCELLED)
        self.assertEquals(order.receival_date, None)

    def test_cancel_order_on_dest_branch(self):
        source_branch = Branch.get_active_remote_branches(self.store)[0]
        dest_branch = api.get_current_branch(self.store)

        order = self.create_transfer_order(source_branch=source_branch,
                                           dest_branch=dest_branch)
        self.create_transfer_order_item(order=order)
        order.identifier = 28474
        order.open_date = localdatetime(2012, 2, 2)
        order.send()

        dialog = TransferOrderDetailsDialog(self.store, order)
        # Destination branch should not cancel the transfer
        self.assertFalse(dialog.cancel_button.get_visible())
