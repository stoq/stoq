# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Daniel Saran R. da Cunha    <daniel@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##              Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
""" Person address editor implementation"""

from kiwi.ui.widgets.list import Column

from stoqlib.domain.address import Address, CityLocation
from stoqlib.domain.person import Person
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.lists import ModelListDialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.slaves.addressslave import AddressSlave

_ = stoqlib_gettext

class AddressEditor(BaseEditor):
    model_name = _('Address')
    model_type = Address
    gladefile = 'AddressEditor'

    proxy_widgets = ('is_main_address_checkbutton', )

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
        ct_location = CityLocation.get_default(conn)
        return Address(connection=self.conn, person=self.person,
                       city_location=ct_location)

    def setup_slaves(self):
        self.address_slave = AddressSlave(self.conn, self.person, self.model,
                                          False,
                                          visual_mode=self.visual_mode)
        self.proxy.set_model(self.address_slave.model)
        self.attach_slave('main_holder', self.address_slave)

    def setup_proxies(self):
        self.proxy = self.add_proxy(widgets=self.proxy_widgets)

    def on_confirm(self):
        if (self.model.is_main_address
            and self.model is not self.current_main_address):
            self.current_main_address.is_main_address = False
        return self.address_slave.on_confirm()

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

    def __init__(self, conn, person):
        self.person = person
        ModelListDialog.__init__(self, conn)

    def populate(self):
        return self.person.addresses

    def run_editor(self, trans, model):
        return run_dialog(
            AddressEditor, parent=self,
            conn=trans, person=trans.get(self.person), address=model)
