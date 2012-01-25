# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2009 Async Open Source <http://www.async.com.br>
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

import datetime
from decimal import Decimal

from kiwi.datatypes import currency

from stoqlib.database.orm import AND
from stoqlib.domain.commission import CommissionSource, Commission
from stoqlib.domain.fiscal import CfopData, FiscalBookEntry
from stoqlib.domain.interfaces import IStorable, IInPayment, IOutPayment
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import (Payment, PaymentAdaptToOutPayment,
                                            PaymentAdaptToInPayment)
from stoqlib.domain.sale import Sale
from stoqlib.domain.till import Till, TillEntry
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.parameters import sysparam


class TestSale(DomainTest):

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

        items = sale.get_items()
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

    def testOrder(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sale.add_sellable(sellable, quantity=5)

        self.failUnless(sale.can_order())
        sale.order()
        self.failIf(sale.can_order())

        # We can also order sales with QUOTE status
        sale = self.create_sale()
        sale.status = Sale.STATUS_QUOTE
        sellable = self.create_sellable()
        sale.add_sellable(sellable, quantity=5)
        self.failUnless(sale.can_order())
        sale.order()
        self.failIf(sale.can_order())

    def testConfirmMoney(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()

        self.add_payments(sale, method_type='money')
        self.failIf(FiscalBookEntry.selectOneBy(
            entry_type=FiscalBookEntry.TYPE_PRODUCT,
            payment_group=sale.group,
            connection=self.trans))
        self.failUnless(sale.can_confirm())
        sale.confirm()
        self.failIf(sale.can_confirm())
        self.assertEqual(sale.status, Sale.STATUS_CONFIRMED)
        self.assertEqual(sale.confirm_date.date(), datetime.date.today())

        book_entry = FiscalBookEntry.selectOneBy(
            entry_type=FiscalBookEntry.TYPE_PRODUCT,
            payment_group=sale.group,
            connection=self.trans)
        self.failUnless(book_entry)
        self.assertEqual(book_entry.cfop.code, '5.102')
        self.assertEqual(book_entry.icms_value, Decimal("1.8"))

        for payment in sale.payments:
            self.assertEquals(payment.status, Payment.STATUS_PAID)
            entry = TillEntry.selectOneBy(payment=payment,
                                          connection=self.trans)
            self.assertEquals(entry.value, payment.value)

    def testConfirmCheck(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()

        self.add_payments(sale, method_type='check')
        self.failIf(FiscalBookEntry.selectOneBy(
            entry_type=FiscalBookEntry.TYPE_PRODUCT,
            payment_group=sale.group,
            connection=self.trans))
        self.failUnless(sale.can_confirm())
        sale.confirm()
        self.failIf(sale.can_confirm())
        self.assertEqual(sale.status, Sale.STATUS_CONFIRMED)
        self.assertEqual(sale.confirm_date.date(), datetime.date.today())

        book_entry = FiscalBookEntry.selectOneBy(
            entry_type=FiscalBookEntry.TYPE_PRODUCT,
            payment_group=sale.group,
            connection=self.trans)
        self.failUnless(book_entry)
        self.assertEqual(book_entry.cfop.code, '5.102')
        self.assertEqual(book_entry.icms_value, Decimal("1.8"))

        for payment in sale.payments:
            self.assertEquals(payment.status, Payment.STATUS_PENDING)
            entry = TillEntry.selectOneBy(payment=payment,
                                          connection=self.trans)
            self.assertEquals(entry.value, payment.value)

    def testConfirmClient(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()
        self.add_payments(sale)

        sale.client = self.create_client()
        sale.confirm()
        self.assertEquals(sale.group.payer, sale.client.person)

    def testPay(self):
        sale = self.create_sale()
        self.failIf(sale.can_set_paid())

        self.add_product(sale)
        sale.order()
        self.failIf(sale.can_set_paid())

        self.add_payments(sale)
        sale.confirm()
        self.failUnless(sale.can_set_paid())

        sale.set_paid()
        self.failIf(sale.can_set_paid())
        self.failUnless(sale.close_date)
        self.assertEqual(sale.status, Sale.STATUS_PAID)
        self.assertEqual(sale.close_date.date(), datetime.date.today())

    def testReturn(self):
        sale = self.create_sale()
        sellable = self.add_product(sale)
        storable = IStorable(sellable.product)
        balance_before_sale = storable.get_full_balance()
        sale.order()
        self.add_payments(sale)
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

        self.add_product(sale)
        sale.order()
        self.failIf(sale.can_return())

        self.add_payments(sale)
        sale.confirm()
        self.failUnless(sale.can_return())

        sale.set_paid()
        self.failUnless(sale.can_return())

        sale.return_(sale.create_sale_return_adapter())
        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())

        till = Till.get_current(self.trans)
        self.assertEqual(sale.group.status, PaymentGroup.STATUS_CANCELLED)
        paid_payment = sale.payments[0]
        payment = Payment.selectOne(
            AND(Payment.q.groupID == sale.group.id,
                Payment.q.tillID == till.id,
                Payment.q.id == PaymentAdaptToOutPayment.q.originalID),
            connection=self.trans)
        self.failUnless(payment)
        self.failUnless(IOutPayment(payment, None))
        self.assertEqual(payment.value, paid_payment.value)
        self.assertEqual(payment.status, Payment.STATUS_PAID)
        self.assertEqual(payment.method.method_name, 'money')

        cfop = CfopData.selectOneBy(code='5.202', connection=self.trans)
        book_entry = FiscalBookEntry.selectOneBy(
            entry_type=FiscalBookEntry.TYPE_PRODUCT,
            payment_group=sale.group,
            cfop=cfop,
            connection=self.trans)
        self.failUnless(book_entry)
        self.assertEqual(book_entry.icms_value,
                         Decimal("0.18") * paid_payment.value)

    def testReturnPaidWithPenalty(self):
        sale = self.create_sale()
        self.failIf(sale.can_return())

        self.add_product(sale, price=300)
        sale.order()
        self.failIf(sale.can_return())

        till = Till.get_current(self.trans)
        balance_initial = till.get_balance()

        self.add_payments(sale)
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
        self.assertEqual(sale.group.status, PaymentGroup.STATUS_CANCELLED)

        paid_payment = Payment.selectOne(
            AND(Payment.q.groupID == sale.group.id,
                Payment.q.tillID == till.id,
                Payment.q.id == PaymentAdaptToInPayment.q.originalID),
            connection=self.trans)
        self.failUnless(paid_payment)
        self.failUnless(IInPayment(paid_payment, None))
        self.assertEqual(paid_payment.status, Payment.STATUS_PAID)
        self.assertEqual(paid_payment.method.method_name, 'money')
        return_payment = Payment.selectOne(
            AND(Payment.q.groupID == sale.group.id,
                Payment.q.tillID == till.id,
                Payment.q.id == PaymentAdaptToOutPayment.q.originalID),
            connection=self.trans)
        self.failUnless(return_payment)
        self.failUnless(IOutPayment(return_payment, None))
        self.assertEqual(return_payment.status, Payment.STATUS_PAID)
        self.assertEqual(return_payment.method.method_name, 'money')
        out_payment_plus_penalty = return_payment.value + renegotiation.penalty_value
        self.assertEqual(out_payment_plus_penalty, paid_payment.value)

        cfop = CfopData.selectOneBy(code='5.202', connection=self.trans)
        book_entry = FiscalBookEntry.selectOneBy(
            entry_type=FiscalBookEntry.TYPE_PRODUCT,
            payment_group=sale.group,
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

        self.add_product(sale, price=300)
        sale.order()
        self.failIf(sale.can_return())

        till = Till.get_current(self.trans)
        balance_initial = till.get_balance()

        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment = method.create_inpayment(sale.group, Decimal(300))
        sale.confirm()
        self.failUnless(sale.can_return())

        balance_before_return = till.get_balance()
        self.failIf(balance_before_return <= balance_initial)

        sale.return_(sale.create_sale_return_adapter())
        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())

        self.assertEqual(sale.group.status, PaymentGroup.STATUS_CANCELLED)
        returned_amount = 0
        for payment in sale.payments:
            if IOutPayment(payment, None) is not None:
                returned_amount += payment.value
        self.assertEqual(returned_amount, currency(0))

        balance_final = till.get_balance()
        self.assertEqual(balance_before_return, balance_final)

    def testReturnNotEntirelyPaid(self):
        sale = self.create_sale()
        self.failIf(sale.can_return())

        self.add_product(sale, price=300)
        sale.order()
        self.failIf(sale.can_return())

        till = Till.get_current(self.trans)
        balance_initial = till.get_balance()

        # Add 3 check payments of 100 each
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment1 = method.create_inpayment(sale.group, Decimal(100))
        method.create_inpayment(sale.group, Decimal(100))
        method.create_inpayment(sale.group, Decimal(100))
        sale.confirm()

        # Pay the first payment.
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

        self.assertEqual(sale.group.status, PaymentGroup.STATUS_CANCELLED)
        returned_amount = 0
        for payment in sale.payments:
            if IOutPayment(payment, None) is not None:
                returned_amount += payment.value
        self.assertEqual(payment.value, returned_amount)

        # Till balance after return.
        balance_after_return = balance_before_return - returned_amount

        balance_final = till.get_balance()
        self.assertEqual(balance_after_return, balance_final)

    def testReturnNotEntirelyPaidWithPenalty(self):
        sale = self.create_sale()
        self.failIf(sale.can_return())

        # Add product of costing 300 to the sale
        self.add_product(sale, price=300)
        sale.order()
        self.failIf(sale.can_return())

        # We start out with an empty till
        till = Till.get_current(self.trans)
        balance_initial = till.get_balance()
        self.assertEqual(balance_initial, 0)

        # Add 3 check payments of 100 each
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment1 = method.create_inpayment(sale.group, Decimal(100))
        method.create_inpayment(sale.group, Decimal(100))
        method.create_inpayment(sale.group, Decimal(100))
        sale.confirm()

        # We should have three payments in the sale
        self.assertEqual(sale.payments.count(), 3)

        # Pay the first payment
        payment = payment1.get_adapted()
        payment.pay()
        self.failUnless(sale.can_return())

        # Make sure we received the money in the current till
        balance_before_return = till.get_balance()
        self.assertEqual(balance_before_return, 300)
        self.failUnless(sale.can_return())

        # Return the product, with a 50 penality
        penalty = 50
        renegotiation = sale.create_sale_return_adapter()
        renegotiation.penalty_value = penalty
        sale.return_(renegotiation)
        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())
        self.assertEqual(sale.group.status, PaymentGroup.STATUS_CANCELLED)

        # Till balance after return.
        total_returned = renegotiation.paid_total - penalty
        balance_after_return = balance_before_return - total_returned
        self.failIf(balance_after_return >= balance_before_return)

        # Penality is still 50
        self.assertEqual(renegotiation.penalty_value, penalty)

        # We know have four payments in the sale, the outpayment as well
        self.assertEqual(sale.payments.count(), 4)

        p1, p2, p3, p4 = sale.payments.orderBy('open_date')
        # First three payments are incoming, one each of 50
        self.failUnless(IInPayment(p1))
        self.failIf(IOutPayment(p1, None))
        self.assertEquals(p1.value, 100)

        self.failUnless(IInPayment(p2))
        self.failIf(IOutPayment(p2, None))
        self.assertEquals(p2.value, 100)

        self.failUnless(IInPayment(p3))
        self.failIf(IOutPayment(p3, None))
        self.assertEquals(p3.value, 100)

        # Last payment is outgoing and should be the same amount as the penalty
        self.failIf(IInPayment(p4, None))
        self.failUnless(IOutPayment(p4))
        self.assertEquals(p4.value, penalty)

        # Paid payments: return money in the till, except the penality.
        # To Pay payments: not return money, the value must remain in the till.
        self.assertEqual(till.get_balance(), balance_after_return)

    def testCanCancel(self):
        sale = self.create_sale()
        self.failIf(sale.can_cancel())

        self.add_product(sale)
        sale.order()
        self.failUnless(sale.can_cancel())

        sale.status = Sale.STATUS_QUOTE
        self.failUnless(sale.can_cancel())

        self.add_payments(sale)
        sale.confirm()
        self.failUnless(sale.can_cancel())

        sale.set_paid()
        self.failUnless(sale.can_cancel())

        sale.return_(sale.create_sale_return_adapter())
        self.failIf(sale.can_cancel())

    def testCancel(self):
        sale = self.create_sale()
        sellable = self.add_product(sale)
        storable = IStorable(sellable.product)
        inital_quantity = storable.get_full_balance()
        sale.order()
        sale.cancel()
        self.assertEquals(sale.status, Sale.STATUS_CANCELLED)
        final_quantity = storable.get_full_balance()
        self.assertEquals(inital_quantity, final_quantity)

    def testCancelPaid(self):
        sale = self.create_sale()
        sellable = self.add_product(sale)
        storable = IStorable(sellable.product)
        initial_quantity = storable.get_full_balance()
        sale.order()

        self.add_payments(sale)
        sale.confirm()
        sale.set_paid()
        self.failUnless(sale.can_cancel())

        after_confirmed_quantity = storable.get_full_balance()
        self.assertEquals(initial_quantity - 1, after_confirmed_quantity)

        self.failUnless(sale.can_cancel())
        sale.cancel()
        self.assertEquals(sale.status, Sale.STATUS_CANCELLED)

        final_quantity = storable.get_full_balance()
        self.assertEquals(initial_quantity, final_quantity)

    def testCancelNotPaid(self):
        sale = self.create_sale()
        sellable = self.add_product(sale, price=300)
        storable = IStorable(sellable.product)
        initial_quantity = storable.get_full_balance()
        sale.order()
        self.failUnless(sale.can_cancel())

        self.add_payments(sale)
        sale.confirm()

        after_confirmed_quantity = storable.get_full_balance()
        self.assertEquals(initial_quantity - 1, after_confirmed_quantity)

        self.failUnless(sale.can_cancel())
        sale.cancel()
        self.assertEquals(sale.status, Sale.STATUS_CANCELLED)

        final_quantity = storable.get_full_balance()
        self.assertEquals(initial_quantity, final_quantity)

    def testCancelQuote(self):
        sale = self.create_sale()
        sellable = self.add_product(sale)
        storable = IStorable(sellable.product)
        inital_quantity = storable.get_full_balance()
        sale.status = Sale.STATUS_QUOTE
        sale.cancel()
        self.assertEquals(sale.status, Sale.STATUS_CANCELLED)
        final_quantity = storable.get_full_balance()
        self.assertEquals(inital_quantity, final_quantity)

    def testCanSetRenegotiated(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()

        self.add_payments(sale, method_type='check')
        sale.confirm()

        self.failUnless(sale.can_set_renegotiated())

        for payment in sale.payments:
            payment.pay()

        self.failIf(sale.can_set_renegotiated())

    def testSetRenegotiated(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()

        self.add_payments(sale, method_type='check')
        sale.confirm()

        self.failUnless(sale.can_set_renegotiated())
        sale.set_renegotiated()
        self.assertEqual(sale.status, Sale.STATUS_RENEGOTIATED)

        for payment in sale.payments:
            payment.cancel()

        self.failIf(sale.can_set_renegotiated())

    def testProducts(self):
        sale = self.create_sale()
        self.failIf(sale.products)

        service = self.create_service()
        sellable = service.sellable
        sale.add_sellable(sellable, quantity=1)

        self.failIf(sale.products)

        product = self.create_product()
        sellable = product.sellable
        sale.add_sellable(sellable, quantity=1)

        self.failUnless(sale.products)

    def testServices(self):
        sale = self.create_sale()
        self.failIf(sale.services)

        product = self.create_product()
        sellable = product.sellable
        sale.add_sellable(sellable, quantity=1)

        self.failIf(sale.services)

        service = self.create_service()
        sellable = service.sellable
        sale.add_sellable(sellable, quantity=1)

        self.failUnless(sale.services)

    def testSaleWithDelivery(self):
        sale = self.create_sale()
        self.failIf(sale.can_set_paid())

        self.add_product(sale)

        sellable = sysparam(self.trans).DELIVERY_SERVICE.sellable
        sale.add_sellable(sellable, quantity=1)
        sale.order()
        self.failIf(sale.can_set_paid())

        self.add_payments(sale)
        sale.confirm()

    def testCommissionAmount(self):
        sale = self.create_sale()
        sellable = self.add_product(sale, price=200)
        CommissionSource(sellable=sellable,
                         direct_value=10,
                         installments_value=5,
                         connection=self.trans)
        sale.order()
        # payment method: money
        # installments number: 1
        self.add_payments(sale)
        self.failIf(Commission.selectBy(sale=sale,
                                        connection=self.trans))
        sale.confirm()
        commissions = Commission.selectBy(sale=sale,
                                          connection=self.trans)
        self.assertEquals(commissions.count(), 1)
        self.assertEquals(commissions[0].value, Decimal('20.00'))

    def testCommissionAmountMultiple(self):
        sale = self.create_sale()
        sellable = self.add_product(sale, price=200)
        CommissionSource(sellable=sellable,
                         direct_value=10,
                         installments_value=5,
                         connection=self.trans)
        sellable = self.add_product(sale, price=300)
        CommissionSource(sellable=sellable,
                         direct_value=12,
                         installments_value=5,
                         connection=self.trans)
        sale.order()
        # payment method: money
        # installments number: 1
        self.add_payments(sale)
        self.failIf(Commission.selectBy(sale=sale,
                                        connection=self.trans))
        sale.confirm()
        commissions = Commission.selectBy(sale=sale,
                                          connection=self.trans)
        self.assertEquals(commissions.count(), 1)
        self.assertEquals(commissions[0].value, Decimal('56.00'))

    def testCommissionAmountWhenSaleReturn(self):
        sale = self.create_sale()
        sellable = self.add_product(sale, price=200)
        CommissionSource(sellable=sellable,
                         direct_value=10,
                         installments_value=5,
                         connection=self.trans)
        sale.order()
        # payment method: money
        # installments number: 1
        self.add_payments(sale)
        self.failIf(Commission.selectBy(sale=sale,
                                        connection=self.trans))
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

    def testOnlyPaidWithMoney(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()
        self.add_payments(sale, method_type='money')
        sale.confirm()

        self.failUnless(sale.only_paid_with_money())

        sale = self.create_sale()
        self.add_product(sale)
        sale.order()
        self.add_payments(sale, method_type='check')
        sale.confirm()

        self.failIf(sale.only_paid_with_money())

    def testQuoteSale(self):
        sale = self.create_sale()
        sale.status = Sale.STATUS_QUOTE
        self.add_product(sale)

        self.failUnless(sale.can_confirm())
        self.add_payments(sale)
        sale.confirm()
        self.failIf(sale.can_confirm())
        self.assertEqual(sale.status, Sale.STATUS_CONFIRMED)

    def testAccountTransactionCheck(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()

        payment = self.add_payments(sale, method_type='check').payment

        account = self.create_account()
        payment.method.destination_account = account

        self.failIf(account.transactions)

        paid_date = datetime.datetime(2010, 1, 2)
        sale.confirm()
        payment.pay(paid_date)

        self.failUnless(account.transactions)
        self.assertEquals(account.transactions.count(), 1)

        t = account.transactions[0]
        self.assertEquals(t.payment, payment)
        self.assertEquals(t.value, payment.value)
        self.assertEquals(t.date, payment.paid_date)

    def testAccountTransactionMoney(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()
        payment = self.add_payments(sale, method_type='money').payment
        account = self.create_account()
        payment.method.destination_account = account
        self.failIf(account.transactions)
        sale.confirm()
        self.failIf(account.transactions)


class TestSaleItem(DomainTest):
    def testGetTotal(self):
        sale = self.create_sale()
        product = self.create_product(price=10)
        sale_item = sale.add_sellable(product.sellable, quantity=5)

        self.assertEqual(sale_item.get_total(), 50)

    def testGetDescription(self):
        sale = self.create_sale()
        product = self.create_product()
        sale_item = sale.add_sellable(product.sellable)
        self.assertEqual(sale_item.get_description(), 'Description')

    def testIsService(self):
        sale = self.create_sale()
        product = self.create_product(price=10)
        sale_item = sale.add_sellable(product.sellable, quantity=5)
        self.failIf(sale_item.is_service() is True)

        service = self.create_service()
        sale_item = sale.add_sellable(service.sellable, quantity=2)
        self.failIf(sale_item.is_service() is False)
