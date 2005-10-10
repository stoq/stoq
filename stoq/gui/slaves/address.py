# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
"""
stoq/gui/slaves/address.py:

    Address slave implementation.
"""


from stoqlib.gui.editors import BaseEditorSlave

from stoq.domain.person import CityLocation, Address
from stoq.lib.runtime import new_transaction
from stoq.lib.defaults import get_country_states
from stoq.lib.parameters import sysparam


class AddressSlave(BaseEditorSlave):
    model_type = Address
    gladefile = 'AddressSlave'
    
    widgets = ('street',
               'number',
               'complement',
               'district',
               'postal_code',
               'country',
               'city',
               'state')

    def __init__(self, conn, model=None, is_main_address=True):
        """ model: A Address object or nothing """
        self.is_main_address = (model and model.is_main_address
                                or is_main_address)
        BaseEditorSlave.__init__(self, conn, model)

    def create_model(self, conn):
        # XXX: Waiting fix for bug #2043. We should create Address and
        # CityLocation objects not persistents.
        return Address(person=None, city_location=None,
                       is_main_address=self.is_main_address,
                       connection=conn)

    def setup_entries_completion(self):
        cities = [sysparam(self.conn).CITY_SUGGESTED]
        countries = [sysparam(self.conn).COUNTRY_SUGGESTED]
        states = get_country_states()

        # XXX: Maybe we can to do a "select distinct" and remove this loop
        for city_loc in CityLocation.select(connection=self.conn):
            if city_loc.city and city_loc.city not in cities:
                cities.append(city_loc.city)

            if city_loc.country and city_loc.country not in countries:
                countries.append(city_loc.country)

            if city_loc.state and city_loc.state not in states:
                states.append(city_loc.state)

        self.city.set_completion_strings(cities)
        self.country.set_completion_strings(countries)
        self.state.set_completion_strings(states)

    def ensure_address(self):
        """ Check if we already have the city location specified by the
        user, if so reuse it. """
        cityloc = self.model.city_location

        if not cityloc.is_valid_model():
            self.model.city_location = None
            CityLocation.delete(cityloc.id, connection=self.conn)

        query = ("city = '%s' and state = '%s' and country = '%s'"
                 % (cityloc.city, cityloc.state, cityloc.country))
        conn = new_transaction()
        result = CityLocation.select(query, connection=conn)
        conn.close()

        if not result.count():
            return

        msg = ("You should get just one city_location instance. Probably you "
               "have a database inconsistency.")
        assert result.count() == 1, msg

        self.model.city_location = CityLocation.get(result[0].id)
        CityLocation.delete(cityloc.id, connection=self.conn)

    def set_model(self, model):
        """ Changes proxy model.  This method is used when this slave is
        attached as an container for the main address and the main address
        needs be changed, so this slave must reflect the new address
        defined.  """
        self.proxy.new_model(model)

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self.setup_entries_completion()

        # XXX: Waiting fix for bug #2043. We should create Address and
        # CityLocation objects not persistents.
        if self.model.city_location is None:
            city_loc = CityLocation(connection=self.conn)
        else:
            city_loc = self.model.city_location.clone()
        self.model.city_location = city_loc

        self.proxy = self.add_proxy(self.model, self.widgets)

    def can_confirm(self):
        return self.model.is_valid_model()

    def on_confirm(self):
        self.ensure_address()
        return self.model


