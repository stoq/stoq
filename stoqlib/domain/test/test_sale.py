# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
## Author(s):     Lincoln Molica <lincoln@async.com.br>
##                Johan Dahlin <jdahlin@async.com.br>
##

import datetime
from decimal import Decimal

from kiwi.datatypes import currency
from sqlobject.sqlbuilder import AND
from stoqdrivers.enum import TaxType

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.commission import CommissionSource, Commission
from stoqlib.domain.fiscal import CfopData, FiscalBookEntry
from stoqlib.domain.interfaces import (IClient,
                                       IIndividual,
                                       IPaymentGroup,
                                       ISellable,
                                       IStorable,
                                       IOutPayment,
                                       IGiftCertificate)
from stoqlib.domain.person import Person
from stoqlib.domain.payment.group import AbstractPaymentGroup
from stoqlib.domain.payment.methods import CheckPM, MoneyPM
from stoqlib.domain.payment.payment import Payment, PaymentAdaptToOutPayment
from stoqlib.domain.sale import Sale
from stoqlib.domain.sellable import SellableTaxConstant
from stoqlib.domain.till import Till, TillEntry
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.parameters import sysparam

class TestSale(DomainTest):

    def _add_payments(self, sale, method_type=MoneyPM):
        group = IPaymentGroup(sale, None)
        if group is None:
            group = sale.addFacet(IPaymentGroup, connection=self.trans)

        method = method_type.selectOne(connection=self.trans)
        payment = method.create_inpayment(group,
                                          sale.get_sale_subtotal())

    def _add_product(self, sale, price=None):
        product = self.create_product(price=price)
        sellable = ISellable(product)
        sellable.tax_constant = SellableTaxConstant(
            description="18",
            tax_type=int(TaxType.CUSTOM),
            tax_value=18,
            connection=self.trans)
        sale.add_sellable(sellable, quantity=1)
        storable = product.addFacet(IStorable, connection=self.trans)
        storable.increase_stock(100, get_current_branch(self.trans))
        return sellable

    def _add_delivery(self, sale):
        sellable = sysparam(self.trans).DELIVERY_SERVICE
        sale.add_sellable(sellable, quantity=1)

    def testGetPercentageValue(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sale.add_sellable(sellable, quantity=5)

        self.assertEqual(sale._get_percentage_value(0), currency(0))
        self.assertEqual(sale._get_percentage_value(10), currency(5))

    def testSetDiscountByPercentage(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sale.add_sellable(sellable, quantity=5)

        sale._set_discount_by_percentage(10)
        self.assertEqual(sale.discount_value, currency(5))

    def testGetDiscountByPercentage(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sale.add_sellable(sellable, quantity=5)

        self.assertEqual(sale._get_discount_by_percentage(), Decimal('0.0'))
        sale._set_discount_by_percentage(10)
        self.assertEqual(sale._get_discount_by_percentage(), 10)

    def testSetSurchargeByPercentage(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sale.add_sellable(sellable, quantity=5)

        sale._set_surcharge_by_percentage(10)
        self.assertEqual(sale.surcharge_value, currency(5))

    def testGetSurchargeByPercentage(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sale.add_sellable(sellable, quantity=5)

        self.assertEqual(sale._get_surcharge_by_percentage(), currency(0))
        sale._set_surcharge_by_percentage(15)
        self.assertEqual(sale._get_surcharge_by_percentage(), 15)

    def testGetItems(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sale.add_sellable(sellable, quantity=5)

        items =  sale.get_items()
        self.assertEqual(items.count(), 1)
        self.assertEqual(sellable, items[0].sellable)

    def testRemoveItem(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sale.add_sellable(sellable, quantity=5)

        item = 'test purpose'
        self.failUnlessRaises(TypeError, sale.remove_item, item)
        item = sale.get_items()[0]
        sale.remove_item(item)
        self.assertEqual(sale.get_items().count(), 0)

    def test_get_status_name(self):
        sale = self.create_sale()
        self.failUnlessRaises(TypeError,
                              sale.get_status_name, 'invalid status')

    def test_add_custom_gift_certificate(self):
        sale = self.create_sale()
        self.failUnless(IGiftCertificate(
            sale.add_custom_gift_certificate(Decimal(230), u'11'), None))

    def test_get_clone(self):
        sale = self.create_sale()
        clone = sale.get_clone()
        self.assertEqual(clone.client, sale.client)
        self.assertEqual(clone.salesperson, sale.salesperson)

    def testCheckPaymentGroup(self):
        sale_no_payment = self.create_sale()

        sale = self.create_sale()
        sale.addFacet(IPaymentGroup, connection=self.trans)

        group = sale.check_payment_group()
        assert isinstance(group, Sale.getAdapterClass(IPaymentGroup))
        self.failIf(sale_no_payment.check_payment_group())

    def test_update_client(self):
        person = Person(name='Eliosvaldo', connection=self.trans)
        sale = self.create_sale()
        self.failUnlessRaises(TypeError, sale.update_client, person)
        individual = person.addFacet(IIndividual, connection=self.trans)
        client = person.addFacet(IClient, connection=self.trans)
        sale.update_client(person)
        self.assertEqual(sale.client, client)

    def test_reset_discount_and_surcharge(self):
        sale = self.create_sale()
        sale.reset_discount_and_surcharge()
        self.assertEqual(sale.discount_value, currency(0))
        self.assertEqual(sale.surcharge_value, currency(0))

    def testOrder(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sale.add_sellable(sellable, quantity=5)

        self.failUnless(sale.can_order())
        sale.order()
        self.failIf(sale.can_order())

    def testConfirmMoney(self):
        sale = self.create_sale()
        self._add_product(sale)
        sale.order()

        self._add_payments(sale, method_type=MoneyPM)
        group = IPaymentGroup(sale)
        self.failIf(FiscalBookEntry.selectOneBy(
            entry_type=FiscalBookEntry.TYPE_PRODUCT,
            payment_group=group,
            connection=self.trans))
        self.failUnless(sale.can_confirm())
        sale.confirm()
        self.failIf(sale.can_confirm())
        self.assertEqual(sale.status, Sale.STATUS_CONFIRMED)
        self.assertEqual(sale.confirm_date.date(), datetime.date.today())

        book_entry = FiscalBookEntry.selectOneBy(
            entry_type=FiscalBookEntry.TYPE_PRODUCT,
            payment_group=group,
            connection=self.trans)
        self.failUnless(book_entry)
        self.assertEqual(book_entry.cfop.code, '5.102')
        self.assertEqual(book_entry.icms_value, Decimal("1.8"))

        for payment in group.get_items():
            self.assertEquals(payment.status, Payment.STATUS_PAID)
            entry = TillEntry.selectOneBy(payment=payment, connection=self.trans)
            self.assertEquals(entry.value, payment.value)

    def testConfirmCheck(self):
        sale = self.create_sale()
        self._add_product(sale)
        sale.order()

        self._add_payments(sale, method_type=CheckPM)
        group = IPaymentGroup(sale)
        self.failIf(FiscalBookEntry.selectOneBy(
            entry_type=FiscalBookEntry.TYPE_PRODUCT,
            payment_group=group,
            connection=self.trans))
        self.failUnless(sale.can_confirm())
        sale.confirm()
        self.failIf(sale.can_confirm())
        self.assertEqual(sale.status, Sale.STATUS_CONFIRMED)
        self.assertEqual(sale.confirm_date.date(), datetime.date.today())

        book_entry = FiscalBookEntry.selectOneBy(
            entry_type=FiscalBookEntry.TYPE_PRODUCT,
            payment_group=group,
            connection=self.trans)
        self.failUnless(book_entry)
        self.assertEqual(book_entry.cfop.code, '5.102')
        self.assertEqual(book_entry.icms_value, Decimal("1.8"))

        for payment in group.get_items():
            self.assertEquals(payment.status, Payment.STATUS_PENDING)
            entry = TillEntry.selectOneBy(payment=payment, connection=self.trans)
            self.assertEquals(entry.value, payment.value)

    def testPay(self):
        sale = self.create_sale()
        self.failIf(sale.can_set_paid())

        self._add_product(sale)
        sale.order()
        self.failIf(sale.can_set_paid())

        self._add_payments(sale)
        sale.confirm()
        self.failUnless(sale.can_set_paid())

        sale.set_paid()
        self.failIf(sale.can_set_paid())
        self.failUnless(sale.close_date)
        self.assertEqual(sale.status, Sale.STATUS_PAID)
        self.assertEqual(sale.close_date.date(), datetime.date.today())

    def testReturn(self):
        sale = self.create_sale()
        self._add_product(sale)
        sale.order()
        self._add_payments(sale)
        sale.confirm()

        self.failUnless(sale.can_return())
        sale.return_(sale.create_sale_return_adapter())
        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())

    def testReturnPaid(self):
        sale = self.create_sale()
        self.failIf(sale.can_return())

        self._add_product(sale)
        sale.order()
        self.failIf(sale.can_return())

        self._add_payments(sale)
        sale.confirm()
        self.failUnless(sale.can_return())

        sale.set_paid()
        self.failUnless(sale.can_return())

        sale.return_(sale.create_sale_return_adapter())
        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())

        till = Till.get_current(self.trans)
        group = IPaymentGroup(sale)
        self.assertEqual(group.cancel_date.date(), datetime.date.today())
        self.assertEqual(group.status, AbstractPaymentGroup.STATUS_CANCELLED)
        paid_payment = group.get_items()[0]
        payment = Payment.selectOne(
            AND(Payment.q.groupID == group.id,
                Payment.q.tillID == till.id,
                Payment.q.id == PaymentAdaptToOutPayment.q._originalID),
            connection=self.trans)
        self.failUnless(payment)
        self.failUnless(IOutPayment(payment, None))
        self.assertEqual(payment.value, paid_payment.value)
        self.assertEqual(payment.status, Payment.STATUS_PAID)
        self.failUnless(isinstance(payment.method, MoneyPM))

        cfop = CfopData.selectOneBy(code='5.202', connection=self.trans)
        book_entry = FiscalBookEntry.selectOneBy(
            entry_type=FiscalBookEntry.TYPE_PRODUCT,
            payment_group=group,
            cfop=cfop,
            connection=self.trans)
        self.failUnless(book_entry)
        self.assertEqual(book_entry.icms_value,
                         Decimal("0.18") * paid_payment.value)

    def testCanCancel(self):
        sale = self.create_sale()
        self.failIf(sale.can_cancel())

        self._add_product(sale)
        sale.order()
        self.failUnless(sale.can_cancel())

        self._add_payments(sale)
        sale.confirm()
        self.failIf(sale.can_cancel())

        sale.set_paid()
        self.failIf(sale.can_cancel())

        sale.return_(sale.create_sale_return_adapter())
        self.failIf(sale.can_cancel())

    def testCancel(self):
        sale = self.create_sale()
        self._add_product(sale)
        sale.order()
        sale.cancel()
        self.assertEquals(sale.status, Sale.STATUS_CANCELLED)
        self.assertEquals(sale.cancel_date.date(), datetime.date.today())

    def testProducts(self):
        sale = self.create_sale()
        self.failIf(sale.products)

        service = self.create_service()
        sellable = ISellable(service)
        sale.add_sellable(sellable, quantity=1)

        self.failIf(sale.products)

        product = self.create_product()
        sellable = ISellable(product)
        sale.add_sellable(sellable, quantity=1)

        self.failUnless(sale.products)

    def testServices(self):
        sale = self.create_sale()
        self.failIf(sale.services)

        product = self.create_product()
        sellable = ISellable(product)
        sale.add_sellable(sellable, quantity=1)

        self.failIf(sale.services)

        service = self.create_service()
        sellable = ISellable(service)
        sale.add_sellable(sellable, quantity=1)

        self.failUnless(sale.services)

    def testSaleWithDelivery(self):
        sale = self.create_sale()
        self.failIf(sale.can_set_paid())

        self._add_product(sale)
        self._add_delivery(sale)
        sale.order()
        self.failIf(sale.can_set_paid())

        self._add_payments(sale)
        sale.confirm()

    def testCommissionAmount(self):
        sale = self.create_sale()
        sellable = self._add_product(sale, price=200)
        source = CommissionSource(asellable=sellable,
                                  direct_value=10,
                                  installments_value=5,
                                  connection=self.trans)
        sale.order()
        # payment method: money
        # installments number: 1
        self._add_payments(sale)
        self.failIf(Commission.selectBy(connection=self.trans))
        sale.confirm()
        commissions = Commission.selectBy(sale=sale,
                                          connection=self.trans)
        self.assertEquals(commissions.count(), 1)
        self.assertEquals(commissions[0].value ,Decimal('20.00'))

    def testCommissionAmountMultiple(self):
        sale = self.create_sale()
        sellable = self._add_product(sale, price=200)
        source = CommissionSource(asellable=sellable,
                                  direct_value=10,
                                  installments_value=5,
                                  connection=self.trans)
        sellable = self._add_product(sale, price=300)
        source = CommissionSource(asellable=sellable,
                                  direct_value=12,
                                  installments_value=5,
                                  connection=self.trans)
        sale.order()
        # payment method: money
        # installments number: 1
        self._add_payments(sale)
        self.failIf(Commission.selectBy(connection=self.trans))
        sale.confirm()
        commissions = Commission.selectBy(sale=sale,
                                          connection=self.trans)
        self.assertEquals(commissions.count(), 1)
        self.assertEquals(commissions[0].value, Decimal('56.00'))

class TestSaleItem(DomainTest):
    def testGetTotal(self):
        sale = self.create_sale()
        product = self.create_product(price=10)
        sale_item = sale.add_sellable(product, quantity=5)

        self.assertEqual(sale_item.get_total(), 50)


    def testGetDescription(self):
        sale = self.create_sale()
        product = self.create_product()
        sale_item = sale.add_sellable(product)
        self.assertEqual(sale_item.get_description(), 'Description')
