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

from stoqlib.domain.test.domaintest import DomainTest

from ..opticaldomain import OpticalMedic, OpticalWorkOrder


class OpticalDomainTest(DomainTest):
    def create_optical_medic(self, crm_number=None):
        person = self.create_person()
        person.name = u'Medic'
        return OpticalMedic(store=self.store,
                            crm_number=crm_number or u'1234',
                            person=person)

    def create_optical_work_order(self):
        work_order = self.create_workorder()
        return OpticalWorkOrder(store=self.store,
                                work_order=work_order)


class OpticalMedicTest(OpticalDomainTest):
    def test_get_description(self):
        medic = self.create_optical_medic()
        assert medic.get_description() == u'Medic (upid: 1234)'


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
