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

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.commission import CommissionSource, Commission
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.sale import Sale
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.parameters import sysparam


class TestPaymentGroup(DomainTest):

    def _payComissionWhenConfirmed(self):
        sysparam(self.trans).update_parameter(
            "SALE_PAY_COMMISSION_WHEN_CONFIRMED",
            "1")
        self.failUnless(
            sysparam(self.trans).SALE_PAY_COMMISSION_WHEN_CONFIRMED)

    def testConfirm(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sale.add_sellable(sellable, price=150)

        method = PaymentMethod.get_by_name(self.trans, 'bill')
        payment = method.create_inpayment(sale.group, Decimal(10))
        payment = payment.get_adapted()
        self.assertEqual(payment.status, Payment.STATUS_PREVIEW)
        sale.group.confirm()
        self.assertEqual(payment.status, Payment.STATUS_PENDING)

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
        method.create_inpayment(sale.group, Decimal(100))
        method.create_inpayment(sale.group, Decimal(200))
        self.failIf(Commission.selectBy(sale=sale, connection=self.trans))
        sale.confirm()
        self.failUnless(Commission.selectBy(sale=sale, connection=self.trans))

        commissions = Commission.selectBy(sale=sale,
                                          connection=self.trans)
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
        method.create_inpayment(sale.group, Decimal(300))
        method.create_inpayment(sale.group, Decimal(450))
        method.create_inpayment(sale.group, Decimal(150))
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
        self._payComissionWhenConfirmed()
        sale = self.create_sale()
        sellable = self.create_sellable()
        CommissionSource(sellable=sellable,
                         direct_value=12,
                        installments_value=5,
                         connection=self.trans)

        sale.add_sellable(sellable, quantity=3, price=300)
        product = sellable.product
        product.addFacet(IStorable, connection=self.trans)
        storable = IStorable(sellable.product)
        storable.increase_stock(100, get_current_branch(self.trans))

        sale.order()
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment1 = method.create_inpayment(sale.group, Decimal(300))
        payment2 = method.create_inpayment(sale.group, Decimal(450))
        payment3 = method.create_inpayment(sale.group, Decimal(150))
        sale.confirm()

        # the commissions are created after the payment
        payment1.get_adapted().pay()
        payment2.get_adapted().pay()
        payment3.get_adapted().pay()

        sale.return_(sale.create_sale_return_adapter())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)

        commissions = Commission.selectBy(sale=sale,
                                          connection=self.trans)
        value = sum([c.value for c in commissions])
        self.assertEqual(value, Decimal(0))
        self.assertEqual(commissions.count(), 4)
        self.failIf(commissions[-1].value >= 0)

    def testGetTotalValue(self):
        sale = self.create_sale()
        group = sale.group
        self.assertEqual(group.get_total_value(), 0)

        sellable = self.create_sellable()
        sale.add_sellable(sellable, quantity=3, price=300)
        product = sellable.product
        product.addFacet(IStorable, connection=self.trans)
        storable = IStorable(sellable.product)
        storable.increase_stock(100, get_current_branch(self.trans))
        sale.order()
        method = PaymentMethod.get_by_name(self.trans, 'check')
        method.create_inpayment(sale.group, Decimal(900))
        sale.confirm()
        self.assertEqual(group.get_total_value(), 3 * 300)

    def testGetTotalDiscount(self):
        sale = self.create_sale()
        group = sale.group
        self.assertEqual(group.get_total_discount(), 0)

        sellable = self.create_sellable()
        sale.add_sellable(sellable, quantity=3, price=300)
        product = sellable.product
        product.addFacet(IStorable, connection=self.trans)
        storable = IStorable(sellable.product)
        storable.increase_stock(100, get_current_branch(self.trans))
        sale.order()
        method = PaymentMethod.get_by_name(self.trans, 'check')
        inpayment = method.create_inpayment(sale.group, Decimal(900))
        payment = inpayment.get_adapted()
        payment.discount = 10
        sale.confirm()
        self.assertEqual(group.get_total_discount(), 10)

    def testGetTotalInterest(self):
        sale = self.create_sale()
        group = sale.group
        self.assertEqual(group.get_total_interest(), 0)

        sellable = self.create_sellable()
        sale.add_sellable(sellable, quantity=3, price=300)
        product = sellable.product
        product.addFacet(IStorable, connection=self.trans)
        storable = IStorable(sellable.product)
        storable.increase_stock(100, get_current_branch(self.trans))
        sale.order()
        method = PaymentMethod.get_by_name(self.trans, 'check')
        inpayment = method.create_inpayment(sale.group, Decimal(900))
        payment = inpayment.get_adapted()
        payment.interest = 15
        sale.confirm()
        self.assertEqual(group.get_total_interest(), 15)

    def testGetTotalPenalty(self):
        sale = self.create_sale()
        group = sale.group
        self.assertEqual(group.get_total_penalty(), 0)

        sellable = self.create_sellable()
        sale.add_sellable(sellable, quantity=3, price=300)
        product = sellable.product
        product.addFacet(IStorable, connection=self.trans)
        storable = IStorable(sellable.product)
        storable.increase_stock(100, get_current_branch(self.trans))
        sale.order()
        method = PaymentMethod.get_by_name(self.trans, 'check')
        inpayment = method.create_inpayment(sale.group, Decimal(900))
        payment = inpayment.get_adapted()
        payment.penalty = 25
        sale.confirm()
        self.assertEqual(group.get_total_penalty(), 25)
