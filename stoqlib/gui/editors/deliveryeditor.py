# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
""" Product delivery editor implementation """

import datetime
from decimal import Decimal

from kiwi.datatypes import ValidationError
from kiwi.python import any
from kiwi.ui.widgets.list import Column, ObjectList

from stoqlib.api import api
from stoqlib.domain.person import ClientView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.addresseditor import AddressSelectionDialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.editors.personeditor import ClientEditor
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.lib.formatters import format_quantity
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class Delivery(object):
    def __init__(self, price=None):
        self.price = price
        self.estimated_fix_date = None
        self.notes = None
        self.client = None
        self.address = None
        self.description = _('Delivery')


class DeliveryEditor(BaseEditor):
    model_name = _('Delivery')
    model_type = object
    gladefile = 'DeliveryEditor'
    title = _('New Delivery')
    size = (700, 500)

    proxy_widgets = [
        'client',
        'delivery_address',
        'estimated_fix_date',
        'price'
        ]

    def __init__(self, conn, model=None, sale_items=None):
        self.sale_items = sale_items
        for sale_item in sale_items:
            sale_item.deliver = True
        self._can_edit_price = model is None
        BaseEditor.__init__(self, conn, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self.additional_info_label.set_size('small')
        self.additional_info_label.set_color('Red')
        self.register_validate_function(self._validate_widgets)
        self._update_widgets()
        self.price.set_sensitive(self._can_edit_price)
        self.set_description(self.model_name)

    def _validate_widgets(self, validation_value):
        if validation_value:
            validation_value = any(item.deliver for item in self.items)
        self.refresh_ok(validation_value)

    def _update_widgets(self):
        has_selected_client = bool(self.client.get_selected())
        self.refresh_ok(has_selected_client)
        if self.model.notes:
            self.additional_info_label.show()
        else:
            self.additional_info_label.hide()

    def _get_sale_items_columns(self):
        return [Column('code', title=_('Code'),
                       data_type=str),
                Column('description', title=_('Description'),
                       data_type=str, expand=True),
                Column('quantity', title=_('Quantity'),
                       data_type=Decimal, format_func=format_quantity),
                Column('deliver', title=_('Deliver'),
                       data_type=bool, editable=True)]

    def _show_address_editor(self):
        address = run_dialog(AddressSelectionDialog, self,
                             self.conn, self.model.client.person)
        if address:
            self._update_address(address)

    def _update_address(self, address):
        text = address.get_address_string()
        self.delivery_address.set_text(text)
        self.model.address = address

    def _create_client(self):
        trans = api.new_transaction()
        client = run_person_role_dialog(ClientEditor, self, trans, None)
        api.finish_transaction(trans, client)

        if client is not None:
            self._populate_person()
            self.client.select(client)

    def _populate_person(self):
        clients = ClientView.get_active_clients(self.conn)
        max_results = sysparam(self.conn).MAX_SEARCH_RESULTS
        clients = clients[:max_results]
        items = [(c.name, c.client) for c in clients]
        self.client.prefill(sorted(items))
        self.client.set_sensitive(len(items))

    #
    # Callbacks
    #

    def on_change_address_button__clicked(self, button):
        self._show_address_editor()

    def on_additional_info_button__clicked(self, button):
        if run_dialog(NoteEditor, self, self.conn, self.model, 'notes',
                      title=_('Delivery Instructions')):
            self._update_widgets()

    def on_estimated_fix_date__validate(self, widget, date):
        if date < datetime.date.today():
            return ValidationError(_("Expected delivery date must "
                 "be set to a future date"))

    def on_price__validate(self, widget, price):
        if price < 0:
            return ValidationError(
                _("The Delivery cost must be a positive value."))

    def on_client__content_changed(self, combo):
        client = combo.get_selected_data()
        self.change_address_button.set_sensitive(bool(client))
        if client:
            self._update_address(client.person.get_main_address())

    def on_create_client__clicked(self, button):
        self._create_client()

    def _on_items__cell_edited(self, items, item, attribute):
        self.force_validation()

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        price = sysparam(self.conn).DELIVERY_SERVICE.sellable.price
        return Delivery(price=price)

    def setup_proxies(self):
        self._populate_person()
        self.proxy = self.add_proxy(self.model, DeliveryEditor.proxy_widgets)
        if not self.model.client:
            self.change_address_button.set_sensitive(False)

    def setup_slaves(self):

        self.items = ObjectList(columns=self._get_sale_items_columns(),
                                objects=self.sale_items)
        self.items.connect('cell-edited', self._on_items__cell_edited)
        self.addition_list_holder.add(self.items)
        self.items.show()

    def on_cancel(self):
        for sale_item in self.sale_items:
            sale_item.deliver = False

    def on_confirm(self):
        for sale_item in self.sale_items:
            sale_item.estimated_fix_date = self.estimated_fix_date.read()

        return self.model
