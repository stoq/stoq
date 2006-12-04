# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
##

from decimal import Decimal
import datetime

from kiwi.datatypes import currency

from stoqlib.database.runtime import (get_current_branch,
                                      get_current_station)
from stoqlib.domain.renegotiation import AbstractRenegotiationAdapter
from stoqlib.domain.giftcertificate import GiftCertificate
from stoqlib.domain.interfaces import (IClient, IEmployee, ISalesPerson,
                                       ICompany, IIndividual,
                                       ISellable, IPaymentGroup, ICheckPM,
                                       IStorable)
from stoqlib.domain.payment.payment import AbstractPaymentGroup
from stoqlib.domain.person import Person, EmployeeRole
from stoqlib.domain.product import Product
from stoqlib.domain.renegotiation import RenegotiationAdaptToReturnSale
from stoqlib.domain.sale import Sale
from stoqlib.domain.sellable import BaseSellableInfo, ASellable, OnSaleInfo
from stoqlib.domain.till import Till
from stoqlib.exceptions import StoqlibError
from stoqlib.lib.defaults import INTERVALTYPE_MONTH
from stoqlib.lib.parameters import sysparam

from stoqlib.domain.test.domaintest import DomainTest

def get_sale(conn, specific=None, employee_role=None):
    # specific: if this parameter is 'np' returns a sale with no payment
    # if no specific=None return a list with a sale, a sellable and a
    # storable.

    # setting up a product
    product = Product(connection=conn)
    base_info = BaseSellableInfo(price=Decimal(10),
                                 connection=conn)
    on_sale_info = OnSaleInfo(on_sale_price=Decimal(10),
                              connection=conn)
    # sellable facet
    sellable = product.addFacet(ISellable, connection=conn,
                                base_sellable_info=base_info,
                                on_sale_info=on_sale_info,
                                status=ASellable.STATUS_AVAILABLE)
    if employee_role == None:
        employee_role = 'desenvolvedor'

    person = Person(name='Jonas', connection=conn)
    person.addFacet(IIndividual, connection=conn)
    role = EmployeeRole(connection=conn, name=employee_role)
    employee = person.addFacet(IEmployee, connection=conn,
                               role=role)
    salesperson = person.addFacet(ISalesPerson, connection=conn)
    company = person.addFacet(ICompany, connection=conn)
    branch = get_current_branch(conn)
    station = get_current_station(conn)
    till = Till(connection=conn, station=station,
                status=Till.STATUS_OPEN)
    renegotiation = AbstractRenegotiationAdapter(connection=conn)
    client = person.addFacet(IClient, connection=conn)
    sale = Sale(coupon_id=123, client=client,
                cfop=sysparam(conn).DEFAULT_SALES_CFOP,
                salesperson=salesperson,
                renegotiation_data=renegotiation,
                till=till, connection=conn)
    sellable.add_sellable_item(sale, quantity=5)

    # storable facet
    storable = product.addFacet(IStorable, connection=conn)
    for stock_item in storable.get_stocks():
        stock_item.quantity = 100
        stock_item.stock_cost = Decimal(10)
        stock_item.logic_quantity = stock_item.quantity

    if specific == 'np':
        return sale

    sale.addFacet(IPaymentGroup, connection=conn,
                  installments_number=4)
    sale.set_valid()
    return [sale, sellable, storable]

