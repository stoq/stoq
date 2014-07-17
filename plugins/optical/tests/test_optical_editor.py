# -*- coding: utf-8 -*-
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

import decimal

import mock
from stoqlib.domain.person import Person
from stoqlib.gui.test.uitestutils import GUITest

from ..opticaldomain import OpticalMedic
from ..opticaleditor import MedicEditor, OpticalWorkOrderEditor
from .test_optical_domain import OpticalDomainTest


class TestMedicEditor(GUITest):

    def test_show(self):
        individual = self.create_individual()
        medic = OpticalMedic(person=individual.person, store=self.store)
        medic.crm_number = u'123456'

        editor = MedicEditor(self.store, model=medic)
        self.check_editor(editor, 'editor-medic-show')

    def test_create(self):
        editor = MedicEditor(self.store, role_type=Person.ROLE_COMPANY)
        self.check_editor(editor, 'editor-medic-create')


class TestOpticalWorkOrderEditor(GUITest, OpticalDomainTest):

    def test_show(self):
        optical_wo = self.create_optical_work_order()

        editor = OpticalWorkOrderEditor(self.store, optical_wo.work_order)
        self.check_editor(editor, 'editor-optical-work-order-show')

    @mock.patch('plugins.optical.opticaleditor.WorkOrderHistory.add_entry')
    def test_on_confirm(self, add_entry):
        optical_wo = self.create_optical_work_order()
        optical_wo.patient = u"Some patient"
        optical_wo.medic = self.create_optical_medic()
        editor = OpticalWorkOrderEditor(self.store, optical_wo.work_order)

        # No changes made, WorkOrderHistory should not be created
        self.click(editor.main_dialog.ok_button)
        self.assertEqual(add_entry.call_count, 0)
        add_entry.reset_mock()

        editor = OpticalWorkOrderEditor(self.store, optical_wo.work_order)
        editor.slave.re_distance_cylindrical.update(decimal.Decimal('0.25'))

        # Since we did a change, WorkOrderHistory should be created
        self.click(editor.main_dialog.ok_button)
        add_entry.assert_called_once_with(
            self.store, optical_wo.work_order, what=u"Optical details",
            notes=u"Optical details updated...")
