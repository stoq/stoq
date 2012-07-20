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
import decimal

from kiwi.datatypes import ValidationError
from kiwi.ui.widgets.list import Column, ObjectList

from stoqlib.api import api
from stoqlib.domain.person import Client, Transporter
from stoqlib.domain.sale import Delivery
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.fields import AddressField, PersonField
from stoqlib.lib.formatters import format_quantity
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _CreateDeliveryModel(object):
    def __init__(self, price=None):
        self.price = price
        self.notes = None
        self.client = None
        self.transporter = None
        self.address = None
        self.estimated_fix_date = datetime.date.today()
        self.description = _('Delivery')


class CreateDeliveryEditor(BaseEditor):
    """A fake delivery editor implementation.

    This is used to get get information for creating a delivery,
    without really creating a it.
    """

    model_name = _('Delivery')
    model_type = object
    form_holder_name = 'forms'
    gladefile = 'CreateDeliveryEditor'
    title = _('New Delivery')
    size = (750, 550)

    proxy_widgets = [
        'client',
        'address',
        'estimated_fix_date',
        'price',
        'transporter',
        ]

    fields = dict(
        client=PersonField(_("Client"), proxy=True, mandatory=True,
                           person_type=Client),
        transporter=PersonField(_("Transporter"), proxy=True,
                                person_type=Transporter),
        address=AddressField(_("Address"), proxy=True, mandatory=True),
        )

    def __init__(self, conn, model=None, sale_items=None):
        if not model:
            for sale_item in sale_items:
                sale_item.deliver = True
        self.sale_items = sale_items

        BaseEditor.__init__(self, conn, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self.additional_info_label.set_size('small')
        self.additional_info_label.set_color('red')
        self.register_validate_function(self._validate_widgets)
        self.set_description(self.model_name)

        # Only users with admin or purchase permission can modify transporters
        user = api.get_current_user(self.conn)
        can_modify_transporter = any((
            user.profile.check_app_permission('admin'),
            user.profile.check_app_permission('purchase'),
            ))
        self.fields['transporter'].can_add = can_modify_transporter
        self.fields['transporter'].can_edit = can_modify_transporter

        self.fields['client'].person_type = Client

        self._update_widgets()

    def _validate_widgets(self, validation_value):
        if validation_value:
            validation_value = any(item.deliver for item in self.items)
        self.refresh_ok(validation_value)

    def _update_widgets(self):
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
                       data_type=decimal.Decimal, format_func=format_quantity),
                Column('deliver', title=_('Deliver'),
                       data_type=bool, editable=True)]

    #
    # Callbacks
    #

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
        if client:
            self.fields['address'].set_from_client(client)

    def _on_items__cell_edited(self, items, item, attribute):
        self.force_validation()

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        price = sysparam(self.conn).DELIVERY_SERVICE.sellable.price
        return _CreateDeliveryModel(price=price)

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model,
                                    CreateDeliveryEditor.proxy_widgets)

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


class DeliveryEditor(BaseEditor):
    """An editor for :class:`stoqlib.domain.sale.Delivery`"""

    title = _("Delivery editor")
    gladefile = 'DeliveryEditor'
    size = (600, 400)
    model_type = Delivery
    model_name = _('Delivery')
    form_holder_name = 'forms'

    proxy_widgets = [
        'address',
        'client_str',
        'deliver_date',
        'receive_date',
        'tracking_code',
        'transporter',
        ]

    fields = dict(
        transporter=PersonField(_("Transporter"), proxy=True,
                                person_type=Transporter),
        address=AddressField(_("Address"), proxy=True, mandatory=True)
        )

    def __init__(self, conn, *args, **kwargs):
        self._configuring_proxies = False
        #self.fields['transporter'].person_type = Transporter

        super(DeliveryEditor, self).__init__(conn, *args, **kwargs)

    #
    #  BaseEditor Hooks
    #

    def setup_proxies(self):
        self._configuring_proxies = True
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, DeliveryEditor.proxy_widgets)
        self._update_status_widgets()
        self._configuring_proxies = False

    def setup_slaves(self):
        self.delivery_items = ObjectList(
            columns=self._get_delivery_items_columns(),
            objects=self.model.delivery_items,
            )
        self.delivery_items_holder.add(self.delivery_items)
        self.delivery_items.show()

    #
    #  Private
    #

    def _setup_widgets(self):
        for widget in (self.receive_date, self.deliver_date,
                       self.tracking_code):
            widget.set_sensitive(False)

        # Only users with admin or purchase permission can modify transporters
        user = api.get_current_user(self.conn)
        can_modify_transporter = any((
            user.profile.check_app_permission('admin'),
            user.profile.check_app_permission('purchase'),
            ))
        self.fields['transporter'].can_add = can_modify_transporter
        self.fields['transporter'].can_edit = can_modify_transporter

    def _update_status_widgets(self):
        if self.model.status == Delivery.STATUS_INITIAL:
            for widget in (self.was_delivered_check, self.was_received_check):
                widget.set_active(False)
        elif self.model.status == Delivery.STATUS_SENT:
            self.was_delivered_check.set_active(True)
            self.was_received_check.set_active(False)
        elif self.model.status == Delivery.STATUS_RECEIVED:
            for widget in (self.was_delivered_check, self.was_received_check):
                widget.set_active(True)
        else:
            raise ValueError(_("Invalid status for %s" %
                               self.model.__class__.__name__))

    def _get_delivery_items_columns(self):
        return [
            Column('sellable', title=_('Products to deliver'), data_type=str,
                   expand=True, format_func=lambda s: s.get_description()),
            Column('quantity', title=_('Quantity'), data_type=decimal.Decimal,
                   format_func=format_quantity),
            ]

    #
    #  Callbacks
    #

    def on_was_delivered_check__toggled(self, button):
        active = button.get_active()
        # When delivered, don't let user change transporter
        self.transporter.set_sensitive(not active)
        for widget in (self.deliver_date, self.tracking_code):
            widget.set_sensitive(active)

        if not self.model.deliver_date:
            self.proxy.update('deliver_date', datetime.date.today())

        if self._configuring_proxies:
            # Do not change status above
            return

        if active:
            self.model.set_sent()
        else:
            self.model.set_initial()

    def on_was_received_check__toggled(self, button):
        active = button.get_active()
        self.receive_date.set_sensitive(active)
        for widget in (self.change_address_button,
                       # If it was received, don't let the user unmark
                       # was_delivered_check
                       self.was_delivered_check):
            widget.set_sensitive(not active)

        if not self.was_delivered_check.get_active():
            self.was_delivered_check.set_active(True)

        if not self.model.receive_date:
            self.proxy.update('receive_date', datetime.date.today())

        if self._configuring_proxies:
            # Do not change status above
            return

        if active:
            self.model.set_received()
        else:
            self.model.set_sent()
