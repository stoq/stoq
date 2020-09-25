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

from decimal import Decimal

from gi.repository import Gdk
import mock

from stoq.lib.gui.editors.noteeditor import NoteEditor
from stoq.lib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localdate

from ..opticaldomain import OpticalWorkOrder
from ..opticalslave import MedicDetailsSlave, WorkOrderOpticalSlave
from .test_optical_domain import OpticalDomainTest


class MedicDetailsSlaveTest(GUITest, OpticalDomainTest):

    def test_create(self):
        medic = self.create_optical_medic()
        slave = MedicDetailsSlave(self.store, medic=medic)
        self.check_slave(slave, 'optical-medical-details-slave')

    def test_crm_number_validator(self):
        self.create_optical_medic(crm_number=u'1234')
        medic2 = self.create_optical_medic(crm_number=u'2223')
        slave = MedicDetailsSlave(self.store, medic=medic2)
        slave.crm_number.set_text('2222')
        self.assertValid(slave, ['crm_number'])
        slave.crm_number.set_text('1234')
        self.assertInvalid(slave, ['crm_number'])


class WorkOrderOpticalSlaveTest(GUITest, OpticalDomainTest):

    def test_show_optical_slave(self):
        workorder = self.create_workorder()
        slave = WorkOrderOpticalSlave(self.store, workorder)

        self.check_slave(slave, 'work-order-optical-slave')

    def test_visual_mode_optical_slave(self):
        workorder = self.create_workorder()
        slave = WorkOrderOpticalSlave(self.store, workorder, visual_mode=True)

        self.check_slave(slave, 'work-order-optical-slave-visual-mode')

    def test_focus_event(self):
        workorder = self.create_workorder()
        slave = WorkOrderOpticalSlave(self.store, workorder)

        e = Gdk.Event.new(type=Gdk.EventType.FOCUS_CHANGE)
        slave.le_near_pd.send_focus_change(e)

    def test_notes_button(self):
        workorder = self.create_workorder()
        slave = WorkOrderOpticalSlave(self.store, workorder, show_finish_date=True)
        name = 'plugins.optical.opticalslave.run_dialog'
        with mock.patch(name) as run_dialog:
            run_dialog.return_value = False
            self.click(slave.notes_button)
            self.assertEqual(run_dialog.call_count, 1)
            args, kwargs = run_dialog.call_args
            assert args[0] == NoteEditor
            assert args[3] == workorder
            assert args[4] == 'defect_reported'
            assert kwargs['title'] == 'Observations'

    def test_validate_field(self):
        workorder = self.create_workorder()
        slave = WorkOrderOpticalSlave(self.store, workorder)
        assert not slave.le_near_pd.emit("validate", 0)

        res = slave.le_near_pd.emit("validate", -100)
        assert str(res) == u'Value is out of range'

        res = slave.le_near_pd.emit("validate", Decimal("30.05"))
        assert str(res) == u'Value must be multiple of 0.1'

        for widget_name, minv, maxv, prec, step_inc, page_inc in [
            ('le_distance_spherical', -30, 30, 2, Decimal('0.25'), 1),
            ('re_distance_spherical', -30, 30, 2, Decimal('0.25'), 1),
            ('le_distance_cylindrical', -10, 10, 2, Decimal('0.25'), 1),
            ('re_distance_cylindrical', -10, 10, 2, Decimal('0.25'), 1),
            ('le_distance_axis', 0, 180, 0, 1, 10),
            ('re_distance_axis', 0, 180, 0, 1, 10),
            ('le_distance_pd', 22, 40, 1, Decimal('0.5'), 1),
            ('re_distance_pd', 22, 40, 1, Decimal('0.5'), 1),
            ('le_distance_prism', 0, 10, 2, Decimal('0.25'), 1),
            ('re_distance_prism', 0, 10, 2, Decimal('0.25'), 1),
            ('le_distance_base', 0, 10, 2, Decimal('0.25'), 1),
            ('re_distance_base', 0, 10, 2, Decimal('0.25'), 1),
            ('le_distance_height', 10, 40, 2, Decimal('0.5'), 1),
            ('re_distance_height', 10, 40, 2, Decimal('0.5'), 1),
            ('le_addition', 0, 4, 2, Decimal('0.25'), 1),
            ('re_addition', 0, 4, 2, Decimal('0.25'), 1),
            ('le_near_spherical', -30, 30, 2, Decimal('0.25'), 1),
            ('re_near_spherical', -30, 30, 2, Decimal('0.25'), 1),
            ('le_near_cylindrical', -10, 10, 2, Decimal('0.25'), 1),
            ('re_near_cylindrical', -10, 10, 2, Decimal('0.25'), 1),
            ('le_near_axis', 0, 180, 0, 1, 10),
            ('re_near_axis', 0, 180, 0, 1, 10),
            ('le_near_pd', 22, 40, 1, Decimal('0.1'), 1),
            ('re_near_pd', 22, 40, 1, Decimal('0.1'), 1),
        ]:
            widget = getattr(slave, widget_name)
            self.assertFalse(widget.emit("validate", 0))
            self.assertFalse(widget.emit("validate", minv))
            self.assertFalse(widget.emit("validate", minv + step_inc))
            self.assertFalse(widget.emit("validate", maxv))
            self.assertFalse(widget.emit("validate", maxv - 1))

            res = widget.emit("validate", maxv + step_inc)
            self.assertEqual(str(res), u'Value is out of range')

            res = widget.emit("validate", minv - step_inc)
            self.assertEqual(str(res), u'Value is out of range')

            res = widget.emit("validate", minv + (step_inc / Decimal("2.0")))
            self.assertEqual(str(res),
                             u'Value must be multiple of %s' % (step_inc, ))

    def test_validate_frame_field(self):
        workorder = self.create_workorder()
        slave = WorkOrderOpticalSlave(self.store, workorder)

        for widget_name, minv, maxv, prec, step_inc, page_inc in [
            ('frame_mva', 10, 70, 1, Decimal('0.1'), 1),
            ('frame_mha', 40, 80, 1, Decimal('0.1'), 1),
            ('frame_mda', 10, 65, 1, Decimal('0.1'), 1),
            ('frame_bridge', 5, 30, 1, Decimal('0.1'), 1),
        ]:
            widget = getattr(slave, widget_name)
            self.assertFalse(widget.emit("validate", 0))
            self.assertFalse(widget.emit("validate", minv))
            self.assertFalse(widget.emit("validate", minv + step_inc))
            self.assertFalse(widget.emit("validate", maxv))
            self.assertFalse(widget.emit("validate", maxv - 1))

            res = widget.emit("validate", maxv + step_inc)
            self.assertEqual(str(res), u'Value is out of range')

            res = widget.emit("validate", minv - step_inc)
            self.assertEqual(str(res), u'Value is out of range')

            res = widget.emit("validate", minv + (step_inc / 2))
            self.assertEqual(str(res),
                             u'Value must be multiple of %s' % (step_inc, ))

    def test_lens_types(self):
        workorder = self.create_workorder()
        slave = WorkOrderOpticalSlave(self.store, workorder)
        slave.lens_type.select(OpticalWorkOrder.LENS_TYPE_OPHTALMIC)
        self.check_slave(slave, 'work-order-optical-slave-lens-ophtalmic')
        slave.lens_type.select(OpticalWorkOrder.LENS_TYPE_CONTACT)
        self.check_slave(slave, 'work-order-optical-slave-lens-contact')

    @mock.patch('plugins.optical.opticalslave.localtoday')
    def test_prescription_date(self, localtoday_):
        localtoday_.return_value = localdate(2014, 1, 1)
        not_late_date = localdate(2013, 6, 1).date()
        late_date = localdate(2012, 1, 1).date()
        workorder = self.create_workorder()
        slave = WorkOrderOpticalSlave(self.store, workorder)
        slave.prescription_date.set_date(localdate(2014, 1, 1))
        slave.prescription_date.set_date(not_late_date)
        slave.prescription_date.set_date(late_date)
        slave.prescription_date.set_date(None)

    @mock.patch('plugins.optical.opticalslave.localtoday')
    def test_estimated_finish(self, localtoday_):
        workorder = self.create_workorder()
        workorder.open_date = localdate(2015, 4, 2)
        slave = WorkOrderOpticalSlave(self.store, workorder)
        #localtoday_.return_value = localdate(2014, 1, 1)
        res = slave.estimated_finish.emit("validate", localdate(2015, 4, 1))
        self.assertEqual(str(res),
                         u'Estimated finish date cannot be in the past.')
        # Can be edited without changing the estimated_finish
        res2 = slave.estimated_finish.emit("validate", localdate(2015, 4, 2))
        self.assertEqual(res2, None)

    def test_axis_value_changed(self):
        workorder = self.create_workorder()
        slave = WorkOrderOpticalSlave(self.store, workorder)

        # Left
        slave.le_near_axis.update(Decimal("1"))
        self.assertEqual(slave.le_distance_axis.get_value(), 0.0)
        slave.le_distance_axis.update(Decimal("2"))
        self.assertEqual(slave.le_near_axis.get_value(), 1.0)
        slave.model.le_addition = True
        slave.le_near_axis.update(Decimal("3.0"))
        self.assertEqual(slave.le_distance_axis.get_value(), 3.0)
        slave.le_distance_axis.update(Decimal("4.0"))
        self.assertEqual(slave.le_near_axis.get_value(), 4.0)

        # Right
        slave.re_near_axis.update(Decimal("1"))
        self.assertEqual(slave.re_distance_axis.get_value(), 0.0)
        slave.re_distance_axis.update(Decimal("2"))
        self.assertEqual(slave.re_near_axis.get_value(), 1.0)
        slave.model.re_addition = True
        slave.re_near_axis.update(Decimal("3.0"))
        self.assertEqual(slave.re_distance_axis.get_value(), 3.0)
        slave.re_distance_axis.update(Decimal("4.0"))
        self.assertEqual(slave.re_near_axis.get_value(), 4.0)

    def test_cylindrical_value_changed(self):
        workorder = self.create_workorder()
        slave = WorkOrderOpticalSlave(self.store, workorder)

        # Left
        slave.le_near_cylindrical.update(Decimal("1"))
        self.assertEqual(slave.le_distance_cylindrical.get_value(), 0.0)
        slave.le_distance_cylindrical.update(Decimal("2"))
        self.assertEqual(slave.le_near_cylindrical.get_value(), 1.0)
        slave.model.le_addition = Decimal("1.0")
        slave.le_near_cylindrical.update(Decimal("3.0"))
        self.assertEqual(slave.le_distance_cylindrical.get_value(), 3.0)
        slave.le_distance_cylindrical.update(Decimal("4.0"))
        self.assertEqual(slave.le_near_cylindrical.get_value(), 4.0)

        # Right
        slave.re_near_cylindrical.update(Decimal("1"))
        self.assertEqual(slave.re_distance_cylindrical.get_value(), 0.0)
        slave.re_distance_cylindrical.update(Decimal("2"))
        self.assertEqual(slave.re_near_cylindrical.get_value(), 1.0)
        slave.model.re_addition = Decimal("1.0")
        slave.re_near_cylindrical.update(Decimal("3.0"))
        self.assertEqual(slave.re_distance_cylindrical.get_value(), 3.0)
        slave.re_distance_cylindrical.update(Decimal("4.0"))
        self.assertEqual(slave.re_near_cylindrical.get_value(), 4.0)

    def test_spherical_value_changed(self):
        workorder = self.create_workorder()
        slave = WorkOrderOpticalSlave(self.store, workorder)

        # Left
        slave.le_near_spherical.update(Decimal("1"))
        self.assertEqual(slave.le_addition.get_value(), 1)

        slave.le_near_spherical.update(Decimal("0.25"))
        self.assertEqual(slave.le_addition.get_value(), 0.25)

        slave.le_near_spherical.update(Decimal("-0.25"))
        self.assertEqual(slave.le_addition.get_value(), 0)

        # Right
        slave.re_near_spherical.update(Decimal("1"))
        self.assertEqual(slave.re_addition.get_value(), 1)

        slave.re_near_spherical.update(Decimal("0.25"))
        self.assertEqual(slave.re_addition.get_value(), 0.25)

        slave.re_near_spherical.update(Decimal("-0.25"))
        self.assertEqual(slave.re_addition.get_value(), 0)

    def test_update(self):
        workorder = self.create_workorder()
        slave = WorkOrderOpticalSlave(self.store, workorder)

        slave.re_addition.update(Decimal("1"))
        self.assertEqual(slave.re_near_spherical.get_value(), Decimal("1.0"))
        slave.le_distance_spherical.update(Decimal("5.0"))
        slave.le_addition.update(Decimal("1.0"))
        self.assertEqual(slave.le_near_spherical.get_value(), Decimal("6.0"))
        slave.le_addition.update(Decimal("2.0"))
        self.assertEqual(slave.le_distance_spherical.get_value(), Decimal("5.0"))
        self.assertEqual(slave.le_near_spherical.get_value(), Decimal("7.0"))
        slave.le_distance_spherical.update(Decimal("1.0"))
        self.assertEqual(slave.le_near_spherical.get_value(), Decimal("3.0"))
        slave.le_near_spherical.update(Decimal("1.5"))
        self.assertEqual(slave.le_addition.get_value(), Decimal("0.5"))

        slave.le_addition.update(Decimal("0.0"))
        self.assertEqual(slave.le_distance_spherical.get_value(), Decimal("0.0"))

        slave.le_distance_spherical.update(Decimal("5.0"))
        slave.le_distance_cylindrical.update(Decimal("1.0"))
        slave.le_addition.update(Decimal("1.0"))
        self.assertEqual(slave.le_near_spherical.get_value(), Decimal("6.0"))
        self.assertEqual(slave.le_near_cylindrical.get_value(), Decimal("1.0"))

        slave.le_addition.update(Decimal("0.0"))
        self.assertEqual(slave.le_near_spherical.get_value(), Decimal("0.0"))

        self.assertEqual(slave.le_near_cylindrical.get_value(), Decimal("0.0"))

        # FIXME: Need many more tests

    def test_addition_changed(self):
        workorder = self.create_workorder()
        slave = WorkOrderOpticalSlave(self.store, workorder)

        self._test_addition_changed(slave.le_addition,
                                    slave.le_distance_axis,
                                    slave.le_distance_cylindrical,
                                    slave.le_near_axis,
                                    slave.le_near_cylindrical)
        self._test_addition_changed(slave.re_addition,
                                    slave.re_distance_axis,
                                    slave.re_distance_cylindrical,
                                    slave.re_near_axis,
                                    slave.re_near_cylindrical)

    def _test_addition_changed(self, addition,
                               distance_axis, distance_cylindrical,
                               near_axis, near_cylindrical):
        distance_cylindrical.update(Decimal("1.0"))
        addition.update(Decimal("1.0"))
        self.assertEqual(near_cylindrical.get_value(), Decimal("1.0"))
        addition.update(Decimal("0.0"))
        self.assertEqual(near_cylindrical.get_value(), Decimal("0.0"))

        near_cylindrical.update(Decimal("1.0"))
        addition.update(Decimal("1.0"))
        self.assertEqual(distance_cylindrical.get_value(), Decimal("1.0"))
        addition.update(Decimal("0.0"))

        # FIXME: Should be 1.0
        #self.assertEqual(distance_cylindrical.get_value(), Decimal("0.0"))

        distance_axis.update(Decimal("1.0"))
        addition.update(Decimal("1.0"))
        self.assertEqual(near_axis.get_value(), Decimal("1.0"))
        addition.update(Decimal("0.0"))
        self.assertEqual(near_axis.get_value(), Decimal("0.0"))

        near_axis.update(Decimal("1.0"))
        addition.update(Decimal("1.0"))
        self.assertEqual(distance_axis.get_value(), Decimal("1.0"))
        addition.update(Decimal("0.0"))
        # FIXME: Should be 1.0
        #self.assertEqual(distance_cylindrical.get_value(), Decimal("0.0"))

    def test_hide_description(self):
        with self.sysparam(CUSTOM_WORK_ORDER_DESCRIPTION=True):
            workorder = self.create_workorder()
            slave = WorkOrderOpticalSlave(self.store, workorder)
            self.assertTrue(slave.patient.get_visible())

        with self.sysparam(CUSTOM_WORK_ORDER_DESCRIPTION=False):
            workorder = self.create_workorder()
            slave = WorkOrderOpticalSlave(self.store, workorder)
            self.assertFalse(slave.patient.get_visible())

    def test_copy_wo(self):
        client = self.create_client()
        workorder = self.create_workorder(client=client)
        opt_wo = self.create_optical_work_order(work_order=workorder)
        opt_wo.le_distance_spherical = Decimal("1.25")
        opt_wo.re_distance_spherical = Decimal("1.50")

        slave = WorkOrderOpticalSlave(self.store, workorder)
        self.assertEqual(slave.le_distance_spherical.read(), Decimal("1.25"))
        self.assertEqual(slave.re_distance_spherical.read(), Decimal("1.50"))

    def test_copy_wo_without_client(self):
        workorder = self.create_workorder()
        workorder.client = None

        slave = WorkOrderOpticalSlave(self.store, workorder)
        # Since there is no client the slave should be without any information
        self.assertEqual(slave.le_distance_spherical.read(), Decimal("0"))
        self.assertEqual(slave.re_distance_spherical.read(), Decimal("0"))
