# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2008 Async Open Source <http://www.async.com.br>
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

__tests__ = 'stoqlib/domain/payment/group.py'

from decimal import Decimal

from nose.exc import SkipTest
from kiwi.python import Settable

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.commission import CommissionSource, Commission
from stoqlib.domain.events import PaymentGroupGetOrderEvent
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.sale import Sale
from stoqlib.domain.stockdecrease import StockDecrease
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.parameters import sysparam

StockDecrease  # pylint: disable=W0104


class TestPaymentGroup(DomainTest):

    def setUp(self):
        # FIXME: On some tests where PaymentGroup._renegotiation is accessed,
        # a traceback ocours because PaymentRenegotiation were not imported.
        # We can't import it on PaymentGroup since it would generate an import
        # loop error. This is a potential problem on Stoq and we should be
        # fixed there.
        from stoqlib.domain.payment.renegotiation import PaymentRenegotiation
        PaymentRenegotiation  # pylint: disable=W0104

        super(TestPaymentGroup, self).setUp()

    def _payComissionWhenConfirmed(self):
        sysparam.set_bool(
            self.store,
            "SALE_PAY_COMMISSION_WHEN_CONFIRMED",
            True)
        self.failUnless(
            sysparam.get_bool('SALE_PAY_COMMISSION_WHEN_CONFIRMED'))

    def test_remove_item(self):
        payment = self.create_payment()
        with self.assertRaises(AttributeError):
            payment.group.remove_item(payment=None)
        self.assertIsNone(payment.group.remove_item(payment=payment))

    def test_installments_number(self):
        payment = self.create_payment()
        self.assertEquals(payment.group.installments_number, 1)

    def test_get_payments_sum(self):
        payment = self.create_payment()
        payments = payment.group.get_valid_payments()
        result = payment.group._get_payments_sum(payments=payments,
                                                 attr=Payment.value)
        self.assertEquals(result, 10)

    def test_clear_unused(self):
        payment = self.create_payment()
        payment2 = self.create_payment(group=payment.group)
        payment2.status = Payment.STATUS_PREVIEW
        self.assertEquals(payment.group._get_preview_payments().count(), 2)
        payment.group.clear_unused()
        with self.assertRaises(AttributeError):
            payment.group._get_preview_payments()

    def test_confirm(self):
        branch = self.create_branch()
        group = self.create_payment_group()

        method = PaymentMethod.get_by_name(self.store, u'bill')
        payment1 = method.create_payment(Payment.TYPE_IN, group, branch, Decimal(10))
        payment2 = method.create_payment(Payment.TYPE_IN, group, branch, Decimal(10))

        payment2.set_pending()
        self.assertEqual(payment1.status, Payment.STATUS_PREVIEW)
        self.assertEqual(payment2.status, Payment.STATUS_PENDING)

        group.confirm()
        self.assertEqual(payment1.status, Payment.STATUS_PENDING)
        self.assertEqual(payment2.status, Payment.STATUS_PENDING)

    def test_pay(self):
        branch = self.create_branch()
        group = self.create_payment_group()

        method = PaymentMethod.get_by_name(self.store, u'bill')
        payment1 = method.create_payment(Payment.TYPE_IN, group, branch, Decimal(10))
        payment2 = method.create_payment(Payment.TYPE_IN, group, branch, Decimal(10))
        group.confirm()

        self.assertEqual(payment1.status, Payment.STATUS_PENDING)
        self.assertEqual(payment2.status, Payment.STATUS_PENDING)
        payment2.pay()
        self.assertEqual(payment2.status, Payment.STATUS_PAID)

        group.pay()
        self.assertEqual(payment1.status, Payment.STATUS_PAID)
        self.assertEqual(payment2.status, Payment.STATUS_PAID)

    def test_pay_money_payments(self):
        branch = self.create_branch()
        group = self.create_payment_group()

        method = PaymentMethod.get_by_name(self.store, u'bill')
        payment1 = method.create_payment(Payment.TYPE_IN, group, branch, Decimal(10))
        payment2 = method.create_payment(Payment.TYPE_IN, group, branch, Decimal(10))
        method = PaymentMethod.get_by_name(self.store, u'money')
        method.max_installments = 2
        payment3 = method.create_payment(Payment.TYPE_IN, group, branch, Decimal(10))
        payment4 = method.create_payment(Payment.TYPE_IN, group, branch, Decimal(10))
        group.confirm()

        self.assertEqual(payment1.status, Payment.STATUS_PENDING)
        self.assertEqual(payment2.status, Payment.STATUS_PENDING)
        self.assertEqual(payment3.status, Payment.STATUS_PENDING)
        self.assertEqual(payment4.status, Payment.STATUS_PENDING)
        payment3.pay()
        self.assertEqual(payment3.status, Payment.STATUS_PAID)

        group.pay_method_payments(u'money')
        self.assertEqual(payment1.status, Payment.STATUS_PENDING)
        self.assertEqual(payment2.status, Payment.STATUS_PENDING)
        self.assertEqual(payment3.status, Payment.STATUS_PAID)
        self.assertEqual(payment4.status, Payment.STATUS_PAID)

    def test_cancel(self):
        branch = self.create_branch()
        group = self.create_payment_group()

        method = PaymentMethod.get_by_name(self.store, u'bill')
        payment1 = method.create_payment(Payment.TYPE_IN, group, branch, Decimal(10))
        payment2 = method.create_payment(Payment.TYPE_IN, group, branch, Decimal(10))
        payment3 = method.create_payment(Payment.TYPE_IN, group, branch, Decimal(10))
        group.confirm()

        payment3.pay()
        self.assertEqual(payment1.status, Payment.STATUS_PENDING)
        self.assertEqual(payment2.status, Payment.STATUS_PENDING)
        self.assertEqual(payment3.status, Payment.STATUS_PAID)

        group.cancel()
        self.assertEqual(payment1.status, Payment.STATUS_CANCELLED)
        self.assertEqual(payment2.status, Payment.STATUS_CANCELLED)
        self.assertEqual(payment3.status, Payment.STATUS_PAID)

    def test_installments_commission_amount(self):
        self._payComissionWhenConfirmed()

        sale = self.create_sale()
        sellable = self.add_product(sale, price=300)
        sale.order()
        CommissionSource(sellable=sellable,
                         direct_value=12,
                         installments_value=5,
                         store=self.store)

        method = PaymentMethod.get_by_name(self.store, u'check')
        method.create_payment(Payment.TYPE_IN, sale.group, sale.branch, Decimal(100))
        method.create_payment(Payment.TYPE_IN, sale.group, sale.branch, Decimal(200))
        self.assertTrue(self.store.find(Commission, sale=sale).is_empty())
        sale.confirm()
        self.assertFalse(self.store.find(Commission, sale=sale).is_empty())

        commissions = self.store.find(Commission,
                                      sale=sale).order_by(Commission.value)
        self.assertEquals(commissions.count(), 2)
        for c in commissions:
            self.failUnless(c.commission_type == Commission.INSTALLMENTS)

        # the first payment represent 1/3 of the total amount
        # 5% of 300: 15,00 * 1/3 => 5,00
        self.assertEquals(commissions[0].value, Decimal("5.00"))
        # the second payment represent 2/3 of the total amount
        # $15 * 2/3 => 10,00
        self.assertEquals(commissions[1].value, Decimal("10.00"))

    def test_installments_commission_amount_with_multiple_items(self):
        self._payComissionWhenConfirmed()

        sale = self.create_sale()
        sellable = self.add_product(sale, price=300, quantity=3)
        sale.order()

        CommissionSource(sellable=sellable,
                         direct_value=12,
                         installments_value=5,
                         store=self.store)

        method = PaymentMethod.get_by_name(self.store, u'check')
        method.create_payment(Payment.TYPE_IN, sale.group, sale.branch, Decimal(300))
        method.create_payment(Payment.TYPE_IN, sale.group, sale.branch, Decimal(450))
        method.create_payment(Payment.TYPE_IN, sale.group, sale.branch, Decimal(150))
        self.assertTrue(self.store.find(Commission, sale=sale).is_empty())

        sale.confirm()

        commissions = self.store.find(Commission,
                                      sale=sale).order_by(Commission.value)
        self.assertEquals(commissions.count(), 3)
        for c in commissions:
            self.failUnless(c.commission_type == Commission.INSTALLMENTS)

        # the first payment represent 1/3 of the total amount
        # 45 / 6 => 7.50
        self.assertEquals(commissions[0].value, Decimal("7.50"))
        # the second payment represent 1/3 of the total amount
        # 5% of 900: 45,00 * 1/3 => 15,00
        self.assertEquals(commissions[1].value, Decimal("15.00"))
        # the third payment represent 1/2 of the total amount
        # 45 / 2 => 22,50
        self.assertEquals(commissions[2].value, Decimal("22.50"))

    def test_installments_commission_amount_when_sale_return(self):
        if True:
            raise SkipTest(u"See stoqlib.domain.returnedsale.ReturnedSale.return_ "
                           u"and bug 5215.")

        self._payComissionWhenConfirmed()
        sale = self.create_sale()
        sellable = self.create_sellable()
        CommissionSource(sellable=sellable,
                         direct_value=12,
                         installments_value=5,
                         store=self.store)

        sale.add_sellable(sellable, quantity=3, price=300)
        product = sellable.product
        branch = get_current_branch(self.store)
        self.create_storable(product, branch, 100)

        sale.order()
        method = PaymentMethod.get_by_name(self.store, u'check')
        payment1 = method.create_payment(Payment.TYPE_IN, sale.group, sale.branch, Decimal(300))
        payment2 = method.create_payment(Payment.TYPE_IN, sale.group, sale.branch, Decimal(450))
        payment3 = method.create_payment(Payment.TYPE_IN, sale.group, sale.branch, Decimal(150))
        sale.confirm()

        # the commissions are created after the payment
        payment1.pay()
        payment2.pay()
        payment3.pay()

        returned_sale = sale.create_sale_return_adapter()
        returned_sale.return_()
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)

        commissions = self.store.find(Commission, sale=sale)
        value = sum([c.value for c in commissions])
        self.assertEqual(value, Decimal(0))
        self.assertEqual(commissions.count(), 4)
        self.failIf(commissions[-1].value >= 0)

    def test_get_total_value(self):
        method = PaymentMethod.get_by_name(self.store, u'check')

        # Test for a group in a sale
        # On sale's group, total value should return
        # sum(inpayments.value) - sum(outpayments.value)
        sale = self.create_sale()
        group = sale.group
        self.assertEqual(group.get_total_value(), 0)

        method.create_payment(Payment.TYPE_IN, group, sale.branch, Decimal(100))
        self.assertEqual(group.get_total_value(), Decimal(100))

        method.create_payment(Payment.TYPE_IN, group, sale.branch, Decimal(200))
        self.assertEqual(group.get_total_value(), Decimal(300))

        method.create_payment(Payment.TYPE_OUT, group, sale.branch, Decimal(50))
        self.assertEqual(group.get_total_value(), Decimal(250))

        # Test for a group in a purchase
        # On purchase's group, total value should return
        # sum(inpayments.value) - sum(outpayments.value)
        purchase = self.create_purchase_order()
        group = purchase.group
        self.assertEqual(group.get_total_value(), 0)

        method.create_payment(Payment.TYPE_OUT, group, purchase.branch, Decimal(100))
        self.assertEqual(group.get_total_value(), Decimal(100))

        method.create_payment(Payment.TYPE_OUT, group, purchase.branch, Decimal(200))
        self.assertEqual(group.get_total_value(), Decimal(300))

        method.create_payment(Payment.TYPE_IN, group, purchase.branch, Decimal(50))
        self.assertEqual(group.get_total_value(), Decimal(250))

    def test_get_total_to_pay(self):
        method = PaymentMethod.get_by_name(self.store, u'check')

        # Test for a group in a sale
        sale = self.create_sale()
        group = sale.group
        self.assertEqual(group.get_total_to_pay(), 0)

        payment1 = method.create_payment(Payment.TYPE_IN, group, sale.branch,
                                         Decimal(100))
        payment1.set_pending()
        self.assertEqual(group.get_total_to_pay(), Decimal(100))

        payment2 = method.create_payment(Payment.TYPE_IN, group, sale.branch,
                                         Decimal(200))
        payment2.set_pending()
        self.assertEqual(group.get_total_to_pay(), Decimal(300))

        payment1.pay()
        self.assertEqual(group.get_total_to_pay(), Decimal(200))

        payment2.pay()
        self.assertEqual(group.get_total_to_pay(), Decimal(0))

    def test_get_total_confirmed_value(self):
        method = PaymentMethod.get_by_name(self.store, u'check')

        # Test for a group in a sale
        # On sale's group, total value should return
        # sum(inpayments.value) - sum(outpayments.value)
        sale = self.create_sale()
        group = sale.group
        self.assertEqual(group.get_total_confirmed_value(), 0)

        p = method.create_payment(
            Payment.TYPE_IN, group, sale.branch, Decimal(100))
        self.assertEqual(group.get_total_confirmed_value(), 0)
        p.set_pending()
        self.assertEqual(group.get_total_confirmed_value(), 100)

        p = method.create_payment(
            Payment.TYPE_IN, group, sale.branch, Decimal(200))
        self.assertEqual(group.get_total_confirmed_value(), 100)
        p.set_pending()
        self.assertEqual(group.get_total_confirmed_value(), 300)

        p = method.create_payment(
            Payment.TYPE_OUT, group, sale.branch, Decimal(50))
        self.assertEqual(group.get_total_confirmed_value(), 300)
        p.set_pending()
        self.assertEqual(group.get_total_confirmed_value(), 250)

        # Test for a group in a purchase
        # On purchase's group, total value should return
        # sum(inpayments.value) - sum(outpayments.value)
        purchase = self.create_purchase_order()
        group = purchase.group
        self.assertEqual(group.get_total_confirmed_value(), 0)

        p = method.create_payment(
            Payment.TYPE_OUT, group, purchase.branch, Decimal(100))
        self.assertEqual(group.get_total_confirmed_value(), 0)
        p.set_pending()
        self.assertEqual(group.get_total_confirmed_value(), 100)

        p = method.create_payment(
            Payment.TYPE_OUT, group, purchase.branch, Decimal(200))
        self.assertEqual(group.get_total_confirmed_value(), 100)
        p.set_pending()
        self.assertEqual(group.get_total_confirmed_value(), 300)

        p = method.create_payment(
            Payment.TYPE_IN, group, purchase.branch, Decimal(50))
        self.assertEqual(group.get_total_confirmed_value(), 300)
        p.set_pending()
        self.assertEqual(group.get_total_confirmed_value(), 250)

    def test_get_total_discount(self):
        method = PaymentMethod.get_by_name(self.store, u'check')

        # Test for a group in a sale
        # On sale's group, total value should return
        # sum(inpayments.discount) - sum(outpayments.discount)
        sale = self.create_sale()
        group = sale.group
        self.assertEqual(group.get_total_value(), 0)

        p = method.create_payment(Payment.TYPE_IN, group, sale.branch, Decimal(10))
        p.discount = Decimal(10)
        self.assertEqual(group.get_total_discount(), Decimal(10))

        p = method.create_payment(Payment.TYPE_IN, group, sale.branch, Decimal(10))
        p.discount = Decimal(20)
        self.assertEqual(group.get_total_discount(), Decimal(30))

        p = method.create_payment(Payment.TYPE_OUT, group, sale.branch, Decimal(10))
        p.discount = Decimal(10)
        self.assertEqual(group.get_total_discount(), Decimal(20))

        # Test for a group in a purchase
        # On purchase's group, total value should return
        # sum(inpayments.discount) - sum(outpayments.discount)
        purchase = self.create_purchase_order()
        group = purchase.group
        self.assertEqual(group.get_total_value(), 0)

        p = method.create_payment(Payment.TYPE_OUT, group, purchase.branch, Decimal(10))
        p.discount = Decimal(10)
        self.assertEqual(group.get_total_discount(), Decimal(10))

        p = method.create_payment(Payment.TYPE_OUT, group, purchase.branch, Decimal(10))
        p.discount = Decimal(20)
        self.assertEqual(group.get_total_discount(), Decimal(30))

        p = method.create_payment(Payment.TYPE_IN, group, purchase.branch, Decimal(10))
        p.discount = Decimal(10)
        self.assertEqual(group.get_total_discount(), Decimal(20))

    def test_get_total_interest(self):
        method = PaymentMethod.get_by_name(self.store, u'check')

        # Test for a group in a sale
        # On sale's group, total value should return
        # sum(inpayments.interest) - sum(outpayments.interest)
        sale = self.create_sale()
        group = sale.group
        self.assertEqual(group.get_total_value(), 0)

        p = method.create_payment(Payment.TYPE_IN, group, sale.branch, Decimal(10))
        p.interest = Decimal(10)
        self.assertEqual(group.get_total_interest(), Decimal(10))

        p = method.create_payment(Payment.TYPE_IN, group, sale.branch, Decimal(10))
        p.interest = Decimal(20)
        self.assertEqual(group.get_total_interest(), Decimal(30))

        p = method.create_payment(Payment.TYPE_OUT, group, sale.branch, Decimal(10))
        p.interest = Decimal(10)
        self.assertEqual(group.get_total_interest(), Decimal(20))

        # Test for a group in a purchase
        # On purchase's group, total value should return
        # sum(inpayments.interest) - sum(outpayments.interest)
        purchase = self.create_purchase_order()
        group = purchase.group
        self.assertEqual(group.get_total_value(), 0)

        p = method.create_payment(Payment.TYPE_OUT, group, purchase.branch, Decimal(10))
        p.interest = Decimal(10)
        self.assertEqual(group.get_total_interest(), Decimal(10))

        p = method.create_payment(Payment.TYPE_OUT, group, purchase.branch, Decimal(10))
        p.interest = Decimal(20)
        self.assertEqual(group.get_total_interest(), Decimal(30))

        p = method.create_payment(Payment.TYPE_IN, group, purchase.branch, Decimal(10))
        p.interest = Decimal(10)
        self.assertEqual(group.get_total_interest(), Decimal(20))

    def test_get_total_penalty(self):
        method = PaymentMethod.get_by_name(self.store, u'check')

        # Test for a group in a sale
        # On sale's group, total value should return
        # sum(inpayments.penalty) - sum(outpayments.penalty)
        sale = self.create_sale()
        group = sale.group
        self.assertEqual(group.get_total_value(), 0)

        p = method.create_payment(Payment.TYPE_IN, group, sale.branch, Decimal(10))
        p.penalty = Decimal(10)
        self.assertEqual(group.get_total_penalty(), Decimal(10))

        p = method.create_payment(Payment.TYPE_IN, group, sale.branch, Decimal(10))
        p.penalty = Decimal(20)
        self.assertEqual(group.get_total_penalty(), Decimal(30))

        p = method.create_payment(Payment.TYPE_OUT, group, sale.branch, Decimal(10))
        p.penalty = Decimal(10)
        self.assertEqual(group.get_total_penalty(), Decimal(20))

        # Test for a group in a purchase
        # On purchase's group, total value should return
        # sum(inpayments.penalty) - sum(outpayments.penalty)
        purchase = self.create_purchase_order()
        group = purchase.group
        self.assertEqual(group.get_total_value(), 0)

        p = method.create_payment(Payment.TYPE_OUT, group, purchase.branch, Decimal(10))
        p.penalty = Decimal(10)
        self.assertEqual(group.get_total_penalty(), Decimal(10))

        p = method.create_payment(Payment.TYPE_OUT, group, purchase.branch, Decimal(10))
        p.penalty = Decimal(20)
        self.assertEqual(group.get_total_penalty(), Decimal(30))

        p = method.create_payment(Payment.TYPE_IN, group, purchase.branch, Decimal(10))
        p.penalty = Decimal(10)
        self.assertEqual(group.get_total_penalty(), Decimal(20))

    def test_get_payment_by_method_name(self):
        group = self.create_payment_group()

        method = PaymentMethod.get_by_name(self.store, u'money')
        money_payment1 = self.create_payment(method=method)
        group.add_item(money_payment1)
        money_payment2 = self.create_payment(method=method)
        group.add_item(money_payment2)

        method = PaymentMethod.get_by_name(self.store, u'check')
        check_payment1 = self.create_payment(method=method)
        group.add_item(check_payment1)
        check_payment2 = self.create_payment(method=method)
        group.add_item(check_payment2)

        money_payments = group.get_payments_by_method_name(u'money')
        for payment in [money_payment1, money_payment2]:
            self.assertTrue(payment in money_payments)
        for payment in [check_payment1, check_payment2]:
            self.assertFalse(payment in money_payments)

        check_payments = group.get_payments_by_method_name(u'check')
        for payment in [check_payment1, check_payment2]:
            self.assertTrue(payment in check_payments)
        for payment in [money_payment1, money_payment2]:
            self.assertFalse(payment in check_payments)

    def test_get_parent(self):
        sale = self.create_sale()
        purchase = self.create_purchase_order()
        renegotiation = self.create_payment_renegotiation()
        group = self.create_payment_group()
        decrease = self.create_stock_decrease(group=group)
        payment_group = self.create_payment_group()

        self.assertEquals(sale, sale.group.get_parent())
        self.assertEquals(purchase, purchase.group.get_parent())
        self.assertEquals(renegotiation, renegotiation.group.get_parent())
        self.assertEquals(decrease, decrease.group.get_parent())
        self.assertEquals(None, payment_group.get_parent())

    def test_get_description(self):
        sale = self.create_sale()
        purchase = self.create_purchase_order()
        renegotiation = self.create_payment_renegotiation()
        group = self.create_payment_group()
        decrease = self.create_stock_decrease(group=group)

        sale.identifier = 77777
        purchase.identifier = 88888
        renegotiation.identifier = 99999
        decrease.identifier = 12345

        self.assertEquals(sale.group.get_description(), u'sale 77777')
        self.assertEquals(purchase.group.get_description(), u'order 88888')
        self.assertEquals(renegotiation.group.get_description(),
                          u'renegotiation 99999')
        self.assertEquals(decrease.group.get_description(),
                          u'stock decrease 12345')

        callback = lambda g, s: Settable(payment_description='foobar')
        PaymentGroupGetOrderEvent.connect(callback)
        try:
            self.assertEquals(
                self.create_payment_group().get_description(), 'foobar')
        finally:
            PaymentGroupGetOrderEvent.disconnect(callback)

    def test_get_order_object(self):
        sale = self.create_sale()
        purchase = self.create_purchase_order()
        renegotiation = self.create_payment_renegotiation()
        decrease = self.create_stock_decrease(group=self.create_payment_group())

        for obj in [sale, purchase, renegotiation, decrease]:
            self.assertEqual(obj.group.get_order_object(), obj)

        group = self.create_payment_group()
        self.assertIsNone(group.get_order_object())

        obj = object()
        callback = lambda g, s: obj
        PaymentGroupGetOrderEvent.connect(callback)
        try:
            self.assertIs(group.get_order_object(), obj)
        finally:
            PaymentGroupGetOrderEvent.disconnect(callback)
