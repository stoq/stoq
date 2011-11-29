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
""" Individual edition template slaves implementation.  """

import datetime

from kiwi.argcheck import argcheck
from kiwi.datatypes import ValidationError
from kiwi.python import AttributeForwarder

from stoqlib.database.runtime import StoqlibTransaction
from stoqlib.domain.address import CityLocation
from stoqlib.domain.interfaces import IIndividual
from stoqlib.domain.person import PersonAdaptToIndividual
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.lib.defaults import get_country_states
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.validators import validate_cpf

_ = stoqlib_gettext


class _IndividualDocuments(BaseEditorSlave):
    model_iface = IIndividual
    gladefile = 'IndividualDocuments'
    proxy_widgets = ('cpf',
                     'rg_expedition_date',
                     'rg_expedition_local',
                     'rg_number')

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model,
                                    _IndividualDocuments.proxy_widgets)

    def on_cpf__validate(self, widget, value):
        # This will allow the user to use an empty value to this field
        if self.cpf.is_empty():
            return

        if not validate_cpf(value):
            return ValidationError(_(u'The CPF is not valid.'))

        if self.model.check_cpf_exists(value):
            return ValidationError(_('A person with this CPF already exists'))


class _IndividualDetailsModel(AttributeForwarder):
    attributes = [
        'birth_date',
        'mother_name',
        'father_name',
        'occupation',
        'spouse_name',
        'marital_status',
        'get_marital_statuses',
        'birth_location',
        'gender'
        ]

    @argcheck(PersonAdaptToIndividual, StoqlibTransaction)
    def __init__(self, target, conn):
        AttributeForwarder.__init__(self, target)
        self.conn = conn
        if not target.birth_location:
            target.birth_location = CityLocation.get_default(conn)

        self.birth_city = target.birth_location.city
        self.birth_state = target.birth_location.state
        self.birth_country = target.birth_location.country

    def is_married(self):
        return (self.target.marital_statuses ==
                PersonAdaptToIndividual.STATUS_MARRIED)

    def is_male(self):
        return self.target.gender == PersonAdaptToIndividual.GENDER_MALE

    def is_female(self):
        return self.target.gender == PersonAdaptToIndividual.GENDER_FEMALE

    def birth_location_changed(self):
        return (self.birth_city != self.target.birth_location.city or
                self.birth_state != self.target.birth_location.state or
                self.birth_country != self.target.birth_location.country)

    def ensure_birth_location(self):
        changed = self.birth_location_changed()
        if changed:
            self.target.birth_location = CityLocation.get_or_create(
                city=self.birth_city,
                state=self.birth_state,
                country=self.birth_country,
                trans=self.conn)


class _IndividualDetailsSlave(BaseEditorSlave):
    model_type = _IndividualDetailsModel
    gladefile = 'IndividualDetailsSlave'

    proxy_widgets = [
        'birth_date',
        'mother_name',
        'father_name',
        'occupation',
        'spouse_name',
        'marital_status',
        'birth_city',
        'birth_country',
        'birth_state',
        ]

    def __init__(self, conn, model, visual_mode=False):
        BaseEditorSlave.__init__(self, conn, model, visual_mode=visual_mode)

    def _setup_widgets(self):
        self.male_check.set_active(self.model.is_male())
        self.female_check.set_active(self.model.is_female())
        self.marital_status.prefill(self.model.get_marital_statuses())
        self.birth_state.prefill(get_country_states())

    def _update_marital_status(self):
        if self.model.is_married():
            self.spouse_lbl.show()
            self.spouse_name.show()
        else:
            self.spouse_lbl.hide()
            self.spouse_name.hide()

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    _IndividualDetailsSlave.proxy_widgets)
        self._update_marital_status()

    def update_visual_mode(self):
        self.male_check.set_sensitive(False)
        self.female_check.set_sensitive(False)

    def on_confirm(self):
        if self.male_check.get_active():
            self.model.gender = PersonAdaptToIndividual.GENDER_MALE
        else:
            self.model.gender = PersonAdaptToIndividual.GENDER_FEMALE

        self.model.ensure_birth_location()
        return self.model

    #
    # Callbacks
    #

    def on_marital_status__changed(self, *args):
        self._update_marital_status()

    def on_birth_date__validate(self, widget, date):
        if date >= datetime.date.today():
            return ValidationError(_(u"Birth date must be less than today"))


class IndividualEditorTemplate(BaseEditorSlave):
    model_iface = IIndividual
    gladefile = 'BaseTemplate'

    def __init__(self, conn, model=None, person_slave=None,
                 visual_mode=False):
        """ Creates a new IndividualEditorTemplate object

        @param conn: a database connnection
        @param model: model
        @param person_slave: the person slave
        @param visual_model:
        """
        self._person_slave = person_slave
        BaseEditorSlave.__init__(self, conn, model, visual_mode=visual_mode)

    def get_person_slave(self):
        return self._person_slave

    def attach_person_slave(self, slave):
        self._person_slave.attach_slave('person_status_holder', slave)

    #
    # BaseEditorSlave hooks
    #

    def setup_slaves(self):
        self.model = self.conn.get(self.model)
        self.documents_slave = self._person_slave.attach_model_slave(
            'individual_holder', _IndividualDocuments, self.model)
        self.details_slave = self._person_slave.attach_model_slave(
            'details_holder', _IndividualDetailsSlave,
            _IndividualDetailsModel(self.model, self.conn))

    def on_confirm(self, confirm_person=True):
        self.details_slave.on_confirm()
        if confirm_person:
            self._person_slave.on_confirm()
        return self.model
