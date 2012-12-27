# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Person address editor implementation"""

from stoqlib.domain.address import Address, CityLocation
from stoqlib.domain.person import Person
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.slaves.addressslave import AddressSlave
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class AddressEditor(BaseEditor):
    model_name = _('Address')
    model_type = Address
    gladefile = 'AddressEditor'

    def __init__(self, store, person, address=None, visual_mode=False):
        self.person = store.fetch(person)
        if not isinstance(person, Person):
            raise TypeError("Invalid type for person argument. It should "
                            "be of type Person, got %s instead"
                            % type(person))
        self.current_main_address = self.person.get_main_address()

        BaseEditor.__init__(self, store, address, visual_mode=visual_mode)
        self.set_description(self.model_name)

    #
    # BaseEditor Hooks
    #

    def create_model(self, store):
        return Address(person=self.person,
                       city_location=CityLocation.get_default(store),
                       is_main_address=False,
                       store=store)

    def setup_slaves(self):
        self.address_slave = AddressSlave(self.store, self.person, self.model,
                                          is_main_address=False,
                                          visual_mode=self.visual_mode)
        self.attach_slave('main_holder', self.address_slave)

    def validate_confirm(self):
        return self.model.is_valid_model()
