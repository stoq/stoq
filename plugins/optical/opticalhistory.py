# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

#
# Copyright (C) 2013 Async Open Source <http://www.async.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
# Author(s): Stoq Team <stoq-devel@async.com.br>
#
"""Client (patient) optical history"""

import datetime
import operator

from kiwi.enums import ListType
from kiwi.ui.objectlist import Column

from stoqlib.api import api
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.domain.person import Client
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.lists import ModelListSlave

from .opticaldomain import (OpticalPatientHistory,
                            OpticalPatientMeasures,
                            OpticalPatientTest,
                            OpticalPatientVisualAcuity)

_ = stoqlib_gettext


#
#   Editors
#

class OpticalPatientHistoryEditor(BaseEditor):
    translation_domain = 'stoq'
    domain = 'optical'
    gladefile = 'PatientHistory'
    # TRANSLATORS: Traduzir como 'Anamnese'
    title = _(u'Patient History')
    model_type = OpticalPatientHistory

    general_proxy_widgets = ['user_type', 'occupation', 'work_environment', 'history_notes']
    first_proxy_widgets = ['has_tested', 'tested_brand', 'eye_irritation',
                           'purpose_of_use', 'intended_hour_usage']
    second_proxy_widgets = ['s_previous_brand', 's_previous_feeling', 's_cornea_issues',
                            's_hours_per_day_usage', 'user_since', 'has_previous_lenses',
                            'previous_lenses_notes']
    ex_proxy_widgets = ['e_previous_brand', 'e_previous_feeling', 'e_cornea_issues',
                        'e_hours_per_day_usage', 'last_use', 'stop_reason', 'protein_removal',
                        'cleaning_product']
    adaptation_proxy_widgets = [
        'eye_injury', 'recent_pathology', 'using_eye_drops', 'health_problems',
        'using_medicament', 'family_health_problems', 'end_of_day_feeling',
        'adaptation_notes']

    def __init__(self, store, client, model=None, visual_mode=False):
        self._client = client
        if model:
            assert model.client == client
        BaseEditor.__init__(self, store, model, visual_mode)

    def create_model(self, store):
        return OpticalPatientHistory(store=store, client_id=self._client.id,
                                     responsible=api.get_current_user(store))

    def setup_proxies(self):
        self.type_proxy = None
        self._setup_widgets()
        self.add_proxy(self.model, self.general_proxy_widgets)
        self.add_proxy(self.model, self.adaptation_proxy_widgets)

        self.add_proxy(self.model, self.first_proxy_widgets)
        self.add_proxy(self.model, self.second_proxy_widgets)
        self.add_proxy(self.model, self.ex_proxy_widgets)

    def _setup_widgets(self):
        types = [(value, key) for key, value in self.model_type.user_types.items()]
        self.user_type.prefill(types)

    def on_user_type__changed(self, widget):
        user_type = self.model.user_type
        if user_type == OpticalPatientHistory.TYPE_FIRST_USER:
            self.first_box.show()
            self.second_box.hide()
            self.ex_box.hide()
        elif user_type == OpticalPatientHistory.TYPE_SECOND_USER:
            self.first_box.hide()
            self.second_box.show()
            self.ex_box.hide()
        elif user_type == OpticalPatientHistory.TYPE_EX_USER:
            self.first_box.hide()
            self.second_box.hide()
            self.ex_box.show()


class OpticalPatientMeasuresEditor(BaseEditor):
    translation_domain = 'stoq'
    domain = 'optical'
    gladefile = 'PatientMeasures'
    title = _(u'Measures')
    model_type = OpticalPatientMeasures
    # TODO: Dominant eye
    widgets = ['keratometer_horizontal', 'keratometer_vertical',
               'keratometer_axis', 'eyebrown', 'eyelash', 'conjunctiva', 'sclerotic',
               'iris_diameter', 'eyelid', 'eyelid_opening', 'cornea', 'tbut', 'schirmer']

    def __init__(self, store, client, model=None, visual_mode=False):
        if model:
            assert model.client == client
        self._client = client
        BaseEditor.__init__(self, store, model, visual_mode)

    def create_model(self, store):
        return OpticalPatientMeasures(client_id=self._client.id, store=store,
                                      responsible=api.get_current_user(store))

    def setup_proxies(self):
        options = [(value, key) for key, value in self.model_type.eye_options.items()]
        self.dominant_eye.prefill(sorted(options, key=operator.itemgetter(1)))

        widgets = ['notes', 'dominant_eye']
        for widget in self.widgets:
            widgets.extend(['le_' + widget, 're_' + widget])

        self.proxy = self.add_proxy(self.model, widgets)


