# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2008 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito  <evandro@async.com.br>
##              Johan Dahlin            <jdahlin@async.com.br>
##
##
""" Dialogs for payment method management"""

import gtk
from kiwi.ui.objectlist import ObjectList
from kiwi.ui.widgets.list import Column

from stoqlib.database.runtime import finish_transaction
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.gui.base.dialogs import BasicDialog, run_dialog
from stoqlib.gui.base.search import SearchEditorToolBar
from stoqlib.gui.editors.paymentmethodeditor import (PaymentMethodEditor,
                                                     CardPaymentMethodEditor)
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.message import warning

_ = stoqlib_gettext


class PaymentMethodsDialog(BasicDialog):
    # TODO Bug 2406 will avoid duplicating code here
    size = (400, 400)
    title = _("Payment Method Settings")

    def __init__(self, conn):
        BasicDialog.__init__(self)
        self._initialize(hide_footer=True, size=PaymentMethodsDialog.size,
                         title=PaymentMethodsDialog.title)
        self.conn = conn
        self._setup_list()
        self._setup_slaves()

    def _setup_slaves(self):
        self._toolbar_slave = SearchEditorToolBar()
        self._toolbar_slave.connect("edit", self._on_edit_button__clicked)
        self._toolbar_slave.new_button.hide()
        self._toolbar_slave.edit_button.set_sensitive(False)
        self.attach_slave("extra_holder", self._toolbar_slave)

    def _setup_list(self):
        methods = PaymentMethod.select(connection=self.conn)
        self.klist = ObjectList(self._get_columns(), methods,
                                gtk.SELECTION_BROWSE)
        self.klist.connect("selection-changed",
                           self._on_klist__selection_changed)
        self.klist.connect("row-activated", self._on_klist__row_activated)
        self.klist.connect("cell-edited", self.on_cell_edited)
        self.main.remove(self.main.get_child())
        self.main.add(self.klist)
        self.klist.show()

    def _get_columns(self):
        return [Column('description', title=_('Payment Method'), data_type=str,
                       expand=True, sorted=True),
                Column('is_active', title=_('Active'), data_type=bool,
                       editable_attribute='active_editable',
                       editable=True)]

    def _get_dialog(self, method):
        method_editors = {
            # Keep these around since the payment method is not
            # actually gone when migrating from old databases
            'giftcertificate': NotImplementedError,
            'finance': NotImplementedError,
            # TODO: implement editor for 'multiple' payment method.
            'multiple': NotImplementedError,
            'card': (CardPaymentMethodEditor, method),
            'money': (PaymentMethodEditor, method),
            'check': (PaymentMethodEditor, method),
            'bill': (PaymentMethodEditor, method),
            }
        dialog = method_editors.get(method.method_name)
        if dialog is None:
            raise TypeError(
                'Invalid payment method adapter: %s' % (
                method.method_name,))
        elif dialog is NotImplementedError:
            warning(_('Editor for %s is not implemented' % (
                method.method_name)))
            return None

        return dialog

    def _edit_item(self, item):
        dialog = self._get_dialog(item)
        if dialog is None:
            return
        dialog_args = [self, self.conn]
        if isinstance(dialog, tuple):
            dialog, model = dialog
            dialog_args.append(model)
        res = run_dialog(dialog, *dialog_args)
        finish_transaction(self.conn, res)

    #
    # Callbacks
    #

    def on_cell_edited(self, klist, obj, attr):
        conn = obj.get_connection()
        conn.commit()

    def _on_klist__selection_changed(self, list, data):
        self._toolbar_slave.edit_button.set_sensitive(data is not None)

    def _on_edit_button__clicked(self, toolbar_slave):
        self._edit_item(self.klist.get_selected())

    def _on_klist__row_activated(self, list, data):
        self._edit_item(data)
