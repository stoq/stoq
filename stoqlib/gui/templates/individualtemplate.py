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

from kiwi.datatypes import ValidationError
from kiwi.python import AttributeForwarder

from stoqlib.api import api
from stoqlib.domain.address import CityLocation
from stoqlib.domain.person import Individual
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.slaves.addressslave import CityLocationMixin
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _IndividualDocuments(BaseEditorSlave):
    model_type = Individual
    gladefile = 'IndividualDocuments'
    proxy_widgets = ('cpf',
                     'rg_expedition_date',
                     'rg_expedition_local',
                     'rg_number')

    def setup_proxies(self):
        self.document_l10n = api.get_l10n_field('person_document')
        self.cpf_lbl.set_label(self.document_l10n.label + ':')
        self.cpf.set_mask(self.document_l10n.entry_mask)
        self.proxy = self.add_proxy(self.model,
                                    _IndividualDocuments.proxy_widgets)

    def on_cpf__validate(self, widget, value):
        # This will allow the user to use an empty value to this field
        if self.cpf.is_empty():
            return

        if not self.document_l10n.validate(value):
            return ValidationError(_('%s is not valid.') % (
                self.document_l10n.label,))

        if self.model.check_cpf_exists(value):
            return ValidationError(_('A person with this %s already exists') % (
                self.document_l10n.label,))


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

    def __init__(self, target, store):
        """
        :param model: an Individial
        :param store: a store
        """
        AttributeForwarder.__init__(self, target)
        self.store = store
        if not target.birth_location:
            target.birth_location = CityLocation.get_default(store)

        self.city = target.birth_location.city
        self.state = target.birth_location.state
        self.country = target.birth_location.country

    def is_married(self):
        return (self.target.marital_statuses ==
                Individual.STATUS_MARRIED)

    def is_male(self):
        return self.target.gender == Individual.GENDER_MALE

    def is_female(self):
        return self.target.gender == Individual.GENDER_FEMALE

    def birth_location_changed(self):
        return (self.city != self.target.birth_location.city or
                self.state != self.target.birth_location.state or
                self.country != self.target.birth_location.country)

    def ensure_birth_location(self):
        changed = self.birth_location_changed()
        if changed:
            self.target.birth_location = CityLocation.get_or_create(
                city=self.city,
                state=self.state,
                country=self.country,
                store=self.store)


class _IndividualDetailsSlave(BaseEditorSlave, CityLocationMixin):
    model_type = _IndividualDetailsModel
    gladefile = 'IndividualDetailsSlave'

    proxy_widgets = [
        'birth_date',
        'mother_name',
        'father_name',
        'occupation',
        'spouse_name',
        'marital_status',
        'city',
        'country',
        'state',
    ]

    def _setup_widgets(self):
        self.male_check.set_active(self.model.is_male())
        self.female_check.set_active(self.model.is_female())
        self.marital_status.prefill(self.model.get_marital_statuses())

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
        CityLocationMixin.setup_proxies(self)

        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    _IndividualDetailsSlave.proxy_widgets)
        self._update_marital_status()

    def validate_confirm(self):
        return CityLocationMixin.validate_confirm(self)

    def update_visual_mode(self):
        self.male_check.set_sensitive(False)
        self.female_check.set_sensitive(False)

    def on_confirm(self):
        if self.male_check.get_active():
            self.model.gender = Individual.GENDER_MALE
        else:
            self.model.gender = Individual.GENDER_FEMALE

        self.model.ensure_birth_location()

    #
    # Callbacks
    #

    def on_marital_status__changed(self, *args):
        self._update_marital_status()

    def on_birth_date__validate(self, widget, date):
        if date > localtoday().date():
            return ValidationError(_(u"Birth date must be less than today"))


class IndividualEditorTemplate(BaseEditorSlave):
    model_type = Individual
    gladefile = 'BaseTemplate'

    def __init__(self, store, model=None, person_slave=None,
                 visual_mode=False):
        """ Creates a new IndividualEditorTemplate object

        :param store: a store
        :param model: model
        :param person_slave: the person slave
        :param visual_model:
        """
        self._person_slave = person_slave
        BaseEditorSlave.__init__(self, store, model, visual_mode=visual_mode)

    def get_person_slave(self):
        return self._person_slave

    def attach_person_slave(self, slave):
        self._person_slave.attach_slave('person_status_holder', slave)

    #
    # BaseEditorSlave hooks
    #

    def setup_slaves(self):
        self.model = self.store.fetch(self.model)
        self.documents_slave = self._person_slave.attach_model_slave(
            'individual_holder', _IndividualDocuments, self.model)
        self.details_slave = self._person_slave.attach_model_slave(
            'details_holder', _IndividualDetailsSlave,
            _IndividualDetailsModel(self.model, self.store))
