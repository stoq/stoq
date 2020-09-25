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

import collections
import decimal

from kiwi.datatypes import ValidationError
from kiwi.ui.forms import (PriceField, DateField, TextField, BoolField,
                           IntegerField, ChoiceField, EmptyField, NumericField)
from kiwi.ui.objectlist import Column, ObjectList

from stoqlib.api import api
from stoqlib.domain.person import Client, Transporter, Person
from stoqlib.domain.sale import Delivery
from stoq.lib.gui.base.dialogs import run_dialog
from stoq.lib.gui.editors.baseeditor import BaseEditor
from stoq.lib.gui.editors.noteeditor import NoteEditor
from stoq.lib.gui.events import StockOperationPersonValidationEvent
from stoq.lib.gui.fields import AddressField, PersonField, PersonQueryField
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.formatters import format_quantity
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.validators import validate_vehicle_license_plate

_ = stoqlib_gettext


class CreateDeliveryModel(object):
    _savepoint_attr = ['price', 'notes', 'recipient', 'transporter_id', 'address',
                       'estimated_fix_date', 'freight_type', 'volumes_kind',
                       'volumes_quantity', 'volumes_gross_weight',
                       'volumes_net_weight', 'vehicle_license_plate',
                       'vehicle_state', 'vehicle_registration']

    def __init__(self, price=None, notes=None, recipient=None, transporter_id=None,
                 address=None, estimated_fix_date=None, description=None,
                 freight_type=None, volumes_kind=None, volumes_quantity=1,
                 volumes_gross_weight=decimal.Decimal(), vehicle_state=None,
                 vehicle_license_plate=None, vehicle_registration=None,
                 volumes_net_weight=decimal.Decimal(), original_delivery=None):
        self.price = price
        self.notes = notes
        self.address = address or (recipient and recipient.address)
        self.recipient = recipient or (address and address.person)
        self.transporter_id = transporter_id
        self.estimated_fix_date = estimated_fix_date or localtoday().date()
        self.description = description or _(u'Delivery')
        self.freight_type = freight_type or Delivery.FREIGHT_TYPE_CIF
        self.volumes_kind = volumes_kind or _(u'Volumes')
        self.volumes_quantity = volumes_quantity
        self.volumes_gross_weight = volumes_gross_weight
        self.volumes_net_weight = volumes_net_weight
        self.vehicle_license_plate = vehicle_license_plate
        self.vehicle_state = vehicle_state
        self.vehicle_registration = vehicle_registration
        self.original_delivery = original_delivery

        self._savepoint = {}

    @classmethod
    def from_delivery(cls, delivery):
        service_item = delivery.service_item
        return cls(
            price=service_item.price,
            notes=service_item.notes,
            transporter_id=delivery.transporter_id,
            address=delivery.address,
            estimated_fix_date=service_item.estimated_fix_date,
            freight_type=delivery.freight_type,
            volumes_kind=delivery.volumes_kind,
            volumes_quantity=delivery.volumes_quantity,
            volumes_gross_weight=delivery.volumes_gross_weight,
            volumes_net_weight=delivery.volumes_net_weight,
            vehicle_license_plate=delivery.vehicle_license_plate,
            vehicle_state=delivery.vehicle_state,
            vehicle_registration=delivery.vehicle_registration,
            original_delivery=delivery)

    # Since CreateDeliveryModel is not a Domain, changes to it can't be
    # undone by a store.rollback(). Therefore, we must make the rollback
    # by hand.

    def create_savepoint(self):
        for attr in self._savepoint_attr:
            self._savepoint[attr] = getattr(self, attr)

    def rollback_to_savepoint(self):
        if not self._savepoint:
            return

        for attr in self._savepoint_attr:
            setattr(self, attr, self._savepoint.get(attr))
        return self