class OpticalPatientTestEditor(BaseEditor):
    translation_domain = 'stoq'
    domain = 'optical'
    gladefile = 'PatientTest'
    title = _(u'Test')
    model_type = OpticalPatientTest
    widgets = ['item', 'brand', 'base_curve', 'spherical_degree', 'cylindrical',
               'axis', 'diameter', 'movement', 'centralization', 'spin',
               'fluorescein', 'over_refraction', 'bichrome', 'client_approved', 'delivered',
               'client_purchased']

    def __init__(self, store, client, model=None, visual_mode=False):
        if model:
            assert model.client == client
        self._client = client
        BaseEditor.__init__(self, store, model, visual_mode)

    def create_model(self, store):
        return OpticalPatientTest(client_id=self._client.id, store=store,
                                  responsible=api.get_current_user(store))

    def setup_proxies(self):
        widgets = []
        for widget in self.widgets:
            widgets.extend(['le_' + widget, 're_' + widget])

        self.proxy = self.add_proxy(self.model, widgets)


class OpticalPatientVisualAcuityEditor(BaseEditor):
    translation_domain = 'stoq'
    domain = 'optical'
    gladefile = 'PatientVisualAcuity'
    title = _(u'Visual Acuity')
    size = (-1, 350)
    model_type = OpticalPatientVisualAcuity
    proxy_widgets = ['be_distance_glasses', 'le_distance_glasses', 're_distance_glasses',
                     'be_distance_lenses', 'le_distance_lenses', 're_distance_lenses',
                     'be_near_glasses', 'be_near_lenses', 'notes']

    def __init__(self, store, client, model=None, visual_mode=False):
        if model:
            assert model.client == client
        self._client = client
        BaseEditor.__init__(self, store, model, visual_mode)

    def create_model(self, store):
        return OpticalPatientVisualAcuity(client_id=self._client.id, store=store,
                                          responsible=api.get_current_user(store))

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)


#
#   List Slaves
#

class _BaseListSlave(ModelListSlave):
    columns = [
        Column('create_date', _('Date'), data_type=datetime.date, sorted=True),
        Column('responsible_name', _('Responsible'), data_type=str, expand=True),
    ]

    def __init__(self, client, parent, store):
        self._client = client
        ModelListSlave.__init__(self, parent, store)
        self.set_list_type(ListType.UNREMOVABLE)

    def run_editor(self, store, model):
        client = store.fetch(self._client)
        return self.run_dialog(self.editor_class,
                               store=store, client=client, model=model)

    def populate(self):
        return self.store.find(self.model_type, client=self._client)


class OpticalPatientHistoryListSlave(_BaseListSlave):
    model_type = OpticalPatientHistory
    editor_class = OpticalPatientHistoryEditor


class OpticalPatientMeasuresListSlave(_BaseListSlave):
    model_type = OpticalPatientMeasures
    editor_class = OpticalPatientMeasuresEditor


class OpticalPatientTestListSlave(_BaseListSlave):
    model_type = OpticalPatientTest
    editor_class = OpticalPatientTestEditor


class OpticalPatientVisualAcuityListSlave(_BaseListSlave):
    model_type = OpticalPatientVisualAcuity
    editor_class = OpticalPatientVisualAcuityEditor


class OpticalPatientDetails(BaseEditor):
    model_type = Client
    size = (500, 300)
    translation_domain = 'stoq'
    domain = 'optical'
    gladefile = 'PatientHistoryDialog'

    list_slaves = [
        ('history_holder', OpticalPatientHistoryListSlave),
        ('measures_holder', OpticalPatientMeasuresListSlave),
        ('tests_holder', OpticalPatientTestListSlave),
        ('visual_acuity_holder', OpticalPatientVisualAcuityListSlave),
    ]

    def __init__(self, store, model, visual_mode=False):
        BaseEditor.__init__(self, store, model, visual_mode=False)
        self.set_description(self.model.person.name)

    def setup_slaves(self):
        self._slaves = {}
        for holder, klass in self.list_slaves:
            slave = klass(self.model, self, self.store)
            self.attach_slave(holder, slave)

    def setup_proxies(self):
        self.add_proxy(self.model, ['name'])


# Run this with one of the editors defined above
def test_editor(editor):  # pragma nocover
    from stoqlib.gui.base.dialogs import run_dialog
    ec = api.prepare_test()
    model = ec.store.find(editor.model_type).any()
    if not model:
        client = ec.store.find(Client).any()
        run_dialog(editor, None, ec.store, client)
    else:
        run_dialog(editor, None, ec.store, model.client, model)

    ec.store.commit()


def test_dialog():  # pragma nocover
    from stoqlib.gui.base.dialogs import run_dialog

    ec = api.prepare_test()
    client = ec.store.find(Client).any()
    run_dialog(OpticalPatientDetails, None, ec.store, client)
    ec.store.commit()

if __name__ == '__main__':  # pragma nocover
    #test_editor(OpticalPatientHistoryEditor)
    #test_editor(OpticalPatientMeasuresEditor)
    #test_editor(OpticalPatientTestEditor)
    #test_editor(OpticalPatientVisualAcuityEditor)
    test_dialog()
