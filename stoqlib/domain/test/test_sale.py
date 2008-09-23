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
from stoqlib.domain.interfaces import (IPaymentGroup,
                                       ISellable,
                                       IStorable,
                                       IOutPayment,
                                       IGiftCertificate)
from stoqlib.domain.payment.group import AbstractPaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment, PaymentAdaptToOutPayment
from stoqlib.domain.sale import Sale
from stoqlib.domain.sellable import SellableTaxConstant
from stoqlib.domain.till import Till, TillEntry
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.parameters import sysparam

class TestSale(DomainTest):

    def _add_payments(self, sale, method_type='money'):
        group = IPaymentGroup(sale, None)
        if group is None:
            group = sale.addFacet(IPaymentGroup, connection=self.trans)
            
        method = PaymentMethod.get_by_name(self.trans, method_type)
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

    def testCheckPaymentGroup(self):
        sale_no_payment = self.create_sale()

        sale = self.create_sale()
        sale.addFacet(IPaymentGroup, connection=self.trans)

        group = IPaymentGroup(sale, None)
        assert isinstance(group, Sale.getAdapterClass(IPaymentGroup))
        self.failIf(IPaymentGroup(sale_no_payment, None))

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

        self._add_payments(sale, method_type='money')
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

        self._add_payments(sale, method_type='check')
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
        sellable = self._add_product(sale)
        storable = IStorable(sellable)
        balance_before_sale = storable.get_full_balance()
        sale.order()
        self._add_payments(sale)
        sale.confirm()

        self.failUnless(sale.can_return())
        sale.return_(sale.create_sale_return_adapter())
        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())

        balance_after_sale = storable.get_full_balance()
        self.assertEqual(balance_before_sale, balance_after_sale)

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
        self.assertEqual(payment.method.method_name, 'money')

        cfop = CfopData.selectOneBy(code='5.202', connection=self.trans)
        book_entry = FiscalBookEntry.selectOneBy(
            entry_type=FiscalBookEntry.TYPE_PRODUCT,
            payment_group=group,
            cfop=cfop,
            connection=self.trans)
        self.failUnless(book_entry)
        self.assertEqual(book_entry.icms_value,
                         Decimal("0.18") * paid_payment.value)

    def testReturnPaidWithPenalty(self):
        sale = self.create_sale()
        self.failIf(sale.can_return())

        self._add_product(sale, price=300)
        sale.order()
        self.failIf(sale.can_return())

        till = Till.get_current(self.trans)
        balance_initial = till.get_balance()

        self._add_payments(sale)
        sale.confirm()
        self.failUnless(sale.can_return())

        balance_before_return = till.get_balance()
        self.failIf(balance_before_return <= balance_initial)

        sale.set_paid()
        self.failUnless(sale.can_return())

        renegotiation = sale.create_sale_return_adapter()
        renegotiation.penalty_value = currency(50)
        sale.return_(renegotiation)
        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())

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
        out_payment_plus_penalty = payment.value + renegotiation.penalty_value
        self.assertEqual(out_payment_plus_penalty, paid_payment.value)
        self.assertEqual(payment.status, Payment.STATUS_PAID)
        self.assertEqual(payment.method.method_name, 'money')

        cfop = CfopData.selectOneBy(code='5.202', connection=self.trans)
        book_entry = FiscalBookEntry.selectOneBy(
            entry_type=FiscalBookEntry.TYPE_PRODUCT,
            payment_group=group,
            cfop=cfop,
            connection=self.trans)
        self.failUnless(book_entry)
        self.assertEqual(book_entry.icms_value,
                         Decimal("0.18") * paid_payment.value)

        balance_final = till.get_balance()
        self.failIf(balance_initial >= balance_final)

    def testReturnNotPaid(self):
        sale = self.create_sale()
        self.failIf(sale.can_return())

        product = self._add_product(sale, price=300)
        sale.order()
        self.failIf(sale.can_return())

        till = Till.get_current(self.trans)
        balance_initial = till.get_balance()

        group = sale.addFacet(IPaymentGroup, connection=self.trans)
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment = method.create_inpayment(group, Decimal(300))
        sale.confirm()
        self.failUnless(sale.can_return())

        balance_before_return = till.get_balance()
        self.failIf(balance_before_return <= balance_initial)

        sale.return_(sale.create_sale_return_adapter())
        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())

        self.assertEqual(group.cancel_date.date(), datetime.date.today())
        self.assertEqual(group.status, AbstractPaymentGroup.STATUS_CANCELLED)
        returned_amount = 0
        for item in group.get_items():
            if IOutPayment(item, None) is not None:
                returned_amount += item.value
        self.assertEqual(returned_amount, currency(0))

        balance_final = till.get_balance()
        self.assertEqual(balance_initial, balance_final)

    def testReturnNotEntirelyPaid(self):
        sale = self.create_sale()
        self.failIf(sale.can_return())

        self._add_product(sale, price=300)
        sale.order()
        self.failIf(sale.can_return())

        till = Till.get_current(self.trans)
        balance_initial = till.get_balance()

        group = sale.addFacet(IPaymentGroup, connection=self.trans)
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment1 = method.create_inpayment(group, Decimal(100))
        payment2 = method.create_inpayment(group, Decimal(100))
        payment3 = method.create_inpayment(group, Decimal(100))
        sale.confirm()
        payment = payment1.get_adapted()
        payment.pay()
        self.failUnless(sale.can_return())

        balance_before_return = till.get_balance()
        self.failIf(balance_before_return <= balance_initial)

        self.failUnless(sale.can_return())
        sale.return_(sale.create_sale_return_adapter())
        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())

        self.assertEqual(group.cancel_date.date(), datetime.date.today())
        self.assertEqual(group.status, AbstractPaymentGroup.STATUS_CANCELLED)
        returned_amount = 0
        for item in group.get_items():
            if IOutPayment(item, None) is not None:
                returned_amount += item.value
        self.assertEqual(payment.value, returned_amount)

        balance_final = till.get_balance()
        self.assertEqual(balance_initial, balance_final)

    def testReturnNotEntirelyPaidWithPenalty(self):
        sale = self.create_sale()
        self.failIf(sale.can_return())

        self._add_product(sale, price=300)
        sale.order()
        self.failIf(sale.can_return())

        till = Till.get_current(self.trans)
        balance_initial = till.get_balance()

        group = sale.addFacet(IPaymentGroup, connection=self.trans)
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment1 = method.create_inpayment(group, Decimal(100))
        payment2 = method.create_inpayment(group, Decimal(100))
        payment3 = method.create_inpayment(group, Decimal(100))
        sale.confirm()
        payment = payment1.get_adapted()
        payment.pay()
        self.failUnless(sale.can_return())

        balance_before_return = till.get_balance()
        self.failIf(balance_before_return <= balance_initial)

        self.failUnless(sale.can_return())
        renegotiation = sale.create_sale_return_adapter()
        renegotiation.penalty_value = currency(50)
        sale.return_(renegotiation)
        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())

        self.assertEqual(group.cancel_date.date(), datetime.date.today())
        self.assertEqual(group.status, AbstractPaymentGroup.STATUS_CANCELLED)
        returned_amount = 0
        for item in group.get_items():
            if IOutPayment(item, None) is not None:
                returned_amount += item.value
        paid_value = payment.value - renegotiation.penalty_value
        self.assertEqual(paid_value, returned_amount)

        balance_final = till.get_balance()
        self.failIf(balance_initial >= balance_final)

    def testCanCancel(self):
        sale = self.create_sale()
        self.failIf(sale.can_cancel())

        self._add_product(sale)
        sale.order()
        self.failUnless(sale.can_cancel())

        self._add_payments(sale)
        sale.confirm()
        self.failUnless(sale.can_cancel())

        sale.set_paid()
        self.failUnless(sale.can_cancel())

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

    def testCommissionAmountWhenSaleReturn(self):
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
        sale.return_(sale.create_sale_return_adapter())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)

        commissions = Commission.selectBy(sale=sale,
                                          connection=self.trans)
        value = sum([c.value for c in commissions])
        self.assertEqual(value, Decimal(0))
        self.assertEqual(commissions.count(), 2)
        self.failIf(commissions[-1].value >= 0)

    def testGetClientRole(self):
        sale = self.create_sale()
        client_role = sale.get_client_role()
        self.failUnless(client_role is None)

        sale.client = self.create_client()
        client_role = sale.get_client_role()
        self.failIf(client_role is None)

    def testPaidWithMoney(self):
        sale = self.create_sale()
        self._add_product(sale)
        sale.order()
        self._add_payments(sale, method_type='money')
        sale.confirm()

        self.failUnless(sale.paid_with_money())

        sale = self.create_sale()
        self._add_product(sale)
        sale.order()
        self._add_payments(sale, method_type='check')
        sale.confirm()

        self.failIf(sale.paid_with_money())


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
