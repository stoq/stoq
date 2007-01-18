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
##
""" Individual edition template slaves implementation.  """


from stoqlib.gui.base.editors import BaseEditorSlave
from stoqlib.lib.defaults import get_country_states
from stoqlib.domain.address import CityLocation
from stoqlib.domain.interfaces import IIndividual


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

    general_widgets = (
        'birth_date',
        'mother_name',
        'father_name',
        'occupation',
        'spouse_name',
        'marital_status',
        )

    proxy_widgets = general_widgets + birth_loc_widgets

    def _setup_widgets(self):
        is_male = self.model.gender == self.model_type.GENDER_MALE
        is_female = self.model.gender == self.model_type.GENDER_FEMALE
        self.male_check.set_active(is_male)
        self.female_check.set_active(is_female)

        states = get_country_states()
        self.birth_loc_state.prefill(states)

        self.marital_status.prefill(self.model.get_marital_statuses())

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

    def update_visual_mode(self):
        self.male_check.set_sensitive(False)
        self.female_check.set_sensitive(False)

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    IndividualDetailsSlave.general_widgets)
        self.update_marital_status()
        if self.model.birth_location:
            self.model.birth_location = self.model.birth_location.clone()
        else:
            cityloc = CityLocation(connection=self.conn)
            self.model.birth_location = cityloc
        self.birth_loc_proxy = self.add_proxy(
            self.model.birth_location,
            IndividualDetailsSlave.birth_loc_widgets)

    def on_confirm(self):
        if self.male_check.get_active():
            self.model.gender = self.model_type.GENDER_MALE
        else:
            self.model.gender = self.model_type.GENDER_FEMALE
        self.model.ensure_birth_location()
        return self.model
