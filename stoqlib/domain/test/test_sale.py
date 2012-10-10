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

from kiwi.currency import currency
from nose.exc import SkipTest

from stoqlib.api import api
from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.commission import CommissionSource, Commission
from stoqlib.domain.fiscal import FiscalBookEntry
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.sale import Sale, SalePaymentMethodView
from stoqlib.domain.till import TillEntry
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.parameters import sysparam


class TestSale(DomainTest):

    def testSalePaymentsOrdered(self):
        sale = self.create_sale()
        self.add_payments(sale, method_type='check', installments=10)
        initial_date = datetime.datetime(2012, 10, 15)
        for i, p in enumerate(sale.payments):
            p.open_date = initial_date - datetime.timedelta(i)

        prev_p = None
        for p in sale.payments:
            if prev_p is None:
                prev_p = p
                continue
            self.assertGreater(p.open_date, prev_p.open_date)
            prev_p = p

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

    def testTotalReturn(self):
        sale = self.create_sale(branch=get_current_branch(self.trans))
        sellable = self.add_product(sale)
        storable = sellable.product_storable
        balance_before_confirm = storable.get_balance_for_branch(sale.branch)

        sale.order()
        self.add_payments(sale)
        sale.confirm()
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_confirm - 1)
        balance_before_return = storable.get_balance_for_branch(sale.branch)

        self.failUnless(sale.can_return())
        returned_sale = sale.create_sale_return_adapter()
        returned_sale.return_()

        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_return + 1)
        # Since this is a total return, balance should be
        # as it wasn't ever confirmed
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_confirm)

    def testPartialReturn(self):
        sale = self.create_sale(branch=get_current_branch(self.trans))
        sellable = self.add_product(sale, quantity=5)
        storable = sellable.product_storable
        balance_before_confirm = storable.get_balance_for_branch(sale.branch)

        sale.order()
        self.add_payments(sale)
        sale.confirm()
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_confirm - 5)
        balance_before_return = storable.get_balance_for_branch(sale.branch)

        self.failUnless(sale.can_return())
        returned_sale = sale.create_sale_return_adapter()
        returned_sale.returned_items[0].quantity = 2
        returned_sale.return_()
        self.failUnless(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_CONFIRMED)
        # 2 of 5 returned
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_return + 2)
        # Since we return 2, it's like we sold 3 instead of 5
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_confirm - 3)

        returned_sale = sale.create_sale_return_adapter()
        # Since we already returned 2 above, this should be created with 3
        self.assertEqual(returned_sale.returned_items[0].quantity, 3)
        # Now this is the final return and will be considered as a total return
        returned_sale.return_()
        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())
        # All 5 returned (2 before plus 3 above)
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_return + 5)
        # Since everything was returned, balance should be
        # as it wasn't ever confirmed
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_confirm)

    def testTotalReturnPaid(self):
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

        returned_sale = sale.create_sale_return_adapter()
        returned_sale.return_()
        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())

        paid_payment = sale.payments[0]
        payment = sale.payments[1]
        self.assertEqual(payment.value, paid_payment.value)
        self.assertEqual(payment.status, Payment.STATUS_PENDING)
        self.assertEqual(payment.method.method_name, 'money')

        fbe = FiscalBookEntry.selectOneBy(
            payment_group=sale.group,
            is_reversal=False,
            connection=self.trans)
        rfbe = FiscalBookEntry.selectOneBy(
            payment_group=sale.group,
            is_reversal=True,
            connection=self.trans)
        # The fiscal entries should be totally reversed
        self.assertEqual(fbe.icms_value - rfbe.icms_value, 0)
        self.assertEqual(fbe.iss_value - rfbe.iss_value, 0)
        self.assertEqual(fbe.ipi_value - rfbe.ipi_value, 0)

    def testPartialReturnPaid(self):
        sale = self.create_sale()
        self.failIf(sale.can_return())

        self.add_product(sale, quantity=2)
        sale.order()
        self.failIf(sale.can_return())

        self.add_payments(sale)
        sale.confirm()
        self.failUnless(sale.can_return())

        sale.set_paid()
        self.failUnless(sale.can_return())

        payment = sale.payments[0]
        self.assertEqual(payment.value, 20)

        returned_sale = sale.create_sale_return_adapter()
        returned_sale.returned_items[0].quantity = 1
        returned_sale.return_()
        self.assertTrue(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_PAID)

        paid_payment = sale.payments[0]
        returned_payment = sale.payments[1]
        self.assertTrue(returned_payment.payment_type, Payment.TYPE_OUT)
        # Since a half of the products were returned, half of the paid
        # value should be reverted to the client
        self.assertEqual(returned_payment.value, paid_payment.value / 2)
        self.assertEqual(returned_payment.status, Payment.STATUS_PENDING)
        self.assertEqual(returned_payment.method.method_name, 'money')

        fbe = FiscalBookEntry.selectOneBy(
            payment_group=sale.group,
            is_reversal=False,
            connection=self.trans)
        rfbe = FiscalBookEntry.selectOneBy(
            payment_group=sale.group,
            is_reversal=True,
            connection=self.trans)
        # Since a half of the products were returned, half of the
        # taxes should be reverted. That is,
        # actual_value - reverted_value = actual_value / 2
        self.assertEqual(fbe.icms_value - rfbe.icms_value,
                         fbe.icms_value / 2)
        self.assertEqual(fbe.iss_value - rfbe.iss_value,
                         fbe.iss_value / 2)
        self.assertEqual(fbe.ipi_value - rfbe.ipi_value,
                         fbe.ipi_value / 2)

    def testTotalReturnNotPaid(self):
        sale = self.create_sale()
        self.failIf(sale.can_return())

        self.add_product(sale, price=300)
        sale.order()
        self.failIf(sale.can_return())

        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment = method.create_inpayment(sale.group, sale.branch, Decimal(300))
        sale.confirm()
        self.failUnless(sale.can_return())

        returned_sale = sale.create_sale_return_adapter()
        returned_sale.return_()
        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())

        returned_amount = 0
        for payment in sale.payments:
            if payment.is_outpayment():
                returned_amount += payment.value
        self.assertEqual(returned_amount, currency(0))

    def testPartialReturnNotPaid(self):
        sale = self.create_sale()
        self.failIf(sale.can_return())

        self.add_product(sale, quantity=2, price=300)
        sale.order()
        self.failIf(sale.can_return())

        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment = method.create_inpayment(sale.group, sale.branch, Decimal(600))
        sale.confirm()
        self.failUnless(sale.can_return())

        returned_sale = sale.create_sale_return_adapter()
        returned_sale.returned_items[0].quantity = 1

        # Mimic what is done on sale return wizard that is to cancel
        # the existing payment and create another one with the new
        # total (in this case, 300)
        method.create_inpayment(sale.group, sale.branch, Decimal(300))
        payment.cancel()

        returned_sale.return_()
        self.failUnless(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_CONFIRMED)

        returned_amount = 0
        for payment in sale.payments:
            if payment.is_outpayment():
                returned_amount += payment.value
        self.assertEqual(returned_amount, currency(0))

    def testTotalReturnNotEntirelyPaid(self):
        sale = self.create_sale()
        self.failIf(sale.can_return())

        self.add_product(sale, price=300)
        sale.order()
        self.failIf(sale.can_return())

        # Add 3 check payments of 100 each
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment1 = method.create_inpayment(sale.group, sale.branch, Decimal(100))
        method.create_inpayment(sale.group, sale.branch, Decimal(100))
        method.create_inpayment(sale.group, sale.branch, Decimal(100))
        sale.confirm()

        # Pay the first payment.
        payment = payment1
        payment.pay()
        self.failUnless(sale.can_return())

        self.failUnless(sale.can_return())
        returned_sale = sale.create_sale_return_adapter()
        returned_sale.return_()
        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())

        returned_amount = 0
        for payment in sale.payments:
            if payment.is_inpayment():
                # At this point, inpayments should be either paid or cancelled
                self.assertFalse(payment.is_pending())
                self.assertTrue(payment.is_paid() or payment.is_cancelled())
            if payment.is_outpayment():
                returned_amount += payment.value
        self.assertEqual(payment.value, returned_amount)

    def testPartialReturnNotEntirelyPaid(self):
        sale = self.create_sale()
        self.failIf(sale.can_return())

        self.add_product(sale, price=300)
        sale.order()
        self.failIf(sale.can_return())

        # Add 3 check payments of 100 each
        method = PaymentMethod.get_by_name(self.trans, 'check')
        payment1 = method.create_inpayment(sale.group, sale.branch, Decimal(100))
        method.create_inpayment(sale.group, sale.branch, Decimal(100))
        method.create_inpayment(sale.group, sale.branch, Decimal(100))
        sale.confirm()

        # Pay the first payment.
        payment = payment1
        payment.pay()
        self.failUnless(sale.can_return())

        self.failUnless(sale.can_return())
        returned_sale = sale.create_sale_return_adapter()
        returned_sale.return_()
        self.failIf(sale.can_return())
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)
        self.assertEqual(sale.return_date.date(), datetime.date.today())

        returned_amount = 0
        for payment in sale.payments:
            if payment.is_inpayment():
                # At this point, inpayments should be either paid or cancelled
                self.assertTrue(payment.is_paid() or payment.is_cancelled())
            if payment.is_outpayment():
                returned_amount += payment.value
        self.assertEqual(payment.value, returned_amount)

    def testTrade(self):
        sale = self.create_sale(branch=get_current_branch(self.trans))
        self.failIf(sale.can_return())

        sellable = self.add_product(sale)
        storable = sellable.product_storable
        balance_before_confirm = storable.get_balance_for_branch(sale.branch)
        sale.order()
        self.failIf(sale.can_return())

        self.add_payments(sale)
        sale.confirm()
        self.failUnless(sale.can_return())
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_confirm - 1)
        balance_before_trade = storable.get_balance_for_branch(sale.branch)

        sale.set_paid()
        self.failUnless(sale.can_return())

        returned_sale = sale.create_sale_return_adapter()
        self.assertRaises(AssertionError, returned_sale.trade)
        new_sale = self.create_sale()
        returned_sale.new_sale = new_sale
        returned_sale.trade()

        group = returned_sale.group
        payment = group.payments[0]
        self.assertTrue(payment.is_paid())
        self.assertEqual(group, new_sale.group)
        self.assertEqual(group.payments.count(), 1)
        self.assertEqual(payment.value, returned_sale.returned_total)
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_trade + 1)
        # Since this is a total return, balance should be
        # as it wasn't ever confirmed
        self.assertEqual(storable.get_balance_for_branch(sale.branch),
                         balance_before_confirm)

    def testCanEdit(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()
        sale.status = Sale.STATUS_QUOTE
        self.failUnless(sale.can_edit())

        self.add_payments(sale)
        sale.confirm()
        self.assertEqual(sale.status, Sale.STATUS_CONFIRMED)
        self.failIf(sale.can_edit())

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
        storable = sellable.product_storable
        inital_quantity = storable.get_balance_for_branch(sale.branch)
        sale.order()
        sale.cancel()
        self.assertEquals(sale.status, Sale.STATUS_CANCELLED)
        final_quantity = storable.get_balance_for_branch(sale.branch)
        self.assertEquals(inital_quantity, final_quantity)

    def testCancelPaid(self):
        sale = self.create_sale()
        sellable = self.add_product(sale)
        storable = sellable.product_storable
        branch = api.get_current_branch(self.trans)
        initial_quantity = storable.get_balance_for_branch(branch)
        sale.order()

        self.add_payments(sale)
        sale.confirm()
        sale.set_paid()
        self.failUnless(sale.can_cancel())

        after_confirmed_quantity = storable.get_balance_for_branch(branch)
        self.assertEquals(initial_quantity - 1, after_confirmed_quantity)

        self.failUnless(sale.can_cancel())
        sale.cancel()
        self.assertEquals(sale.status, Sale.STATUS_CANCELLED)

        final_quantity = storable.get_balance_for_branch(branch)
        self.assertEquals(initial_quantity, final_quantity)

    def testCancelNotPaid(self):
        branch = api.get_current_branch(self.trans)
        sale = self.create_sale()
        sellable = self.add_product(sale, price=300)
        storable = sellable.product_storable
        initial_quantity = storable.get_balance_for_branch(branch)
        sale.order()
        self.failUnless(sale.can_cancel())

        self.add_payments(sale)
        sale.confirm()

        after_confirmed_quantity = storable.get_balance_for_branch(branch)
        self.assertEquals(initial_quantity - 1, after_confirmed_quantity)

        self.failUnless(sale.can_cancel())
        sale.cancel()
        self.assertEquals(sale.status, Sale.STATUS_CANCELLED)

        final_quantity = storable.get_balance_for_branch(branch)
        self.assertEquals(initial_quantity, final_quantity)

    def testCancelQuote(self):
        sale = self.create_sale()
        sellable = self.add_product(sale)
        storable = sellable.product_storable
        inital_quantity = storable.get_balance_for_branch(sale.branch)
        sale.status = Sale.STATUS_QUOTE
        sale.cancel()
        self.assertEquals(sale.status, Sale.STATUS_CANCELLED)
        final_quantity = storable.get_balance_for_branch(sale.branch)
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

    def testCommissionAmountWhenSaleReturnsCompletly(self):
        raise SkipTest("See stoqlib.domain.returned_sale.ReturnedSale.return_ "
                       "and bug 5215.")

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
        returned_sale = sale.create_sale_return_adapter()
        returned_sale.return_()
        self.assertEqual(sale.status, Sale.STATUS_RETURNED)

        commissions = Commission.selectBy(sale=sale,
                                          connection=self.trans)
        value = sum([c.value for c in commissions])
        self.assertEqual(value, Decimal(0))
        self.assertEqual(commissions.count(), 2)
        self.failIf(commissions[-1].value >= 0)

    def testCommissionAmountWhenSaleReturnsPartially(self):
        raise SkipTest("See stoqlib.domain.returnedsale.ReturnedSale.return_ "
                       "and bug 5215.")

        sale = self.create_sale()
        sellable = self.add_product(sale, quantity=2, price=200)
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
        commission_value_before_return = Commission.selectBy(
            connection=self.trans, sale=sale).sum(Commission.value)

        returned_sale = sale.create_sale_return_adapter()
        returned_sale.returned_items[0].quantity = 1
        returned_sale.return_()
        self.assertEqual(sale.status, Sale.STATUS_CONFIRMED)

        commissions = Commission.selectBy(sale=sale,
                                          connection=self.trans)
        # Since we returned half of the products, commission should
        # be reverted by half too
        self.assertEqual(commissions.sum(Commission.value),
                         commission_value_before_return / 2)
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

        payment = self.add_payments(sale, method_type='check')[0]

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
        payment = self.add_payments(sale, method_type='money')[0]
        account = self.create_account()
        payment.method.destination_account = account
        self.failIf(account.transactions)
        sale.confirm()
        self.failUnless(account.transactions)

    def testPayments(self):
        sale = self.create_sale()
        self.add_product(sale)
        sale.order()

        check_payment = self.add_payments(sale, method_type='check')[0]
        self.assertEqual(sale.payments.count(), 1)
        self.assertTrue(check_payment in sale.payments)
        self.assertEqual(sale.group.payments.count(), 1)
        self.assertTrue(check_payment in sale.group.payments)

        check_payment.cancel()
        # Cancelled payments should not appear on sale, just on group
        self.assertEqual(sale.payments.count(), 0)
        self.assertFalse(check_payment in sale.payments)
        self.assertEqual(sale.group.payments.count(), 1)
        self.assertTrue(check_payment in sale.group.payments)

        money_payment = self.add_payments(sale, method_type='money')[0]
        self.assertEqual(sale.payments.count(), 1)
        self.assertTrue(money_payment in sale.payments)
        self.assertEqual(sale.group.payments.count(), 2)
        self.assertTrue(money_payment in sale.group.payments)


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


class TestSalePaymentMethodView(DomainTest):
    def test_with_one_payment_method_sales(self):
        # Let's create two sales: one with money and another with bill.
        sale_money = self.create_sale()
        self.add_product(sale_money)
        self.add_payments(sale_money, method_type='money')

        sale_bill = self.create_sale()
        self.add_product(sale_bill)
        self.add_payments(sale_bill, method_type='bill')

        # If we search for sales that have money payment...
        method = PaymentMethod.get_by_name(self.trans, 'money')
        res = SalePaymentMethodView.select_by_payment_method(
                                                connection=self.trans,
                                                method=method)
        # Initial database already has a money payment
        self.assertEquals(res.count(), 2)
        # Only the first sale should be in the results.
        self.assertTrue(sale_money in [r.sale for r in res])
        self.assertFalse(sale_bill in [r.sale for r in res])

        # We don't have any sale with deposit payment method.
        method = PaymentMethod.get_by_name(self.trans, 'deposit')
        res = SalePaymentMethodView.select_by_payment_method(
                                                connection=self.trans,
                                                method=method)
        self.assertEquals(res.count(), 0)

    def test_with_two_payment_method_sales(self):
        # Create sale with two payments with different methods: money and bill.
        sale_two_methods = self.create_sale()
        self.add_product(sale_two_methods)
        self.add_payments(sale_two_methods, method_type='money')
        self.add_payments(sale_two_methods, method_type='bill')

        # The sale should appear when searching for money payments...
        method = PaymentMethod.get_by_name(self.trans, 'money')
        res = SalePaymentMethodView.select_by_payment_method(
                                                connection=self.trans,
                                                method=method)
        # Initial database already has a money payment
        self.assertEquals(res.count(), 2)
        self.assertTrue(sale_two_methods in [r.sale for r in res])

        # And bill payments...
        method = PaymentMethod.get_by_name(self.trans, 'bill')
        res = SalePaymentMethodView.select_by_payment_method(
                                                connection=self.trans,
                                                method=method)
        # Initial database already has a bill payment
        self.assertEquals(res.count(), 2)
        self.assertTrue(sale_two_methods in [r.sale for r in res])

    def test_with_two_installments_sales(self):
        # A sale that has two installments of the same method should appear only
        # once in the results.
        sale_two_inst = self.create_sale()
        self.add_product(sale_two_inst)
        self.add_payments(sale_two_inst, method_type='deposit', installments=2)

        method = PaymentMethod.get_by_name(self.trans, 'deposit')
        res = SalePaymentMethodView.select_by_payment_method(
                                                connection=self.trans,
                                                method=method)
        self.assertEquals(res.count(), 1)
        self.assertTrue(sale_two_inst in [r.sale for r in res])
