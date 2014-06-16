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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Dialogs for payment method management"""

import gtk
from kiwi.ui.objectlist import ObjectList, Column

from stoqlib.api import api
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.gui.base.dialogs import BasicDialog, run_dialog
from stoqlib.gui.editors.paymentmethodeditor import (PaymentMethodEditor,
                                                     CardPaymentMethodEditor)
from stoqlib.gui.search.searcheditor import SearchEditorToolBar
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class PaymentMethodsDialog(BasicDialog):
    # TODO Bug 2406 will avoid duplicating code here
    size = (400, 400)
    title = _("Payment Method Settings")

    # TODO: implement editor for 'multiple' payment method.
    METHOD_EDITORS = {u'card': CardPaymentMethodEditor,
                      u'money': PaymentMethodEditor,
                      u'check': PaymentMethodEditor,
                      u'credit': PaymentMethodEditor,
                      u'bill': PaymentMethodEditor,
                      u'deposit': PaymentMethodEditor,
                      u'store_credit': PaymentMethodEditor}

    def __init__(self, store):
        BasicDialog.__init__(self,
                             hide_footer=True, size=PaymentMethodsDialog.size,
                             title=PaymentMethodsDialog.title)
        self._can_edit = False
        self.store = store
        self._setup_list()
        self._setup_slaves()

    def _setup_slaves(self):
        self._toolbar_slave = SearchEditorToolBar()
        self._toolbar_slave.connect("edit", self._on_edit_button__clicked)
        self._toolbar_slave.new_button.hide()
        self._toolbar_slave.edit_button.set_sensitive(False)
        self.attach_slave("extra_holder", self._toolbar_slave)

    def _setup_list(self):
        methods = PaymentMethod.get_editable_methods(self.store)
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
                       expand=True),
                Column('is_active', title=_('Active'), data_type=bool,
                       editable=True)]

    def _edit_item(self, item):
        editor = self.METHOD_EDITORS.get(item.method_name, None)

        if not editor:
            raise TypeError('Invalid payment method adapter: %s'
                            % item.method_name)

        store = api.new_store()
        item = store.fetch(item)
        retval = run_dialog(editor, self, store, item)
        store.confirm(retval)
        store.close()

    #
    # Callbacks
    #

    def on_cell_edited(self, klist, obj, attr):
        # All the payment methods could be (de)activate, except the 'money'
        # payment method.
        if obj.method_name != u'money':
            store = obj.store
            store.commit()
        else:
            obj.is_active = True

    def _on_klist__selection_changed(self, list, data):
        self._can_edit = (data and
                          data.method_name in self.METHOD_EDITORS.keys())
        self._toolbar_slave.edit_button.set_sensitive(self._can_edit)

    def _on_edit_button__clicked(self, toolbar_slave):
        assert self._can_edit
        self._edit_item(self.klist.get_selected())

    def _on_klist__row_activated(self, list, data):
        if not self._can_edit:
            return

        self._edit_item(data)
