# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2008 Async Open Source <http://www.async.com.br>
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
##  Author(s):      Daniel Saran R. da Cunha    <daniel@async.com.br>
##                  Henrique Romano             <henrique@async.com.br>
##                  Evandro Vale Miquelito      <evandro@async.com.br>
##                  Johan Dahlin                <jdahlin@async.com.br>
##
""" Person address editor implementation"""

import gtk
from kiwi.argcheck import argcheck
from kiwi.datatypes import ValidationError
from kiwi.python import AttributeForwarder
from kiwi.ui.widgets.list import Column

from stoqlib.database.runtime import StoqlibTransaction
from stoqlib.domain.address import Address, CityLocation
from stoqlib.domain.person import Person
from stoqlib.gui.base.lists import ModelListDialog
from stoqlib.gui.editors.baseeditor import BaseEditor, BaseEditorSlave
from stoqlib.lib.countries import get_countries
from stoqlib.lib.defaults import get_country_states
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _AddressModel(AttributeForwarder):
    attributes = [
        'streetnumber',
        'district',
        'street',
        'complement',
        'postal_code',
        'is_main_address',
        'is_valid_model',
        'city_location',
        ]

    @argcheck(Address, StoqlibTransaction)
    def __init__(self, target, conn):
        AttributeForwarder.__init__(self, target)
        self.conn = conn
        self.city = target.city_location.city
        self.state = target.city_location.state
        self.country = target.city_location.country

    def _city_location_changed(self):
        return (self.city != self.city_location.city or
                self.state != self.city_location.state or
                self.country != self.city_location.country)

    def ensure_address(self):
        changed = self._city_location_changed()
        if changed:
            location = CityLocation.get_or_create(
                city=self.city,
                state=self.state,
                country=self.country,
                trans=self.conn)
            self.target.city_location = location


class AddressSlave(BaseEditorSlave):
    model_type = _AddressModel
    gladefile = 'AddressSlave'

    proxy_widgets = [
        'streetnumber',
        'district',
        'street',
        'complement',
        'postal_code',
        'streetnumber_check',
        ]

    location_widgets = [
        'city',
        'state',
        'country',
        ]

    @argcheck(object, Person, Address, bool, bool)
    def __init__(self, conn, person, model=None, is_main_address=True,
                 visual_mode=False):
        self.person = person
        self.is_main_address = (model and model.is_main_address
                                or is_main_address)
        if model is not None:
            model = conn.get(model)
            model = _AddressModel(model, conn)
        BaseEditorSlave.__init__(self, conn, model, visual_mode=visual_mode)

    def create_model(self, conn):
        address = Address(person=self.person,
                          city_location=CityLocation.get_default(conn),
                          is_main_address=self.is_main_address,
                          connection=conn)
        return _AddressModel(address, conn)

    def set_model(self, model):
        """ Changes proxy model.  This method is used when this slave is
        attached as a container for the main address and the main address
        needs to be changed, so this slave must reflect the new address
        defined.
        """
        self.model.ensure_address()
        self.model = model
        self.proxy.set_model(self.model)

    def confirm(self):
        self.model.ensure_address()
        return self.model.target

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self.state.prefill(get_country_states())
        self.country.prefill(get_countries())
        self.proxy = self.add_proxy(self.model,
                                    AddressSlave.proxy_widgets)

        has_street_number = self.model.streetnumber > 0
        # Enable if we already have a number or if we are adding a new address.
        self.streetnumber_check.set_active(has_street_number
                                           or not self.edit_mode)
        self._update_streetnumber()

        self.add_proxy(self.model, AddressSlave.location_widgets)

    def can_confirm(self):
        return self.model.is_valid_model()

    def _update_streetnumber(self):
        has_street_number = self.streetnumber_check.get_active()
        self.streetnumber.set_sensitive(has_street_number)
        if not has_street_number:
            self.model.streetnumber = None
            text = _(u"N/A")
        elif self.model.streetnumber:
           text = str(self.model.streetnumber)
        else:
            text = ''

        self.streetnumber.set_text(text)

    #
    # Kiwi callbacks
    #

    def on_streetnumber__validate(self, entry, streetnumber):
        if streetnumber <= 0:
            return ValidationError(_("Number cannot be zero or less than zero"))

    def on_streetnumber_check__clicked(self, check_button):
        self._update_streetnumber()


class AddressEditor(BaseEditor):
    model_name = _('Address')
    model_type = Address
    gladefile = 'AddressEditor'

    def __init__(self, conn, person, address=None):
        self.person = person
        if not isinstance(person, Person):
            raise TypeError("Invalid type for person argument. It should "
                            "be of type Person, got %s instead"
                            % type(person))
        self.current_main_address = self.person.get_main_address()

        BaseEditor.__init__(self, conn, address)
        self.set_description(self.model_name)

    #
    # BaseEditor Hooks
    #

    def create_model(self, conn):
        return Address(person=self.person,
                       city_location=CityLocation.get_default(conn),
                       is_main_address=False,
                       connection=conn)

    def setup_slaves(self):
        self.address_slave = AddressSlave(self.conn, self.person, self.model,
                                          is_main_address=False,
                                          visual_mode=self.visual_mode)
        self.attach_slave('main_holder', self.address_slave)

    def can_confirm(self):
        return self.model.is_valid_model()

    def on_confirm(self):
        return self.address_slave.confirm()


class AddressAdditionDialog(ModelListDialog):
    title = _('Additional Addresses')
    size = (600, 250)

    columns =  [
        Column('address_string', title=_('Address'),
               data_type=str, width=250, expand=True),
        Column('city', title=_('City'), width=100,
               data_type=str),
        Column('state', title=_('State'), data_type=str),
        ]

    model_type = Address

    def __init__(self, trans, person):
        self.person = person
        self.trans = trans
        ModelListDialog.__init__(self, trans)
        self.set_reuse_transaction(trans)

    def populate(self):
        # This is only additional addresses, eg non-main ones
        return Address.selectBy(
            person=self.person,
            is_main_address=False,
            connection=self.trans)

    def run_editor(self, trans, model):
        return self.run_dialog(AddressEditor,
            conn=trans, person=self.person, address=model)

class AddressSelectionDialog(ModelListDialog):
    title = _('Select an address')
    size = (600, 250)

    columns =  [
        Column('address_string', title=_('Address'),
               data_type=str, width=250, expand=True),
        Column('city', title=_('City'), width=100,
               data_type=str),
        Column('state', title=_('State'), data_type=str),
        ]

    model_type = Address

    def __init__(self, conn, person):
        self.person = person
        self.conn = conn
        ModelListDialog.__init__(self)

        # Remove the close button, we'll add it back shortly
        self.action_area.remove(self.action_area.get_children()[0])
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button(gtk.STOCK_APPLY, gtk.RESPONSE_CLOSE)
        self.listcontainer.list.connect('row-activated',
                                        self._on_listcontainer_row_activated)
        self.connect('response', self._on_dialog__response)

    def _on_dialog__response(self, dialog, response):
        if response == gtk.RESPONSE_CLOSE:
            self.retval = self.listcontainer.list.get_selected()

    def _on_listcontainer_row_activated(self, addresses, address):
        self.response(gtk.RESPONSE_CLOSE)

    def populate(self):
        return Address.selectBy(
            person=self.person,
            connection=self.conn)

    def run_editor(self, trans, model):
        return self.run_dialog(AddressEditor,
            conn=trans, person=self.person, address=model)
