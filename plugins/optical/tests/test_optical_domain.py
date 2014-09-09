# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from stoqlib.database.runtime import get_current_user
from stoqlib.domain.test.domaintest import DomainTest

from ..opticaldomain import (OpticalMedic, OpticalWorkOrder,
                             OpticalPatientHistory, OpticalPatientMeasures,
                             OpticalPatientTest, OpticalPatientVisualAcuity)


class OpticalDomainTest(DomainTest):
    def create_optical_medic(self, person=None, crm_number=None):
        person = person or self.create_person()
        person.name = u'Medic'
        return OpticalMedic(store=self.store,
                            crm_number=crm_number or u'1234',
                            person=person)

    def create_optical_work_order(self):
        work_order = self.create_workorder()
        return OpticalWorkOrder(store=self.store,
                                work_order=work_order)

    def create_optical_patient_history(self, client):
        return OpticalPatientHistory(store=self.store, client=client,
                                     responsible=get_current_user(self.store))

    # XXX: This is not a typo. If we include the word 'test' in the method
    # name, it will be considered a unit test
    def create_optical_patient_tes(self, client):
        return OpticalPatientTest(store=self.store, client=client,
                                  responsible=get_current_user(self.store))

    def create_optical_patient_measures(self, client):
        return OpticalPatientMeasures(store=self.store, client=client,
                                      responsible=get_current_user(self.store))

    def create_optical_patient_visual_acuity(self, client):
        return OpticalPatientVisualAcuity(store=self.store, client=client,
                                          responsible=get_current_user(self.store))


class OpticalMedicTest(OpticalDomainTest):
    def test_get_description(self):
        medic = self.create_optical_medic()
        assert medic.get_description() == u'Medic (upid: 1234)'

    def test_get_person_by_crm(self):
        new_person = self.create_person()
        crm = u'111'
        medic = self.create_optical_medic(person=new_person, crm_number=crm)
        person = medic.get_person_by_crm(self.store, crm)
        assert new_person == person

    def test_merge_with_medic(self):
        medic1 = self.create_optical_medic(crm_number=u'1')
        medic2 = self.create_optical_medic(crm_number=u'2')
        medic1.person.merge_with(medic2.person)

    def test_merge_with_client(self):
        medic = self.create_optical_medic(crm_number=u'333')
        client = self.create_client()
        medic.person.merge_with(client.person)
        self.assertEquals(client.person, medic.person)


class OpticalWorkOrderTest(OpticalDomainTest):
    def test_frame_type_str(self):
        opt_wo = self.create_optical_work_order()
        opt_wo.frame_type = OpticalWorkOrder.FRAME_TYPE_3_PIECES
        assert opt_wo.frame_type_str == 'Closed ring'
        opt_wo.frame_type = OpticalWorkOrder.FRAME_TYPE_NYLON
        assert opt_wo.frame_type_str == 'Nylon String'
        opt_wo.frame_type = OpticalWorkOrder.FRAME_TYPE_CLOSED_RING
        assert opt_wo.frame_type_str == '3 pieces'

    def test_lens_type_str(self):
        opt_wo = self.create_optical_work_order()
        opt_wo.lens_type = OpticalWorkOrder.LENS_TYPE_OPHTALMIC
        assert opt_wo.lens_type_str == 'Ophtalmic'
        opt_wo.lens_type = OpticalWorkOrder.LENS_TYPE_CONTACT
        assert opt_wo.lens_type_str == 'Contact'
