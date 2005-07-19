# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
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
gui/editors/individual_editor.py

    Base classes for individual editors
"""

from stoqlib.gui.editors import BaseEditorSlave
from stoqlib.gui.dialogs import run_dialog

from stoq.gui.editors.person_editor import PersonEditor
from stoq.lib.parameters import get_system_parameter
from stoq.lib.runtime import new_transaction
from stoq.domain.person import (CityLocation, 
                                PersonAdaptToIndividual,
                                Person)
from stoq.domain.interfaces import IIndividual


class IndividualDocuments(BaseEditorSlave):
    gladefile = 'IndividualDocuments'
    model_type = PersonAdaptToIndividual

    widgets = ('cpf',
               'rg_expedition_date',
               'rg_expedition_local',
               'rg_number')
    
    def __init__(self, parent):
        BaseEditorSlave.__init__(self, parent.conn, parent.model)

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.widgets)


class IndividualDetailsSlave(BaseEditorSlave):
    gladefile = 'IndividualDetailsSlave'
    model_type = PersonAdaptToIndividual

    proxy_widgets = ('birth_date',
                     'mother_name',
                     'father_name',
                     'occupation',
                     #'spouse', # XXX: depends on bug 2001 to work
                     'marital_status',
                     'gender')

    city_location_widgets = ('birth_loc_city',
                             'birth_loc_country',
                             'birth_loc_state')

    widgets = (proxy_widgets + city_location_widgets + 
               ('new_spouse_button', 'spouse_lbl', 'spouse'))
    
    def __init__(self, parent):
        BaseEditorSlave.__init__(self, parent.conn, parent.model)

    def setup_proxies(self):
        self.setup_combos()

        birthloc = self.model.birth_location
        if birthloc:
            birthloc = birthloc.clone()
        else:
            birthloc = CityLocation(connection=self.conn)
        self.model.birth_location = birthloc

        self.person_proxy = self.add_proxy(self.model, self.proxy_widgets)
        self.birthloc_proxy = self.add_proxy(birthloc, 
                                             self.city_location_widgets)

    def setup_combos(self):
        self.marital_status.connect('changed', self._marital_status_changed)
        
        genders = self.model.genders
        items = [(genders[i], i) for i in genders.keys()]
        self.gender.prefill(items, sort=True)

        self.marital_status.prefill(self.model.get_marital_statuses())

        cities = []
        sparam = get_system_parameter(self.conn)
        states = sparam.CITY_LOCATION_STATES
        countries = []

        for city_loc in CityLocation.select():
            if city_loc.city and city_loc.city not in cities:
                cities.append(city_loc.city)
            
            if city_loc.country and city_loc.country not in countries:
                countries.append(city_loc.country)

            if city_loc.state and city_loc.state not in states:
                states.append(city_loc.state)
        
        self.birth_loc_city.prefill(cities, sort=True)
        self.birth_loc_country.prefill(countries, sort=True)
        self.birth_loc_state.prefill(states, sort=True)

        # XXX: spouse combo won't be filled until we get the proper support. 
        # see bug #2001.
        self.spouse.clear()

    def _marital_status_changed(self, *args):
        visible = (self.marital_status.get_selected_data() == 
                   PersonAdaptToIndividual.STATUS_MARRIED) 

        self.new_spouse_button.set_property('visible', visible)
        self.spouse.set_property('visible', visible)
        self.spouse_lbl.set_property('visible', visible)
    
    def on_new_spouse_button__clicked(self, *args):
        #XXX: It is disabled on the glade file because we don't have 
        #CatalogCombo implemented yet. See bug #2001.
        spouse = run_dialog(IndividualEditor, None, self.conn)
        self.model.spouse = spouse or None

    def on_confirm(self):
        # Ensure the CityLocation doesn't exists in the table
        birth_location = self.model.birth_location

        query = ("city = '%s' AND state = '%s' AND country = '%s'" %
                 (birth_location.city, birth_location.state,
                  birth_location.country))

        conn = new_transaction()
        result = CityLocation.select(query, connection=conn)
        conn.close()

        if not birth_location.is_valid_model():
            self.model.birth_location = None
        elif result.count():
            msg = ("You should get just one city_location instance. "
                   "Probably you have a database inconsistency.")
            assert result.count() == 1, msg

            obj = CityLocation.get(result[0].id, 
                                          connection=self.conn)
            self.model.birth_location = obj
        else:
            return

        CityLocation.delete(birth_location.id, connection=self.conn)


class IndividualEditor(PersonEditor):
    title = _('Individual Editor')
    model_type = PersonAdaptToIndividual

    def __init__(self, conn, model=None):
        if not model:
            person_model = Person(name='', connection=conn)
            model = person_model.addFacet(IIndividual, connection=conn)

        PersonEditor.__init__(self, conn, model)

    def setup_slaves(self):
        PersonEditor.setup_slaves(self)

        slave = IndividualDocuments(self)
        self.attach_slave('person_id_holder', slave)

        self.individual_details = IndividualDetailsSlave(self)
        self.attach_slave('person_details_holder', self.individual_details)

    def on_confirm(self):
        self.individual_details.on_confirm()
        PersonEditor.on_confirm(self)
        return self.model


