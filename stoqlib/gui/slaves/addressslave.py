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
##  Author(s):      Daniel Saran R. da Cunha    <daniel@async.com.br>
##                  Henrique Romano             <henrique@async.com.br>
##                  Evandro Vale Miquelito      <evandro@async.com.br>
##
""" Address slave implementation"""


from kiwi.argcheck import argcheck

from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.lib.defaults import get_country_states
from stoqlib.lib.countries import get_countries
from stoqlib.domain.address import Address, CityLocation
from stoqlib.domain.person import Person


class AddressSlave(BaseEditorSlave):
    model_type = Address
    gladefile = 'AddressSlave'

    left_proxy = (
        'street',
        'complement',
        'postal_code',
        'state')

    left_widgets = (
        'address_lbl',
        'complement_lbl',
        'postal_code_lbl',
        'state_lbl'
        )

    proxy_widgets = (
        'number',
        'district',
        'country',
        'city',
        ) + left_proxy


    @argcheck(object, Person, Address, bool, bool)
    def __init__(self, conn, person, model=None, is_main_address=True,
                 visual_mode=False):
        self.person = person
        self.is_main_address = (model and model.is_main_address
                                or is_main_address)
        BaseEditorSlave.__init__(self, conn, model, visual_mode=visual_mode)

    def get_left_widgets(self):
        return [getattr(self, name)
                    for name in (AddressSlave.left_proxy +
                                 AddressSlave.left_widgets)]

    def create_model(self, conn):
        city_loc = CityLocation.get_default(conn)
        return Address(person=self.person, city_location=city_loc,
                       is_main_address=self.is_main_address,
                       connection=conn)

    def set_model(self, model):
        """ Changes proxy model.  This method is used when this slave is
        attached as a container for the main address and the main address
        needs to be changed, so this slave must reflect the new address
        defined.
        """
        self.model.ensure_address()
        self.model = model
        self.proxy.set_model(self.model)

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        states = get_country_states()
        self.state.prefill(states)
        self.country.prefill(get_countries())
        self.proxy = self.add_proxy(self.model,
                                    AddressSlave.proxy_widgets)

    def can_confirm(self):
        return self.model.is_valid_model()

    def on_confirm(self):
        self.model.ensure_address()
        return self.model
