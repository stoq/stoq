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

from decimal import Decimal

from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.workorder import WorkOrder

from ..opticaldomain import (OpticalMedic, OpticalWorkOrder,
                             OpticalPatientHistory, OpticalPatientMeasures,
                             OpticalPatientTest, OpticalPatientVisualAcuity,
                             OpticalProduct, OpticalWorkOrderItemsView)
from ..opticalui import OpticalUI


class OpticalDomainTest(DomainTest):

    @classmethod
    def setUpClass(cls):
        cls.ui = OpticalUI.get_instance()
        super(OpticalDomainTest, cls).setUpClass()

    def create_optical_medic(self, person=None, crm_number=None):
        person = person or self.create_person()
        person.name = u'Medic'
        return OpticalMedic(store=self.store,
                            crm_number=crm_number or u'1234',
                            person=person)

    def create_optical_work_order(self, work_order=None):
        return OpticalWorkOrder(store=self.store,
                                work_order=work_order or self.create_workorder())

    def create_optical_patient_history(self, client):
        return OpticalPatientHistory(store=self.store, client=client,
                                     responsible=self.current_user)

    def create_optical_product(self, product=None, optical_type=None):
        if not product:
            product = self.create_product()
        return OpticalProduct(store=self.store,
                              product=product,
                              optical_type=optical_type)

    # XXX: This is not a typo. If we include the word 'test' in the method
    # name, it will be considered a unit test
    def create_optical_patient_tes(self, client):
        return OpticalPatientTest(store=self.store, client=client,
                                  responsible=self.current_user)

    def create_optical_patient_measures(self, client):
        return OpticalPatientMeasures(store=self.store, client=client,
                                      responsible=self.current_user)

    def create_optical_patient_visual_acuity(self, client):
        return OpticalPatientVisualAcuity(store=self.store, client=client,
                                          responsible=self.current_user)


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

    def test_merge_with_medic_no_crm(self):
        medic1 = self.create_optical_medic()
        medic1.crm_number = None
        medic2 = self.create_optical_medic(crm_number='2')
        medic1.person.merge_with(medic2.person)

    def test_merge_with_client(self):
        medic = self.create_optical_medic(crm_number=u'333')
        client = self.create_client()
        medic.person.merge_with(client.person)
        self.assertEqual(client.person, medic.person)


