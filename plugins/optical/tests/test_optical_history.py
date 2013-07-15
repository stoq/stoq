# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import mock

from stoq.gui.test.baseguitest import BaseGUITest
from stoqlib.lib.dateutils import localdate

from ..opticaldomain import OpticalPatientHistory
from ..opticalhistory import (OpticalPatientHistoryEditor,
                              OpticalPatientTestEditor,
                              OpticalPatientMeasuresEditor,
                              OpticalPatientVisualAcuityEditor,
                              OpticalPatientDetails)
from .test_optical_domain import OpticalDomainTest


class TestOpticalPatientEditors(BaseGUITest, OpticalDomainTest):

    def _generic_test(self, editor_class, uitest, create=None):
        client = self.create_client()
        model = None
        case = 'show'
        if create is not None:
            model = create(client)
            case = 'create'

        editor = editor_class(self.store, client, model)
        self.check_editor(editor, 'editor-optical-patient-%s-%s' % (uitest, case))
        return editor

    def test_optical_patient_history(self):
        # First we test creating a new model
        self._generic_test(OpticalPatientHistoryEditor, 'history')

        # Then we test using an existing model
        editor = self._generic_test(OpticalPatientHistoryEditor, 'history',
                                    self.create_optical_patient_history)

        editor.user_type.select(OpticalPatientHistory.TYPE_SECOND_USER)
        editor.user_type.select(OpticalPatientHistory.TYPE_EX_USER)
        editor.user_type.select(OpticalPatientHistory.TYPE_FIRST_USER)

    def test_optical_patient_test(self):
        # First we test creating a new model
        self._generic_test(OpticalPatientTestEditor, 'test')

        # Then we test using an existing model
        self._generic_test(OpticalPatientTestEditor, 'test',
                           self.create_optical_patient_tes)

    def test_optical_patient_measures(self):
        # First we test creating a new model
        self._generic_test(OpticalPatientMeasuresEditor, 'measures')

        # Then we test using an existing model
        self._generic_test(OpticalPatientMeasuresEditor, 'measures',
                           self.create_optical_patient_measures)

    def test_optical_patient_visual_acuity(self):
        # First we test creating a new model
        self._generic_test(OpticalPatientVisualAcuityEditor, 'visual-acuity')

        # Then we test using an existing model
        self._generic_test(OpticalPatientVisualAcuityEditor, 'visual-acuity',
                           self.create_optical_patient_visual_acuity)


class TestOpticalPatientDetails(BaseGUITest, OpticalDomainTest):

    def test_show(self):
        client = self.create_client()
        when = localdate(2012, 9, 1)

        # Create some data for the editor to display.
        history = self.create_optical_patient_history(client)
        history.create_date = when
        data = self.create_optical_patient_tes(client)
        data.create_date = when
        data = self.create_optical_patient_measures(client)
        data.create_date = when
        data = self.create_optical_patient_visual_acuity(client)
        data.create_date = when

        editor = OpticalPatientDetails(self.store, client)
        self.check_editor(editor, 'editor-optical-patient-details')

        slave = editor.slaves['history_holder']
        with mock.patch.object(slave, 'run_dialog') as run_dialog:
            slave.run_editor(self.store, history)
            run_dialog.assert_called_once_with(OpticalPatientHistoryEditor,
                                               store=self.store, client=client, model=history)
