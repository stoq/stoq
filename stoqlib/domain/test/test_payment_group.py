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
##

from decimal import Decimal

from stoqdrivers.enum import PaymentMethodType

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.commission import CommissionSource, Commission
from stoqlib.domain.interfaces import IPaymentGroup, IStorable
from stoqlib.domain.payment.methods import APaymentMethod
from stoqlib.domain.payment.payment import Payment, PaymentDueDateInfo
from stoqlib.domain.sale import Sale
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.parameters import sysparam

class TestPaymentGroup(DomainTest):
    def testConfirm(self):
        # Actually it tests SaleAdaptToPaymentGroup.confirm
        sale = self.create_sale()
        sellable = self.create_sellable()
        item = sale.add_sellable(sellable, price=150)
        group = sale.addFacet(IPaymentGroup, connection=self.trans)

        method = APaymentMethod.get_by_enum(self.trans, PaymentMethodType.BILL)
        payment = method.create_inpayment(group, Decimal(10))
        payment = payment.get_adapted()
        self.assertEqual(payment.status, Payment.STATUS_PREVIEW)
        group.confirm()
        self.assertEqual(payment.status, Payment.STATUS_PENDING)

    def testInstallmentsCommissionAmount(self):
        sysparam(self.trans).SALE_PAY_COMMISSION_WHEN_CONFIRMED = True
        sale = self.create_sale()
        sellable = self.create_sellable()
        source = CommissionSource(asellable=sellable,
                                  direct_value=12,
                                  installments_value=5,
                                  connection=self.trans)

        item = sale.add_sellable(sellable, price=300)
        sale.order()
        group = sale.addFacet(IPaymentGroup, connection=self.trans)

        method = APaymentMethod.get_by_enum(self.trans,
                                            PaymentMethodType.CHECK)
        payment1 = method.create_inpayment(group, Decimal(100))
        payment2 = method.create_inpayment(group, Decimal(200))
        group.confirm()
        self.failIf(Commission.selectBy(sale=sale, connection=self.trans))

        # the commissions are created after the payment
        payment1.get_adapted().pay()
        payment2.get_adapted().pay()

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
        sysparam(self.trans).SALE_PAY_COMMISSION_WHEN_CONFIRMED = True
        sale = self.create_sale()
        sellable = self.create_sellable()
        source = CommissionSource(asellable=sellable,
                                  direct_value=12,
                                  installments_value=5,
                                  connection=self.trans)

        item = sale.add_sellable(sellable, quantity=3, price=300)
        sale.order()
        group = sale.addFacet(IPaymentGroup, connection=self.trans)

        method = APaymentMethod.get_by_enum(self.trans,
                                            PaymentMethodType.CHECK)
        payment1 = method.create_inpayment(group, Decimal(300))
        payment2 = method.create_inpayment(group, Decimal(450))
        payment3 = method.create_inpayment(group, Decimal(150))
        group.confirm()
        self.failIf(Commission.selectBy(sale=sale, connection=self.trans))

        # the commissions are created after the payment
        payment1.get_adapted().pay()
        payment2.get_adapted().pay()
        payment3.get_adapted().pay()

        commissions = Commission.selectBy(sale=sale,
                                          connection=self.trans)
        self.assertEquals(commissions.count(), 3)
        for c in commissions:
            self.failUnless(c.commission_type == Commission.INSTALLMENTS)

        # the first payment represent 1/3 of the total amount
        # 5% of 900: 45,00 * 1/3 => 15,00 
        self.assertEquals(commissions[0].value, Decimal("15.00"))
        # the second payment represent 1/2 of the total amount
        # 45 / 2 => 22,50
        self.assertEquals(commissions[1].value, Decimal("22.50"))
        # the third payment represent 1/6 of the total amount
        # 45 / 6 => 7.50
        self.assertEquals(commissions[2].value, Decimal("7.50"))

    def testInstallmentsCommissionAmountWhenSaleReturn(self):
        from stoqlib.database.runtime import get_current_branch
        from stoqlib.domain.interfaces import IStorable
        sysparam(self.trans).SALE_PAY_COMMISSION_WHEN_CONFIRMED = True
        sale = self.create_sale()
        sellable = self.create_sellable()
        source = CommissionSource(asellable=sellable,
                                  direct_value=12,
                                  installments_value=5,
                                  connection=self.trans)

        item = sale.add_sellable(sellable, quantity=3, price=300)
        product = sellable.get_adapted()
        product.addFacet(IStorable, connection=self.trans)
        storable = IStorable(sellable)
        storable.increase_stock(100, get_current_branch(self.trans))

        sale.order()
        group = sale.addFacet(IPaymentGroup, connection=self.trans)
        method = APaymentMethod.get_by_enum(self.trans,
                                            PaymentMethodType.CHECK)
        payment1 = method.create_inpayment(group, Decimal(300))
        payment2 = method.create_inpayment(group, Decimal(450))
        payment3 = method.create_inpayment(group, Decimal(150))
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

    def testGetDuePaymentsInfo(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        item = sale.add_sellable(sellable, quantity=2, price=300)
        product = sellable.get_adapted()
        product.addFacet(IStorable, connection=self.trans)
        storable = IStorable(sellable)
        storable.increase_stock(100, get_current_branch(self.trans))
        sale.order()
        group = sale.addFacet(IPaymentGroup, connection=self.trans)
        method = APaymentMethod.get_by_enum(self.trans,
                                            PaymentMethodType.CHECK)
        inpayment1 = method.create_inpayment(group, Decimal(300))
        inpayment2 = method.create_inpayment(group, Decimal(300))
        sale.confirm()

        self.assertEqual(group.get_due_payments_info().count(), 0)
        payment = inpayment1.get_adapted()
        user = self.create_user()
        due_date_info1 = PaymentDueDateInfo(last_due_date=payment.due_date,
                                            payment=payment,
                                            responsible=user,
                                            connection=self.trans)

        due_payments_info = group.get_due_payments_info()
        self.assertEqual(due_payments_info.count(), 1)
        self.assertEqual(due_payments_info[0], due_date_info1)

        payment = inpayment2.get_adapted()
        due_date_info2 = PaymentDueDateInfo(last_due_date=payment.due_date,
                                            payment=payment,
                                            responsible=user,
                                            connection=self.trans)

        due_payments_info = group.get_due_payments_info()
        self.assertEqual(due_payments_info.count(), 2)
        self.assertEqual(due_payments_info[0], due_date_info1)
        self.assertEqual(due_payments_info[1], due_date_info2)