class OpticalWorkOrderTest(OpticalDomainTest):
    def test_find_by_work_order(self):
        work_order = self.create_workorder()
        optical_wo = self.create_optical_work_order(work_order=work_order)
        result = OpticalWorkOrder.find_by_work_order(work_order.store,
                                                     work_order)
        self.assertEquals(result, optical_wo)

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

    def test_can_create_purchase(self):
        sale = self.create_sale()
        wo = self.create_workorder()
        optical_wo = self.create_optical_work_order(work_order=wo)

        # wrong Status
        self.assertFalse(optical_wo.can_create_purchase())

        wo.approve(self.current_user)
        wo.work(self.current_branch, self.current_user)
        # its not coming from a sale
        self.assertFalse(optical_wo.can_create_purchase())

        wo.sale = sale
        optical_prod = self.create_optical_product(optical_type=OpticalProduct.TYPE_GLASS_LENSES)
        item = optical_wo.work_order.add_sellable(optical_prod.product.sellable)
        # There is 1 item to be purchased
        self.assertTrue(optical_wo.can_create_purchase())

        # There is a purchase
        purchase_item = self.create_purchase_order_item()
        item.purchase_item = purchase_item
        self.assertFalse(optical_wo.can_create_purchase())

    def test_create_purchase(self):
        sale = self.create_sale()
        supplier = self.create_supplier()
        optical_prod = self.create_optical_product(optical_type=OpticalProduct.TYPE_GLASS_LENSES)
        optical_prod2 = self.create_optical_product(optical_type=OpticalProduct.TYPE_GLASS_FRAME)
        optical_wo = self.create_optical_work_order()
        wo = optical_wo.work_order
        wo.sale = sale
        item1 = optical_wo.work_order.add_sellable(optical_prod.product.sellable)
        optical_wo.work_order.add_sellable(optical_prod2.product.sellable)
        wo.status = WorkOrder.STATUS_WORK_IN_PROGRESS

        purchase = optical_wo.create_purchase(supplier, item1, False, self.current_branch,
                                              self.current_station, self.current_user)
        for item in purchase.get_items():
            # Default cost
            self.assertEqual(item.cost, Decimal('125'))
            # This item should not be in the purchase
            self.assertNotEqual(item.sellable, optical_prod2.product.sellable)

    def test_create_purchase_with_supplier_info(self):
        sale = self.create_sale()
        supplier = self.create_supplier()
        optical_prod = self.create_optical_product(optical_type=OpticalProduct.TYPE_GLASS_LENSES)
        optical_prod.product.cost = Decimal('10')
        optical_prod2 = self.create_optical_product(optical_type=OpticalProduct.TYPE_GLASS_FRAME)
        optical_wo = self.create_optical_work_order()
        psi = self.create_product_supplier_info(supplier=supplier,
                                                product=optical_prod.product,
                                                branch=self.current_branch)
        psi.base_cost = Decimal('5')
        wo = optical_wo.work_order
        wo.sale = sale
        item1 = optical_wo.work_order.add_sellable(optical_prod.product.sellable)
        optical_wo.work_order.add_sellable(optical_prod2.product.sellable)
        wo.status = WorkOrder.STATUS_WORK_IN_PROGRESS

        purchase = optical_wo.create_purchase(supplier, item1, False, self.current_branch,
                                              self.current_station, self.current_user)
        for item in purchase.get_items():
            self.assertEqual(item.cost, Decimal('5'))
            # This item should not be in the purchase
            self.assertNotEqual(item.sellable, optical_prod2.product.sellable)

    def test_can_receive_purchase(self):
        optical_wo = self.create_optical_work_order()
        wo = optical_wo.work_order
        purchase = self.create_purchase_order()
        purchase.status = PurchaseOrder.ORDER_PENDING

        # Wrong WorkOrder status
        self.assertFalse(optical_wo.can_receive_purchase(purchase))

        wo.approve(self.current_user)
        wo.work(self.current_branch, self.current_user)
        wo.finish(self.current_branch, self.current_user)
        # PurchaseOrder with wrong status
        self.assertFalse(optical_wo.can_receive_purchase(purchase))

        purchase.confirm(self.current_user)
        self.assertTrue(optical_wo.can_receive_purchase(purchase))

    def test_receive_purchase(self):
        optical_wo = self.create_optical_work_order()
        wo = optical_wo.work_order
        purchase = self.create_purchase_order()
        purchase.status = PurchaseOrder.ORDER_PENDING
        wo.approve(self.current_user)
        wo.work(self.current_branch, self.current_user)
        wo.finish(self.current_branch, self.current_user)
        purchase.confirm(self.current_user)
        optical_wo.receive_purchase(purchase, self.current_station, self.current_user)

        self.assertTrue(purchase.status, PurchaseOrder.ORDER_CLOSED)

    def test_reserve_products(self):
        supplier = self.create_supplier()
        optical_prod = self.create_optical_product(optical_type=OpticalProduct.TYPE_GLASS_LENSES)
        optical_prod2 = self.create_optical_product(optical_type=OpticalProduct.TYPE_GLASS_FRAME)
        sale = self.create_sale()
        sale_item1 = sale.add_sellable(optical_prod.product.sellable)
        sale_item2 = sale.add_sellable(optical_prod2.product.sellable)
        optical_wo = self.create_optical_work_order()
        wo = optical_wo.work_order
        wo.sale = sale
        wo_item1 = optical_wo.work_order.add_sellable(optical_prod.product.sellable)
        wo_item2 = optical_wo.work_order.add_sellable(optical_prod2.product.sellable)
        wo_item1.sale_item = sale_item1
        wo_item2.sale_item = sale_item2
        wo.status = WorkOrder.STATUS_WORK_IN_PROGRESS

        purchase = optical_wo.create_purchase(supplier, wo_item1, False, self.current_branch,
                                              self.current_station, self.current_user)
        optical_wo.reserve_products(purchase, self.current_user)


class TestOpticalWorkOrderItemsView(OpticalDomainTest):
    def test_find_by_order(self):
        wo = self.create_workorder()
        optical_wo = self.create_optical_work_order(work_order=wo)
        product = self.create_product()
        optical_product = self.create_optical_product(product=product)
        wo.add_sellable(product.sellable)

        views = OpticalWorkOrderItemsView.find_by_order(wo.store, wo)
        self.assertEquals(len(list(views)), 1)
        # We are adding only one product, so its safe to do this
        view = views[0]
        self.assertEquals(view.optical_product, optical_product)
        self.assertEquals(view.sellable, product.sellable)
        self.assertEquals(view.optical_work_order, optical_wo)
