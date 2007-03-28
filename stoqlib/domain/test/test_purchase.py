# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Johan Dahlin      <jdahlin@async.com.br>
##              Fabio Morbec      <fabio@async.com.br>
##
""" This module test all class in stoq/domain/purchase.py """

from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.interfaces import IPaymentGroup

from stoqlib.domain.test.domaintest import DomainTest

class TestPurchaseOrder(DomainTest):
    def create_purchase_order(self):
        return PurchaseOrder(supplier=self.create_supplier(),
                             branch=self.create_branch(),
                             connection=self.trans)

    def testConfirmOrder(self):
        order = self.create_purchase_order()
        # FIXME: Use a better exception?
        self.assertRaises(ValueError, order.confirm_order)
        order.status = PurchaseOrder.ORDER_PENDING
        self.assertRaises(ValueError, order.confirm_order)

        order.addFacet(IPaymentGroup, connection=self.trans)
        order.confirm_order()

    def testClose(self):
        order = self.create_purchase_order()
        self.assertRaises(ValueError, order.close)
        order.status = PurchaseOrder.ORDER_PENDING
        self.assertRaises(ValueError, order.confirm_order)
        order.addFacet(IPaymentGroup, connection=self.trans)
        order.confirm_order()

        payments = list(IPaymentGroup(order).get_items())
        self.failUnless(len(payments) > 0)

        for payment in payments:
            self.assertEqual(payment.status, Payment.STATUS_PREVIEW)

        order.close()
        for payment in payments:
            self.assertEqual(payment.status, Payment.STATUS_PENDING)
