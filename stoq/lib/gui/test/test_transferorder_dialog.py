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

from gi.repository import Gtk
import mock

from kiwi.ui.forms import TextField

from stoqlib.api import api
from stoqlib.domain.person import Branch
from stoqlib.domain.transfer import TransferOrder
from stoq.lib.gui.dialogs.transferorderdialog import TransferOrderDetailsDialog
from stoq.lib.gui.editors.baseeditor import BaseEditorSlave
from stoq.lib.gui.editors.noteeditor import NoteEditor, Note
from stoq.lib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localdatetime
from stoqlib.lib.decorators import cached_property


class _TestSlave(BaseEditorSlave):
    model_type = object

    @cached_property()
    def fields(self):
        return dict(field_name=TextField('Slave field'))


class TestTransferOrderDetailsDialog(GUITest):
    def test_show(self):
        transfer = self.create_transfer_order()
        self.create_transfer_order_item(order=transfer)

        dialog = TransferOrderDetailsDialog(self.store, transfer)
        self.check_dialog(dialog, 'dialog-transfer-order-details-show')

    def test_show_received(self):
        transfer = self.create_transfer_order()
        self.create_transfer_order_item(order=transfer)

        transfer.send(self.current_user)
        transfer.receive(self.current_user, self.create_employee())
        dialog = TransferOrderDetailsDialog(self.store, transfer)
        self.check_dialog(dialog, 'dialog-cancelled-order-details-show')

    @mock.patch('stoq.lib.gui.dialogs.transferorderdialog.yesno')
    @mock.patch('stoq.lib.gui.dialogs.transferorderdialog.print_report')
    def test_receive_order(self, print_report, yesno):
        yesno.retval = True

        source_branch = Branch.get_active_remote_branches(self.store,
                                                          api.get_current_branch(self.store))[0]
        dest_branch = api.get_current_branch(self.store)

        # Created and sent the order.
        order = self.create_transfer_order(source_branch=source_branch,
                                           dest_branch=dest_branch)
        self.create_transfer_order_item(order=order)
        order.identifier = 28474
        order.open_date = localdatetime(2012, 2, 2)
        order.send(self.current_user)

        dialog = TransferOrderDetailsDialog(self.store, order)
        self.click(dialog.print_button)
        print_report.assert_called_once_with(dialog.report_class, dialog.model)
        self.assertSensitive(dialog, ['receive_button'])
        with mock.patch.object(self.store, 'commit'):
            self.click(dialog.receive_button)

        yesno.assert_called_once_with(u'Receive the order?', Gtk.ResponseType.YES,
                                      u'Receive', u"Don't receive")

        self.assertEqual(order.status, order.STATUS_RECEIVED)
        self.assertEqual(order.cancel_date, None)

    @mock.patch('stoq.lib.gui.dialogs.transferorderdialog.run_dialog')
    @mock.patch('stoq.lib.gui.dialogs.transferorderdialog.get_plugin_manager')
    def test_cancel_order_nfce_plugin_active(self, get_plugin_manager,
                                             run_dialog):
        dest_branch = Branch.get_active_remote_branches(self.store,
                                                        api.get_current_branch(self.store))[0]
        source_branch = api.get_current_branch(self.store)

        order = self.create_transfer_order(source_branch=source_branch,
                                           dest_branch=dest_branch)
        self.create_transfer_order_item(order=order)
        order.identifier = 28474
        order.open_date = localdatetime(2012, 2, 2)
        order.send(self.current_user)

        dialog = TransferOrderDetailsDialog(self.store, order)
        self.assertSensitive(dialog, ['cancel_button'])
        get_plugin_manager.is_active.return_value = True
        run_dialog.return_value = Note()
        with mock.patch.object(self.store, 'commit'):
            self.click(dialog.cancel_button)
            msg_text = u"This will cancel the transfer. Are you sure?"
            run_dialog.assert_called_once_with(
                NoteEditor, dialog, order.store, model=None,
                message_text=msg_text, label_text=u"Reason", mandatory=True,
                ok_button_label=u"Cancel transfer",
                cancel_button_label=u"Don't cancel",
                min_length=15)
        self.assertEqual(order.status, TransferOrder.STATUS_CANCELLED)
        self.assertEqual(order.receival_date, None)

    @mock.patch('stoq.lib.gui.dialogs.transferorderdialog.run_dialog')
    def test_dont_cancel_order(self, run_dialog):
        order = self.create_transfer_order()
        self.create_transfer_order_item(order=order)
        order.identifier = 28474
        order.open_date = localdatetime(2012, 2, 2)
        order.send(self.current_user)
        dialog = TransferOrderDetailsDialog(self.store, order)
        self.assertSensitive(dialog, ['cancel_button'])
        run_dialog.return_value = False
        with mock.patch.object(self.store, 'commit'):
            self.click(dialog.cancel_button)
        self.assertEqual(order.status, TransferOrder.STATUS_SENT)

    @mock.patch('stoq.lib.gui.dialogs.transferorderdialog.run_dialog')
    @mock.patch('stoq.lib.gui.dialogs.transferorderdialog.warning')
    def test_cancel_order_sefaz_rejected(self, warning, run_dialog):
        order = self.create_transfer_order()
        self.create_transfer_order_item(order=order)
        order.identifier = 28474
        order.open_date = localdatetime(2012, 2, 2)
        order.send(self.current_user)
        dialog = TransferOrderDetailsDialog(self.store, order)
        self.assertSensitive(dialog, ['cancel_button'])
        run_dialog.return_value = Note()
        module = 'stoqlib.domain.events.StockOperationTryFiscalCancelEvent.emit'
        with mock.patch(module) as emit:
            with mock.patch.object(self.store, 'commit'):
                emit.return_value = False
                self.click(dialog.cancel_button)
        self.assertEqual(order.status, TransferOrder.STATUS_SENT)
        warning.assert_called_once_with(
            "The cancellation was not authorized by SEFAZ. You should do a "
            "reverse transfer.")

    def test_cancel_order_on_dest_branch(self):
        source_branch = Branch.get_active_remote_branches(self.store,
                                                          api.get_current_branch(self.store))[0]
        dest_branch = api.get_current_branch(self.store)

        order = self.create_transfer_order(source_branch=source_branch,
                                           dest_branch=dest_branch)
        self.create_transfer_order_item(order=order)
        order.identifier = 28474
        order.open_date = localdatetime(2012, 2, 2)
        order.send(self.current_user)

        dialog = TransferOrderDetailsDialog(self.store, order)
        # Destination branch should not cancel the transfer
        self.assertFalse(dialog.cancel_button.get_visible())

    def test_add_tab(self):
        order = self.create_transfer_order()
        dialog = TransferOrderDetailsDialog(self.store, order)
        dialog.add_tab(_TestSlave(self.store, object()), u'Test Tab')
        self.check_dialog(dialog, 'dialog-transfer-order-add-tab')
