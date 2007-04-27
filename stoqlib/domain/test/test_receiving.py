# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   Fabio Morbec      <fabio@async.com.br>
##

from kiwi.datatypes import currency

from stoqlib.database.exceptions import IntegrityError
from stoqlib.domain.test.domaintest import DomainTest
""" This module test all class in stoq/domain/receiving.py """

class TestReceivingOrder(DomainTest):

    def _testInvoiceNumber(self, value):
        order = self.create_receiving_order()
        try:
            order.invoice_number = value
        except IntegrityError, e:
            self.failUnless('valid_invoice_number' in e.pgerror)
        else:
            raise AssertionError

    def testInvoiceNumberLow(self):
        self._testInvoiceNumber(0)

    def testInvoiceNumberHigh(self):
        self._testInvoiceNumber(1000000)

    def testInvoiceNumberNegative(self):
        self._testInvoiceNumber(-1229)

    def testGetTotal(self):
        order = self.create_receiving_order()
        self.assertEqual(order.get_total(), currency(0))
        order.invoice_total = 400
        self.assertEqual(order.get_total(), currency(400))
        order.discount_value = 10
        order.purchase.discount_value = 5
        order.purchase.surcharge_value = 8
        order.surcharge_value = 15
        self.assertEqual(order.get_total(), currency(408))

    def testConfirm(self):
        order = self.create_receiving_order()
        order.quantity = 8
        order_item = self.create_receiving_order_item(order)
        order_item.quantity_received = 10
        self.assertRaises(ValueError, order.confirm)
        order_item.quantity_received = 8
        self.assertRaises(ValueError, order.confirm)
        self.assertRaises(ValueError, order.confirm)

class TestReceivingOrderItem(DomainTest):

    def testGetRemainingQuantity(self):
        order_item = self.create_receiving_order_item()
        self.assertEqual(order_item.get_remaining_quantity(), 5)
        self.assertNotEqual(order_item.get_remaining_quantity(), 4)
        self.assertNotEqual(order_item.get_remaining_quantity(), 8)
        self.assertNotEqual(order_item.get_remaining_quantity(), 18)
        self.assertNotEqual(order_item.get_remaining_quantity(), 0)

        order_item.purchase_item.quantity_received = 7
        self.assertEqual(order_item.get_remaining_quantity(), 1)
        self.assertNotEqual(order_item.get_remaining_quantity(), 5)
        self.assertNotEqual(order_item.get_remaining_quantity(), 8)

        order_item.purchase_item.quantity_received = 8
        self.assertEqual(order_item.get_remaining_quantity(), 0)
        self.assertNotEqual(order_item.get_remaining_quantity(), 1)
        self.assertNotEqual(order_item.get_remaining_quantity(), 8)

    def testGetPrice(self):
        order_item = self.create_receiving_order_item()
        order_item.sellable.cost = 100
        self.assertEqual(order_item.get_price(), currency(100))
        self.assertNotEqual(order_item.get_price(), currency(50))
        self.assertNotEqual(order_item.get_price(), currency(150))
