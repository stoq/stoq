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


from sqlobject.sqlbuilder import AND, func

from stoqlib.database import finish_transaction
from stoqlib.gui.base.editors import BaseEditorSlave
from stoqlib.lib.defaults import get_country_states
from stoqlib.domain.person import CityLocation, Address
from stoqlib.lib.runtime import new_transaction
from stoqlib.lib.parameters import sysparam


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

    def __init__(self, conn, model=None, is_main_address=True):
        """ model: A Address object or nothing """
        self.is_main_address = (model and model.is_main_address
                                or is_main_address)
        if model and model.city_location is not None:
            model.city_location = model.city_location.clone()
        BaseEditorSlave.__init__(self, conn, model)

    def get_left_widgets(self):
        return [getattr(self, name)
                    for name in (AddressSlave.left_proxy +
                                 AddressSlave.left_widgets)]

    def create_model(self, conn):
        city = sysparam(conn).CITY_SUGGESTED
        state = sysparam(conn).STATE_SUGGESTED
        country = sysparam(conn).COUNTRY_SUGGESTED
        city_loc = CityLocation(connection=conn, city=city, country=country,
                                state=state)
        return Address(person=None, city_location=city_loc,
                       is_main_address=self.is_main_address,
                       connection=conn)

    def ensure_address(self):
        """ Check if we already have the city location specified by the
        user, if so reuse it. """
        cityloc = self.model.city_location

        if not cityloc.is_valid_model():
            self.model.city_location = None
            CityLocation.delete(cityloc.id, connection=self.conn)

        q1 = func.UPPER(CityLocation.q.city) == cityloc.city.upper()
        q2 = func.UPPER(CityLocation.q.state) == cityloc.state.upper()
        q3 = func.UPPER(CityLocation.q.country) == cityloc.country.upper()
        query = AND(q1, q2, q3)
        conn = new_transaction()
        result = CityLocation.select(query, connection=conn)

        if not result.count():
            return

        msg = ("You should get just one city_location instance. Probably you "
               "have a database inconsistency.")
        assert result.count() == 1, msg

        self.model.city_location = CityLocation.get(result[0].id)
        CityLocation.delete(cityloc.id, connection=self.conn)
        finish_transaction(conn)

    def set_model(self, model):
        """ Changes proxy model.  This method is used when this slave is
        attached as an container for the main address and the main address
        needs be changed, so this slave must reflect the new address
        defined.  """
        self.proxy.set_model(model)

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        states = get_country_states()
        self.state.prefill(states)
        self.proxy = self.add_proxy(self.model,
                                    AddressSlave.proxy_widgets)

    def can_confirm(self):
        return self.model.is_valid_model()

    def on_confirm(self):
        self.ensure_address()
        return self.model


