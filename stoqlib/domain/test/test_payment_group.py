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

from decimal import Decimal

from nose.exc import SkipTest

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.commission import CommissionSource, Commission
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.product import Storable
from stoqlib.domain.sale import Sale
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.parameters import sysparam


class TestPaymentGroup(DomainTest):

    def setUp(self):
        # FIXME: On some tests where PaymentGroup._renegotiation is accessed,
        # a traceback ocours because PaymentRenegotiation were not imported.
        # We can't import it on PaymentGroup since it would generate an import
        # loop error. This is a potential problem on Stoq and we should be
        # fixed there.
        from stoqlib.domain.payment.renegotiation import PaymentRenegotiation
        PaymentRenegotiation # pyflakes

        super(TestPaymentGroup, self).setUp()

    def _payComissionWhenConfirmed(self):
        sysparam(self.trans).update_parameter(
            "SALE_PAY_COMMISSION_WHEN_CONFIRMED",
            "1")
        self.failUnless(
            sysparam(self.trans).SALE_PAY_COMMISSION_WHEN_CONFIRMED)

    def testConfirm(self):
        branch = self.create_branch()
        group = self.create_payment_group()

        method = PaymentMethod.get_by_name(self.trans, 'bill')
        payment1 = method.create_inpayment(group, branch, Decimal(10))
        payment2 = method.create_inpayment(group, branch, Decimal(10))

        payment2.set_pending()
        self.assertEqual(payment1.status, Payment.STATUS_PREVIEW)
        self.assertEqual(payment2.status, Payment.STATUS_PENDING)

        group.confirm()
        self.assertEqual(payment1.status, Payment.STATUS_PENDING)
        self.assertEqual(payment2.status, Payment.STATUS_PENDING)

    def testPay(self):
        branch = self.create_branch()
        group = self.create_payment_group()

        method = PaymentMethod.get_by_name(self.trans, 'bill')
        payment1 = method.create_inpayment(group, branch, Decimal(10))
        payment2 = method.create_inpayment(group, branch, Decimal(10))
        group.confirm()

        self.assertEqual(payment1.status, Payment.STATUS_PENDING)
        self.assertEqual(payment2.status, Payment.STATUS_PENDING)
        payment2.pay()
        self.assertEqual(payment2.status, Payment.STATUS_PAID)

        group.pay()
        self.assertEqual(payment1.status, Payment.STATUS_PAID)
        self.assertEqual(payment2.status, Payment.STATUS_PAID)

    def testPayMoneyPayments(self):
        branch = self.create_branch()
        group = self.create_payment_group()

        method = PaymentMethod.get_by_name(self.trans, 'bill')
        payment1 = method.create_inpayment(group, branch, Decimal(10))
        payment2 = method.create_inpayment(group, branch, Decimal(10))
        method = PaymentMethod.get_by_name(self.trans, 'money')
        method.max_installments = 2
        payment3 = method.create_inpayment(group, branch, Decimal(10))
        payment4 = method.create_inpayment(group, branch, Decimal(10))
        group.confirm()

        self.assertEqual(payment1.status, Payment.STATUS_PENDING)
        self.assertEqual(payment2.status, Payment.STATUS_PENDING)
        self.assertEqual(payment3.status, Payment.STATUS_PENDING)
        self.assertEqual(payment4.status, Payment.STATUS_PENDING)
        payment3.pay()
        self.assertEqual(payment3.status, Payment.STATUS_PAID)

        group.pay_money_payments()
        self.assertEqual(payment1.status, Payment.STATUS_PENDING)
        self.assertEqual(payment2.status, Payment.STATUS_PENDING)
        self.assertEqual(payment3.status, Payment.STATUS_PAID)
        self.assertEqual(payment4.status, Payment.STATUS_PAID)

    def testCancel(self):
        branch = self.create_branch()
        group = self.create_payment_group()

        method = PaymentMethod.get_by_name(self.trans, 'bill')
        payment1 = method.create_inpayment(group, branch, Decimal(10))
        payment2 = method.create_inpayment(group, branch, Decimal(10))
        payment3 = method.create_inpayment(group, branch, Decimal(10))
        group.confirm()

        payment3.pay()
        self.assertEqual(payment1.status, Payment.STATUS_PENDING)
        self.assertEqual(payment2.status, Payment.STATUS_PENDING)
        self.assertEqual(payment3.status, Payment.STATUS_PAID)

        group.cancel()
        self.assertEqual(payment1.status, Payment.STATUS_CANCELLED)
        self.assertEqual(payment2.status, Payment.STATUS_CANCELLED)
        self.assertEqual(payment3.status, Payment.STATUS_PAID)

    def testInstallmentsCommissionAmount(self):
        self._payComissionWhenConfirmed()

        sale = self.create_sale()
        sellable = self.add_product(sale, price=300)
        sale.order()
        CommissionSource(sellable=sellable,
                         direct_value=12,
                         installments_value=5,
                         connection=self.trans)

        method = PaymentMethod.get_by_name(self.trans, 'check')
        method.create_inpayment(sale.group, sale.branch, Decimal(100))
        method.create_inpayment(sale.group, sale.branch, Decimal(200))
        self.failIf(Commission.selectBy(sale=sale, connection=self.trans))
        sale.confirm()
        self.failUnless(Commission.selectBy(sale=sale, connection=self.trans))

        commissions = Commission.selectBy(sale=sale,
                                          connection=self.trans).orderBy('value')
        self.assertEquals(commissions.count(), 2)
        for c in commissions:
            self.failUnless(c.commission_type == Commission.INSTALLMENTS)

        # the first payment represent 1/3 of the total amount
        # 5% of 300: 15,00 * 1/3 => 5,00
        self.assertEquals(commissions[0].value, Decimal("5.00"))
        # the second payment represent 2/3 of the total amount
        # $15 * 2/3 => 10,00
        self.assertEquals(commissions[1].value, Decimal("10.00"))

    def testInstallmentsCommissionAmountWithMultipleItems(self):
        self._payComissionWhenConfirmed()

        sale = self.create_sale()
        sellable = self.add_product(sale, price=300, quantity=3)
        sale.order()

        CommissionSource(sellable=sellable,
                         direct_value=12,
                         installments_value=5,
                         connection=self.trans)

        method = PaymentMethod.get_by_name(self.trans, 'check')
        method.create_inpayment(sale.group, sale.branch, Decimal(300))
        method.create_inpayment(sale.group, sale.branch, Decimal(450))
        method.create_inpayment(sale.group, sale.branch, Decimal(150))
        self.failIf(Commission.selectBy(sale=sale, connection=self.trans))

        sale.confirm()

        commissions = Commission.selectBy(
            sale=sale,
            connection=self.trans).orderBy('value')
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

    def testInstallmentsCommissionAmountWhenSaleReturn(self):
        raise SkipTest("See stoqlib.domain.returnedsale.ReturnedSale.return_ "
                       "and bug 5215.")

        self._payComissionWhenConfirmed()
        sale = self.create_sale()
        sellable = self.create_sellable()
        CommissionSource(sellable=sellable,
                         direct_value=12,
                        installments_value=5,
                         connection=self.trans)

        sale.add_sellable(sellable, quantity=3, price=300)
        product = sellable.product
        storable = Storable(product=product, connection=self.trans)
        storable.increase_stock(100, get_current_branch(self.trans))

        sale.order()
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment1 = method.create_inpayment(sale.group, sale.branch, Decimal(300))
        payment2 = method.create_inpayment(sale.group, sale.branch, Decimal(450))
        payment3 = method.create_inpayment(sale.group, sale.branch, Decimal(150))
        sale.confirm()

        # the commissions are created after the payment
        payment1.pay()
        payment2.pay()
        payment3.pay()

        returned_sale = sale.create_sale_return_adapter()
        returned_sale.return_()
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)

        commissions = Commission.selectBy(sale=sale,
                                          connection=self.trans)
        value = sum([c.value for c in commissions])
        self.assertEqual(value, Decimal(0))
        self.assertEqual(commissions.count(), 4)
        self.failIf(commissions[-1].value >= 0)

    def testGetTotalValue(self):
        method = PaymentMethod.get_by_name(self.trans, 'check')

        # Test for a group in a sale
        # On sale's group, total value should return
        # sum(inpayments.value) - sum(outpayments.value)
        sale = self.create_sale()
        group = sale.group
        self.assertEqual(group.get_total_value(), 0)

        method.create_inpayment(group, sale.branch, Decimal(100))
        self.assertEqual(group.get_total_value(), Decimal(100))

        method.create_inpayment(group, sale.branch, Decimal(200))
        self.assertEqual(group.get_total_value(), Decimal(300))

        method.create_outpayment(group, sale.branch, Decimal(50))
        self.assertEqual(group.get_total_value(), Decimal(250))

        # Test for a group in a purchase
        # On purchase's group, total value should return
        # sum(inpayments.value) - sum(outpayments.value)
        purchase = self.create_purchase_order()
        group = purchase.group
        self.assertEqual(group.get_total_value(), 0)

        method.create_outpayment(group, purchase.branch, Decimal(100))
        self.assertEqual(group.get_total_value(), Decimal(100))

        method.create_outpayment(group, purchase.branch, Decimal(200))
        self.assertEqual(group.get_total_value(), Decimal(300))

        method.create_inpayment(group, purchase.branch, Decimal(50))
        self.assertEqual(group.get_total_value(), Decimal(250))

    def testGetTotalDiscount(self):
        method = PaymentMethod.get_by_name(self.trans, 'check')

        # Test for a group in a sale
        # On sale's group, total value should return
        # sum(inpayments.discount) - sum(outpayments.discount)
        sale = self.create_sale()
        group = sale.group
        self.assertEqual(group.get_total_value(), 0)

        p = method.create_inpayment(group, sale.branch, Decimal(10))
        p.discount = Decimal(10)
        self.assertEqual(group.get_total_discount(), Decimal(10))

        p = method.create_inpayment(group, sale.branch, Decimal(10))
        p.discount = Decimal(20)
        self.assertEqual(group.get_total_discount(), Decimal(30))

        p = method.create_outpayment(group, sale.branch, Decimal(10))
        p.discount = Decimal(10)
        self.assertEqual(group.get_total_discount(), Decimal(20))

        # Test for a group in a purchase
        # On purchase's group, total value should return
        # sum(inpayments.discount) - sum(outpayments.discount)
        purchase = self.create_purchase_order()
        group = purchase.group
        self.assertEqual(group.get_total_value(), 0)

        p = method.create_outpayment(group, purchase.branch, Decimal(10))
        p.discount = Decimal(10)
        self.assertEqual(group.get_total_discount(), Decimal(10))

        p = method.create_outpayment(group, purchase.branch, Decimal(10))
        p.discount = Decimal(20)
        self.assertEqual(group.get_total_discount(), Decimal(30))

        p = method.create_inpayment(group, purchase.branch, Decimal(10))
        p.discount = Decimal(10)
        self.assertEqual(group.get_total_discount(), Decimal(20))

    def testGetTotalInterest(self):
        method = PaymentMethod.get_by_name(self.trans, 'check')

        # Test for a group in a sale
        # On sale's group, total value should return
        # sum(inpayments.interest) - sum(outpayments.interest)
        sale = self.create_sale()
        group = sale.group
        self.assertEqual(group.get_total_value(), 0)

        p = method.create_inpayment(group, sale.branch, Decimal(10))
        p.interest = Decimal(10)
        self.assertEqual(group.get_total_interest(), Decimal(10))

        p = method.create_inpayment(group, sale.branch, Decimal(10))
        p.interest = Decimal(20)
        self.assertEqual(group.get_total_interest(), Decimal(30))

        p = method.create_outpayment(group, sale.branch, Decimal(10))
        p.interest = Decimal(10)
        self.assertEqual(group.get_total_interest(), Decimal(20))

        # Test for a group in a purchase
        # On purchase's group, total value should return
        # sum(inpayments.interest) - sum(outpayments.interest)
        purchase = self.create_purchase_order()
        group = purchase.group
        self.assertEqual(group.get_total_value(), 0)

        p = method.create_outpayment(group, purchase.branch, Decimal(10))
        p.interest = Decimal(10)
        self.assertEqual(group.get_total_interest(), Decimal(10))

        p = method.create_outpayment(group, purchase.branch, Decimal(10))
        p.interest = Decimal(20)
        self.assertEqual(group.get_total_interest(), Decimal(30))

        p = method.create_inpayment(group, purchase.branch, Decimal(10))
        p.interest = Decimal(10)
        self.assertEqual(group.get_total_interest(), Decimal(20))

    def testGetTotalPenalty(self):
        method = PaymentMethod.get_by_name(self.trans, 'check')

        # Test for a group in a sale
        # On sale's group, total value should return
        # sum(inpayments.penalty) - sum(outpayments.penalty)
        sale = self.create_sale()
        group = sale.group
        self.assertEqual(group.get_total_value(), 0)

        p = method.create_inpayment(group, sale.branch, Decimal(10))
        p.penalty = Decimal(10)
        self.assertEqual(group.get_total_penalty(), Decimal(10))

        p = method.create_inpayment(group, sale.branch, Decimal(10))
        p.penalty = Decimal(20)
        self.assertEqual(group.get_total_penalty(), Decimal(30))

        p = method.create_outpayment(group, sale.branch, Decimal(10))
        p.penalty = Decimal(10)
        self.assertEqual(group.get_total_penalty(), Decimal(20))

        # Test for a group in a purchase
        # On purchase's group, total value should return
        # sum(inpayments.penalty) - sum(outpayments.penalty)
        purchase = self.create_purchase_order()
        group = purchase.group
        self.assertEqual(group.get_total_value(), 0)

        p = method.create_outpayment(group, purchase.branch, Decimal(10))
        p.penalty = Decimal(10)
        self.assertEqual(group.get_total_penalty(), Decimal(10))

        p = method.create_outpayment(group, purchase.branch, Decimal(10))
        p.penalty = Decimal(20)
        self.assertEqual(group.get_total_penalty(), Decimal(30))

        p = method.create_inpayment(group, purchase.branch, Decimal(10))
        p.penalty = Decimal(10)
        self.assertEqual(group.get_total_penalty(), Decimal(20))

    def testGetPaymentByMethodName(self):
        group = self.create_payment_group()

        method = PaymentMethod.get_by_name(self.trans, 'money')
        money_payment1 = self.create_payment(method=method)
        group.add_item(money_payment1)
        money_payment2 = self.create_payment(method=method)
        group.add_item(money_payment2)

        method = PaymentMethod.get_by_name(self.trans, 'check')
        check_payment1 = self.create_payment(method=method)
        group.add_item(check_payment1)
        check_payment2 = self.create_payment(method=method)
        group.add_item(check_payment2)

        money_payments = group.get_payments_by_method_name('money')
        for payment in [money_payment1, money_payment2]:
            self.assertTrue(payment in money_payments)
        for payment in [check_payment1, check_payment2]:
            self.assertFalse(payment in money_payments)

        check_payments = group.get_payments_by_method_name('check')
        for payment in [check_payment1, check_payment2]:
            self.assertTrue(payment in check_payments)
        for payment in [money_payment1, money_payment2]:
            self.assertFalse(payment in check_payments)