class CreateDeliveryEditor(BaseEditor):
    """A fake delivery editor implementation.

    This is used to get get information for creating a delivery,
    without really creating a it.
    """

    model_name = _('Delivery')
    model_type = CreateDeliveryModel
    form_holder_name = 'forms'
    gladefile = 'CreateDeliveryEditor'
    title = _('New Delivery')
    form_columns = 2
    size = (750, 550)

    @cached_property()
    def fields(self):
        # Only users with admin or purchase permission can modify transporters
        user = api.get_current_user(self.store)
        can_modify_transporter = any((
            user.profile.check_app_permission(u'admin'),
            user.profile.check_app_permission(u'purchase'),
        ))
        freight_types = [(v, k) for k, v in Delivery.freights.items()]
        states = [(v, v) for v in api.get_l10n_field('state').state_list]

        return collections.OrderedDict(
            recipient=PersonQueryField(_("Recipient"), proxy=True, mandatory=True,
                                       person_type=self.person_type),
            transporter_id=PersonField(_("Transporter"), proxy=True,
                                       person_type=Transporter,
                                       can_add=can_modify_transporter,
                                       can_edit=can_modify_transporter),
            address=AddressField(_("Address"), proxy=True, mandatory=True),
            freight_type=ChoiceField(_("Freight type"), proxy=True,
                                     values=freight_types),
            price=PriceField(_("Delivery cost"), proxy=True),
            estimated_fix_date=DateField(_("Estimated delivery date"), proxy=True),
            volumes_kind=TextField(_("Volumes kind"), proxy=True),
            volumes_quantity=IntegerField(_("Volumes quantity"), proxy=True),
            volumes_net_weight=NumericField(_("Volumes net weight"), proxy=True,
                                            digits=3),
            volumes_gross_weight=NumericField(_("Volumes gross weight"),
                                              proxy=True, digits=3),
            vehicle_license_plate=TextField(_("Vehicle license plate"), proxy=True),
            vehicle_state=ChoiceField(_("Vehicle state"), proxy=True, use_entry=True,
                                      values=states),
            vehicle_registration=TextField(_("Vehicle registration"), proxy=True),
        )

    def __init__(self, store, model=None, items=None, person_type=Client):
        self.items = items
        self._deliver_items = []
        self.person_type = person_type

        if not model:
            for item in items:
                item.deliver = True
        else:
            model.create_savepoint()
            # Store this information for later rollback.
            for item in items:
                self._deliver_items.append(item.deliver)

        BaseEditor.__init__(self, store, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self.additional_info_label.set_size('small')
        self.additional_info_label.set_color('red')
        self.register_validate_function(self._validate_widgets)
        self.set_description(self.model_name)

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
        if run_dialog(NoteEditor, self, self.store, self.model, 'notes',
                      title=_('Delivery Instructions')):
            self._update_widgets()

    def on_estimated_fix_date__validate(self, widget, date):
        if date < localtoday().date():
            return ValidationError(_("Expected delivery date must "
                                     "be set to a future date"))

    def on_price__validate(self, widget, price):
        if price < 0:
            return ValidationError(
                _("The Delivery cost must be a positive value."))

    def on_vehicle_license_plate__validate(self, widget, value):
        # Do not validate if the widget is empty
        if not value:
            return

        if not validate_vehicle_license_plate(value):
            return ValidationError(_("Invalid License Plate"))

    def on_recipient__content_changed(self, entry):
        entry_value = entry.read()
        if entry_value is None:
            return

        if type(entry_value) is Person:
            person = entry_value
        else:
            person = entry_value.person
        self.fields['address'].set_from_person(person)

    def on_transporter_id__validate(self, widget, transporter_id):
        transporter = self.store.get(Transporter, transporter_id)
        return StockOperationPersonValidationEvent.emit(transporter.person, type(transporter))

    def on_recipient__validate(self, widget, recipient):
        if type(recipient) is Person:
            person = recipient
        else:
            person = recipient.person
        return StockOperationPersonValidationEvent.emit(person, type(recipient))

    def _on_items__cell_edited(self, items, item, attribute):
        self.force_validation()

    #
    # BaseEditor hooks
    #

    def create_model(self, store):
        price = sysparam.get_object(store, 'DELIVERY_SERVICE').sellable.price
        volumes_weight = decimal.Decimal()
        for item in self.items:
            product = item.sellable.product
            if product:
                volumes_weight += product.weight * item.quantity
        return CreateDeliveryModel(price=price, volumes_net_weight=volumes_weight,
                                   volumes_gross_weight=volumes_weight)

    def setup_slaves(self):
        self.items = ObjectList(columns=self._get_sale_items_columns(),
                                objects=self.items)
        self.items.connect('cell-edited', self._on_items__cell_edited)
        self.addition_list_holder.add(self.items)
        self.items.show()

    def on_cancel(self):
        # FIXME: When Kiwi allows choosing proxies to save upon confirm, apply
        # that here instead of making this rollback by hand. Bug 5415.
        self.model.rollback_to_savepoint()
        if self._deliver_items:
            for item, deliver in zip(self.items, self._deliver_items):
                item.deliver = deliver

    def on_confirm(self):
        estimated_fix_date = self.estimated_fix_date.read()
        for item in self.items:
            item.estimated_fix_date = estimated_fix_date


class DeliveryEditor(BaseEditor):
    """An editor for :class:`stoqlib.domain.sale.Delivery`"""

    title = _("Delivery editor")
    gladefile = 'DeliveryEditor'
    size = (700, 500)
    model_type = Delivery
    model_name = _('Delivery')
    form_holder_name = 'forms'
    form_columns = 2

    @cached_property()
    def fields(self):
        # Only users with admin or purchase permission can modify transporters
        user = api.get_current_user(self.store)
        can_modify_transporter = any((
            user.profile.check_app_permission(u'admin'),
            user.profile.check_app_permission(u'purchase'),
        ))
        freight_types = [(v, k) for k, v in Delivery.freights.items()]
        states = [(v, v) for v in api.get_l10n_field('state').state_list]

        return collections.OrderedDict(
            recipient_str=TextField(_("Recipient"), proxy=True, editable=False),
            transporter_id=PersonField(_("Transporter"), proxy=True,
                                       person_type=Transporter,
                                       can_add=can_modify_transporter,
                                       can_edit=can_modify_transporter),
            address=AddressField(_("Address"), proxy=True, mandatory=True),
            is_sent_check=BoolField(_("Was sent to deliver?")),
            send_date=DateField(_("Send date"), mandatory=True, proxy=True),
            tracking_code=TextField(_("Tracking code"), proxy=True),

            freight_type=ChoiceField(_("Freight type"), proxy=True,
                                     values=freight_types),
            volumes_kind=TextField(_("Volumes kind"), proxy=True),
            volumes_quantity=IntegerField(_("Volumes quantity"), proxy=True),
            volumes_net_weight=NumericField(_("Volumes net weight"), proxy=True,
                                            digits=3),
            volumes_gross_weight=NumericField(_("Volumes gross weight"),
                                              proxy=True, digits=3),
            vehicle_license_plate=TextField(_("Vehicle license plate"), proxy=True),
            vehicle_state=ChoiceField(_("Vehicle state"), proxy=True, use_entry=True,
                                      values=states),
            vehicle_registration=TextField(_("Vehicle registration"), proxy=True),
            is_received_check=BoolField(_("Was received by recipient?")),
            receive_date=DateField(_("Receive date"), mandatory=True, proxy=True),
            empty=EmptyField(),
        )

    def __init__(self, store, *args, **kwargs):
        self._configuring_proxies = False

        super(DeliveryEditor, self).__init__(store, *args, **kwargs)

    #
    #  BaseEditor Hooks
    #

    def setup_proxies(self):
        self._configuring_proxies = True
        self._setup_widgets()
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
        for widget in (self.receive_date, self.send_date,
                       self.tracking_code):
            widget.set_sensitive(False)

    def _update_status_widgets(self):
        if self.model.status == Delivery.STATUS_INITIAL:
            for widget in [self.is_sent_check, self.is_received_check]:
                widget.set_active(False)
        elif self.model.status == Delivery.STATUS_SENT:
            self.is_sent_check.set_active(True)
            self.is_received_check.set_active(False)
        elif self.model.status == Delivery.STATUS_RECEIVED:
            for widget in [self.is_sent_check, self.is_received_check]:
                widget.set_active(True)
        else:
            raise ValueError(_("Invalid status for %s") % (
                             self.model.__class__.__name__))

    def _get_delivery_items_columns(self):
        return [
            Column('sellable.description', title=_('Products to deliver'),
                   data_type=str, expand=True, sorted=True),
            Column('quantity', title=_('Quantity'), data_type=decimal.Decimal,
                   format_func=format_quantity),
        ]

    #
    #  Callbacks
    #

    def on_is_sent_check__toggled(self, button):
        active = button.get_active()
        # When delivered, don't let user change transporter or address
        self.transporter_id.set_sensitive(not active)
        self.address.set_sensitive(not active)
        for widget in [self.send_date, self.tracking_code]:
            widget.set_sensitive(active)

        if not self.model.send_date:
            self.send_date.update(localtoday().date())

        if self._configuring_proxies:
            # Do not change status above
            return

        if active:
            self.model.send(api.get_current_user(self.store))
        else:
            self.model.set_initial()

    def on_is_received_check__toggled(self, button):
        active = button.get_active()
        self.receive_date.set_sensitive(active)
        # If it was received, don't let the user unmark is_sent_check
        self.is_sent_check.set_sensitive(not active)

        if not self.is_sent_check.get_active():
            self.is_sent_check.set_active(True)

        if not self.model.receive_date:
            self.receive_date.update(localtoday().date())

        if self._configuring_proxies:
            # Do not change status above
            return

        if active:
            self.model.receive()
        else:
            # We have to change this status manually because set_sent won't
            # allow us to change from RECEIVED to it. Also, it we would call
            # set_sent it would overwrite the sent_date that we set previously
            self.model.status = self.model.STATUS_SENT
