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

from decimal import Decimal

from kiwi.datatypes import currency
from stoqdrivers.enum import TaxType

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.fiscal import IcmsIpiBookEntry
from stoqlib.domain.giftcertificate import GiftCertificate
from stoqlib.domain.interfaces import (IClient,
                                       IIndividual,
                                       IPaymentGroup,
                                       IStorable)
from stoqlib.domain.person import Person
from stoqlib.domain.payment.payment import AbstractPaymentGroup
from stoqlib.domain.payment.methods import CheckPM, MoneyPM
from stoqlib.domain.renegotiation import RenegotiationAdaptToReturnSale
from stoqlib.domain.sale import Sale
from stoqlib.domain.sellable import ASellable, SellableTaxConstant
from stoqlib.exceptions import StoqlibError

from stoqlib.domain.test.domaintest import DomainTest

class TestSale(DomainTest):

    def _create_sale_filled(self):
        # FIXME: Move to examples? create_sale_with_product
        sale = self.create_sale()
        sale.addFacet(IPaymentGroup, connection=self.trans)
        sellable = self.create_sellable()
        sellable.status = ASellable.STATUS_AVAILABLE
        product = sellable.get_adapted()
        storable = product.addFacet(IStorable, connection=self.trans)
        storable.increase_stock(100, get_current_branch(self.trans))
        sellable.add_sellable_item(sale, quantity=5)

        return sale, sellable, storable

    def testGetPercentageValue(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sellable.add_sellable_item(sale, quantity=5)

        self.assertEqual(sale._get_percentage_value(0), currency(0))
        self.assertEqual(sale._get_percentage_value(10), currency(5))

    def testSetDiscountByPercentage(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sellable.add_sellable_item(sale, quantity=5)

        sale._set_discount_by_percentage(10)
        self.assertEqual(sale.discount_value, currency(5))

    def testGetDiscountByPercentage(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sellable.add_sellable_item(sale, quantity=5)

        self.assertEqual(sale._get_discount_by_percentage(), Decimal('0.0'))
        sale._set_discount_by_percentage(10)
        self.assertEqual(sale._get_discount_by_percentage(), 10)

    def testSetSurchargeByPercentage(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sellable.add_sellable_item(sale, quantity=5)

        sale._set_surcharge_by_percentage(10)
        self.assertEqual(sale.surcharge_value, currency(5))

    def testGetSurchargeByPercentage(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sellable.add_sellable_item(sale, quantity=5)

        self.assertEqual(sale._get_surcharge_by_percentage(), currency(0))
        sale._set_surcharge_by_percentage(15)
        self.assertEqual(sale._get_surcharge_by_percentage(), 15)

    def testGetItems(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sellable.add_sellable_item(sale, quantity=5)

        items =  sale.get_items()
        self.assertEqual(items.count(), 1)
        self.assertEqual(sellable, items[0].sellable)

    def testRemoveItem(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sellable.add_sellable_item(sale, quantity=5)

        item = 'test purpose'
        self.failUnlessRaises(TypeError, sale.remove_item, item)
        item = sale.get_items()[0]
        sale.remove_item(item)
        self.assertEqual(sale.get_items().count(), 0)

    def testGetAvailableSales(self):
        sale = self.create_sale()
        sale.set_valid()
        res = Sale.get_available_sales(conn=self.trans, till=sale.till)
        self.assertEqual(res.count(), 1)

    def test_get_status_name(self):
        sale = self.create_sale()
        self.failUnlessRaises(TypeError,
                              sale.get_status_name, 'invalid status')

    def test_add_custom_gift_certificate(self):
        sale = self.create_sale()
        assert isinstance(sale.add_custom_gift_certificate(Decimal(230),
                          u'11').get_adapted(), GiftCertificate)

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

    def testSellItems(self):
        sale, _, storable = self._create_sale_filled()
        sale.sell_items()
        product_item = storable.get_stock_items()[0]
        self.assertEqual(product_item.quantity, 95)

    def testCancelItems(self):
        sale, _, storable = self._create_sale_filled()

        sale.sell_items()
        qty = storable.get_stock_items()[0].quantity
        sale.cancel_items()
        self.assertEqual(qty + 5, storable.get_stock_items()[0].quantity)

    def testCheckClose(self):
        sale = self.create_sale()
        sale.addFacet(IPaymentGroup, connection=self.trans)
        sale_total = sale.get_sale_subtotal()
        check_method = CheckPM.selectOne(connection=self.trans)
        check_method.create_inpayment(IPaymentGroup(sale), sale_total)

        self.failIf(sale.check_close())
        self.failIf(sale.close_date)
        group = sale.check_payment_group()
        group.status = AbstractPaymentGroup.STATUS_CLOSED
        self.failUnlessRaises(ValueError, sale.check_close)

    def testCreateSaleReturnAdapter(self):
        sale = self.create_sale()
        sale.addFacet(IPaymentGroup, connection=self.trans)
        table = RenegotiationAdaptToReturnSale
        count = table.select(connection=self.trans).count()
        sale.create_sale_return_adapter()
        self.assertEqual(count + 1,
                         table.select(connection=self.trans).count())

    def testCancel(self):
        sale = self.create_sale()
        sale.addFacet(IPaymentGroup, connection=self.trans)
        reneg_adapter = sale.create_sale_return_adapter()
        sale.cancel(reneg_adapter)
        self.assertEqual(sale.status, Sale.STATUS_CANCELLED)
        sale.status = Sale.STATUS_ORDER
        self.failUnlessRaises(StoqlibError, sale.cancel, reneg_adapter)

    def testConfirmICMS(self):
        sale, sellable, _ = self._create_sale_filled()

        constant = SellableTaxConstant(description="18",
                                       tax_type=int(TaxType.CUSTOM),
                                       tax_value=18,
                                       connection=self.trans)
        sellable.tax_constant = constant

        method = MoneyPM.selectOne(connection=self.trans)
        method.create_inpayment(IPaymentGroup(sale),
                                sale.get_sale_subtotal())

        self.assertEqual(
            IcmsIpiBookEntry.select(connection=self.trans).count(), 1)
        sale.confirm_sale()
        result = IcmsIpiBookEntry.select(connection=self.trans)
        self.assertEqual(result.count(), 2)
        book_entry = result.orderBy('id')[-1]
        self.assertEqual(book_entry.icms_value, Decimal("9"))
