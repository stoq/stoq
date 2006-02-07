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
## Author(s):   Daniel Saran R. da Cunha    <daniel@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##              Evandro Vale Miquelito      <evandro@async.com.br>
##
"""
stoq/gui/slaves/individual.py

    Individual edition template slaves implementation.
"""


from stoqlib.gui.base.editors import BaseEditorSlave
from stoqlib.lib.defaults import get_country_states

from stoq.domain.person import CityLocation
from stoq.domain.interfaces import IIndividual
from stoq.lib.parameters import sysparam
from stoq.lib.runtime import new_transaction


class IndividualDocuments(BaseEditorSlave):
    model_iface = IIndividual
    gladefile = 'IndividualDocuments'
    proxy_widgets = ('cpf',
                     'rg_expedition_date',
                     'rg_expedition_local',
                     'rg_number')

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model,
                                    IndividualDocuments.proxy_widgets)

class IndividualDetailsSlave(BaseEditorSlave):
    model_iface = IIndividual
    gladefile = 'IndividualDetailsSlave'

    birth_loc_widgets = (
        'birth_loc_city',
        'birth_loc_country',
        'birth_loc_state'
        )

    proxy_widgets = (
        'birth_date',
        'mother_name',
        'father_name',
        'occupation',
        'spouse_name',
        'marital_status',
        )

    def setup_entries_completion(self):
        cities = [sysparam(self.conn).CITY_SUGGESTED]
        states = get_country_states()
        countries = [sysparam(self.conn).COUNTRY_SUGGESTED]

        for city_loc in CityLocation.select(connection=self.conn):
            if city_loc.city and city_loc.city not in cities:
                cities.append(city_loc.city)
            if city_loc.country and city_loc.country not in countries:
                countries.append(city_loc.country)
            if city_loc.state and city_loc.state not in states:
                states.append(city_loc.state)

        self.birth_loc_city.set_completion_strings(cities)
        self.birth_loc_country.set_completion_strings(countries)
        self.birth_loc_state.set_completion_strings(states)

    def _setup_widgets(self):
        is_male = self.model.gender == self.model_type.GENDER_MALE    
        is_female = self.model.gender == self.model_type.GENDER_FEMALE
        self.male_check.set_active(is_male)
        self.female_check.set_active(is_female)
        self.setup_entries_completion()
        self.marital_status.prefill(self.model.get_marital_statuses())

    def ensure_city_location(self):
        """ Search for the birth location fields in database, if found some
        item, reuse the city location object """
        birthloc = self.model.birth_location

        if not birthloc.is_valid_model():
            self.model.birth_location = None
            CityLocation.delete(birthloc.id, connection=self.conn)
            return

        query = ("city = '%s' and state = '%s' and country = '%s'"
                 % (birthloc.city, birthloc.state, birthloc.country))
        conn = new_transaction()
        result = CityLocation.select(query, connection=conn)
        conn.close()

        if not result.count():
            return

        msg = ("You should get just one city_location instance. Probably you "
               "have a database inconsistency.")
        assert result.count() == 1, msg

        self.model.birth_location = CityLocation.get(result[0].id)
        CityLocation.delete(birthloc.id, connection=self.conn)

    def update_marital_status(self):
        marital_status = self.marital_status.get_selected_data()
        visible = marital_status == self.model_type.STATUS_MARRIED
        if visible:
            self.spouse_lbl.show()
            self.spouse_name.show()
        else:
            self.spouse_lbl.hide()
            self.spouse_name.hide()    

    #
    # Kiwi handlers
    #

    def on_marital_status__changed(self, *args):
        self.update_marital_status()
       
    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    IndividualDetailsSlave.proxy_widgets)
        self.update_marital_status()
        if self.model.birth_location:
            self.model.birth_location = self.model.birth_location.clone()
        else:
            c = CityLocation(connection=self.conn)
            self.model.birth_location = c
        self.birth_loc_proxy = self.add_proxy(
            self.model.birth_location,
            IndividualDetailsSlave.birth_loc_widgets)

    def on_confirm(self):
        if self.male_check.get_active():
            self.model.gender = self.model_type.GENDER_MALE
        else:
            self.model.gender = self.model_type.GENDER_FEMALE
        self.ensure_city_location()
        return self.model