class TestSale(DomainTest):

    def setUp(self):
        DomainTest.setUp(self)
        self.sparam = sysparam(self.trans)

    def test_get_percentage_value(self):
        sale = get_sale(self.trans)[0]
        self.assertEqual(sale._get_percentage_value(0), currency(0))
        self.assertEqual(sale._get_percentage_value(10), currency(5))

    def test_set_discount_by_percentage(self):
        sale = get_sale(self.trans)[0]
        sale._set_discount_by_percentage(10)
        self.assertEqual(sale.discount_value, currency(5))

    def test_get_discount_by_percentage(self):
        sale = get_sale(self.trans)[0]
        self.assertEqual(sale._get_discount_by_percentage(), Decimal('0.0'))
        sale._set_discount_by_percentage(10)
        self.assertEqual(sale._get_discount_by_percentage(), 10)

    def test_set_surcharge_by_percentage(self):
        sale = get_sale(self.trans)[0]
        sale._set_surcharge_by_percentage(10)
        self.assertEqual(sale.surcharge_value, currency(5))

    def test_get_surcharge_by_percentage(self):
        sale = get_sale(self.trans)[0]
        self.assertEqual(sale._get_surcharge_by_percentage(), currency(0))
        sale._set_surcharge_by_percentage(15)
        self.assertEqual(sale._get_surcharge_by_percentage(), 15)

    def test_get_items(self):
        usable = get_sale(self.trans)
        sale = usable[0]
        items =  sale.get_items()
        self.assertEqual(items.count(), 1)
        sellable = usable[1]
        self.assertEqual(sellable, items[0].sellable)

    def test_remove_item(self):
        sale = get_sale(self.trans)[0]
        item = 'test purpose'
        self.failUnlessRaises(TypeError, sale.remove_item, item)
        item = sale.get_items()[0]
        sale.remove_item(item)
        self.assertEqual(sale.get_items().count(), 0)

    def test_get_available_sales(self):
        sale = get_sale(self.trans)[0]
        self.assertEqual(sale.get_available_sales(conn=self.trans,
                                                  till=sale.till).count(),
                                                  1)
    def test_get_status_name(self):
        sale = get_sale(self.trans)[0]
        self.failUnlessRaises(TypeError,
                              sale.get_status_name, 'invalid status')

    def test_add_custom_gift_certificate(self):
        sale = get_sale(self.trans)[0]
        assert isinstance(sale.add_custom_gift_certificate(Decimal(230),
                          u'11').get_adapted(), GiftCertificate)

    def test_get_clone(self):
        sale = get_sale(self.trans)[0]
        clone = sale.get_clone()
        self.assertEqual(clone.client, sale.client)
        self.assertEqual(clone.salesperson, sale.salesperson)

    def test_check_payment_group(self):
        sale_no_payment = get_sale(self.trans, 'np')
        sale = get_sale(self.trans, employee_role='Paperback Writer')[0]
        group = sale.check_payment_group()
        assert isinstance(group, Sale.getAdapterClass(IPaymentGroup))
        self.failIf(sale_no_payment.check_payment_group())

    def test_update_client(self):
        person = Person(name='Eliosvaldo', connection=self.trans)
        sale = get_sale(self.trans)[0]
        self.failUnlessRaises(TypeError, sale.update_client, person)
        individual = person.addFacet(IIndividual, connection=self.trans)
        client = person.addFacet(IClient, connection=self.trans)
        sale.update_client(person)
        self.assertEqual(sale.client, client)

    def test_reset_discount_and_surcharge(self):
        sale = get_sale(self.trans)[0]
        sale.reset_discount_and_surcharge()
        self.assertEqual(sale.discount_value, currency(0))
        self.assertEqual(sale.surcharge_value, currency(0))

    def test_sell_items(self):
        usable = get_sale(self.trans)
        sale = usable[0]
        storable = usable[2]
        sale.sell_items()
        product_item = storable.get_stocks()[0]
        self.assertEqual(product_item.quantity, 95)
    test_sell_items.skip = "Quantity"

    def test_cancel_items(self):
        usable = get_sale(self.trans)
        sale = usable[0]
        storable = usable[2]
        sale.sell_items()
        qty = storable.get_stocks()[0].quantity
        sale.cancel_items()
        self.assertEqual(qty + 5, storable.get_stocks()[0].quantity)
    test_cancel_items.skip = "Quantity"

    def test_check_close(self):
        sale = get_sale(self.trans)[0]

        sale_total = sale.get_sale_subtotal()

        pg_facet = IPaymentGroup(sale)
        check_method = ICheckPM(sysparam(self.trans).BASE_PAYMENT_METHOD)
        check_method.setup_inpayments(pg_facet, 4,
                                      datetime.datetime.today(),
                                      INTERVALTYPE_MONTH, 1,
                                      sale_total,
                                      Decimal(0))

        self.failUnless(sale.check_close())
        self.failIf(sale.close_date)
        group = sale.check_payment_group()
        group.status = AbstractPaymentGroup.STATUS_CLOSED
        self.failUnlessRaises(ValueError, sale.check_close)

    test_check_close.skip = "exceptions.AttributeError: 'AbstractCheckBillAdapter' object has no attribute '_SO_class_PaymentDestination'"

    def test_create_sale_return_adapter(self):
        sale = get_sale(self.trans)[0]
        table = RenegotiationAdaptToReturnSale
        count = table.select(connection=self.trans).count()
        sale.create_sale_return_adapter()
        self.assertEqual(count + 1,
                         table.select(connection=self.trans).count())

    def test_cancel(self):
        sale = get_sale(self.trans)[0]
        reneg_adapter = sale.create_sale_return_adapter()
        sale.cancel(reneg_adapter)
        self.assertEqual(sale.status, Sale.STATUS_CANCELLED)
        sale.status = Sale.STATUS_ORDER
        self.failUnlessRaises(StoqlibError, sale.cancel, reneg_adapter)
