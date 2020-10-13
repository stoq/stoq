# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2008 Async Open Source <http://www.async.com.br>
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
""" This module test reporties """

import datetime
from decimal import Decimal

from unittest import mock
from nose.exc import SkipTest

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.commission import CommissionSource, CommissionView
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import InPaymentView, OutPaymentView
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.sale import Sale, SaleView, ReturnedSaleItemsView
from stoqlib.domain.service import ServiceView
from stoqlib.domain.views import ProductFullStockView, PendingReturnedSalesView
from stoqlib.lib.dateutils import localdate
from stoqlib.lib.parameters import sysparam
from stoqlib.reporting.paymentsreceipt import InPaymentReceipt, OutPaymentReceipt
from stoqlib.reporting.clientcredit import ClientCreditReport
from stoqlib.reporting.production import ProductionOrderReport
from stoqlib.reporting.purchase import PurchaseQuoteReport
from stoqlib.reporting.service import ServicePriceReport
from stoqlib.reporting.sale import SaleOrderReport, SalesPersonReport
from stoqlib.reporting.salereturn import SaleReturnReport, PendingReturnReceipt
from stoqlib.reporting.test.reporttest import ReportTest
from stoqlib.reporting.product import ProductPriceReport


class TestReport(ReportTest):

    def test_payable_payment_report(self):
        if True:
            raise SkipTest('We need a SearchDialog to test this report.')

        out_payments = list(self.store.find(OutPaymentView))
        for item in out_payments:
            item.payment.due_date = datetime.date(2007, 1, 1)

    def test_receivable_payment_report(self):
        if True:
            raise SkipTest('We need a SearchDialog to test this report.')

        payments = self.store.find(InPaymentView).order_by(InPaymentView.identifier)
        in_payments = list(payments)
        for item in in_payments:
            item.due_date = datetime.date(2007, 1, 1)

    def test_sale_return_report(self):
        today = datetime.date(2013, 1, 1)

        client = self.create_client()

        # new sale
        sale = self.create_sale(branch=get_current_branch(self.store))
        sale.identifier = 123
        sale.client = client
        sale.open_date = today
        sale.discount_value = Decimal('15')
        sale.surcharge_value = Decimal('8')

        # Product
        item_ = self.create_sale_item(sale, product=True)
        self.create_storable(item_.sellable.product, sale.branch, 1)

        # Payments
        payment = self.add_payments(sale, date=today)[0]
        payment.identifier = 999
        payment.group.payer = client.person

        sale.order(self.current_user)
        sale.confirm(self.current_user)
        sale.group.pay()

        sale.confirm_date = today
        payment.paid_date = today

        date = datetime.date(2013, 2, 2)

        # return sale
        returned_sale = sale.create_sale_return_adapter(self.current_branch, self.current_user,
                                                        self.current_station)
        returned_sale.return_(self.current_user)
        returned_sale.return_date = date

        model = self.store.find(SaleView,
                                SaleView.id == returned_sale.sale.id).one()

        returned_items = list(ReturnedSaleItemsView.find_by_sale(self.store,
                                                                 sale))

        self._diff_expected(SaleReturnReport, 'sale-return-report', self.store,
                            client, model, returned_items)

    def test_pending_returned_sale_receipt(self):
        pending_returned_sale = self.create_pending_returned_sale()
        date = datetime.datetime(2015, 3, 6)
        pending_returned_sale.return_date = date
        pending_returned_sale.sale.identifier = 439
        pending_returned_sale.identifier = 58
        model = self.store.find(PendingReturnedSalesView).one()
        self._diff_expected(PendingReturnReceipt, 'pending-returned-sale-receipt',
                            model)

    def test_in_payment_receipt(self):
        payer = self.create_client()
        address = self.create_address()
        address.person = payer.person

        method = PaymentMethod.get_by_name(self.store, u'money')
        group = self.create_payment_group()
        branch = self.create_branch()
        payment = method.create_payment(branch, self.current_station, Payment.TYPE_IN, group,
                                        Decimal(100))
        payment.description = u"Test receivable account"
        payment.group.payer = payer.person
        payment.set_pending()
        payment.pay()
        payment.identifier = 36
        date = datetime.date(2012, 1, 1)

        self._diff_expected(InPaymentReceipt, 'in-payment-receipt-report',
                            payment, None, date)

    def test_out_payment_receipt(self):
        drawee = self.create_supplier()
        address = self.create_address()
        address.person = drawee.person

        method = PaymentMethod.get_by_name(self.store, u'money')
        group = self.create_payment_group()
        branch = self.create_branch()
        payment = method.create_payment(branch, self.current_station, Payment.TYPE_OUT, group,
                                        Decimal(100))
        payment.description = u"Test payable account"
        payment.group.recipient = drawee.person
        payment.set_pending()
        payment.pay()
        payment.identifier = 35
        date = datetime.date(2012, 1, 1)

        self._diff_expected(OutPaymentReceipt, 'out-payment-receipt-report',
                            payment, None, date)

    def test_sales_person_report(self):
        sysparam.set_bool(self.store, 'SALE_PAY_COMMISSION_WHEN_CONFIRMED', True)
        salesperson = self.create_sales_person()
        product = self.create_product(price=100)
        sellable = product.sellable

        sale = self.create_sale()
        sale.salesperson = salesperson
        sale.add_sellable(sellable, quantity=1)

        self.create_storable(product, get_current_branch(self.store), stock=100)

        CommissionSource(sellable=sellable,
                         direct_value=Decimal(10),
                         installments_value=1,
                         store=self.store)

        sale.order(self.current_user)

        method = PaymentMethod.get_by_name(self.store, u'money')
        method.create_payment(sale.branch, sale.station, Payment.TYPE_IN, sale.group,
                              sale.get_sale_subtotal())
        sale.confirm(self.current_user)
        sale.group.pay()

        salesperson = salesperson
        commissions = list(self.store.find(CommissionView))
        commissions[0].identifier = 1
        commissions[1].identifier = 139

        self._diff_expected(SalesPersonReport, 'sales-person-report',
                            commissions, salesperson)

        # Also test when there is no salesperson selected
        self._diff_expected(SalesPersonReport, 'sales-person-report-without-salesperson',
                            commissions, None)

    def test_sale_order_report(self):
        # Simple sellable
        product = self.create_product(price=100)
        sellable = product.sellable
        sellable.unit = self.create_sellable_unit(description=u'UN')
        default_date = datetime.date(2007, 1, 1)

        # Package sellable
        package = self.create_product(description=u'Package', is_package=True)

        first_component = self.create_product(description=u'First Component', stock=50)
        second_component = self.create_product(description=u'Second Component',
                                               stock=50, price=20)
        p_first_component = self.create_product_component(product=package,
                                                          component=first_component,
                                                          component_quantity=2, price=15)
        p_second_component = self.create_product_component(product=package,
                                                           component=second_component,
                                                           price=10)

        # Sale
        sale = self.create_sale()
        sale.open_date = default_date
        # workaround to make the sale order number constant.
        sale.identifier = 9090

        sale.add_sellable(sellable, quantity=1)

        parent = sale.add_sellable(package.sellable, quantity=2)
        parent.price = 0
        sale.add_sellable(first_component.sellable,
                          quantity=parent.quantity * p_first_component.quantity,
                          price=p_first_component.price,
                          parent=parent)
        sale.add_sellable(second_component.sellable,
                          quantity=parent.quantity * p_second_component.quantity,
                          price=p_second_component.price,
                          parent=parent)

        self.create_storable(product, get_current_branch(self.store), stock=100)
        sale.order(self.current_user)
        self._diff_expected(SaleOrderReport, 'sale-order-report', sale)

    def test_sale_order_report_as_quote(self):
        product = self.create_product(price=238)
        sellable = product.sellable
        sellable.unit = self.create_sellable_unit(description=u'UN')
        default_date = datetime.date(2003, 12, 15)
        sale = self.create_sale()
        sale.open_date = default_date
        # workaround to make the sale order number constant.
        sale.identifier = 8686

        sale.add_sellable(sellable, quantity=1)
        self.create_storable(product, get_current_branch(self.store), stock=196)
        sale.status = Sale.STATUS_QUOTE
        sale.expire_date = datetime.date(2003, 12, 20)
        self._diff_expected(SaleOrderReport, 'sale-order-quote-report', sale)

    def test_product_price_report(self):
        # the order_by clause is only needed by the test
        products = self.store.find(ProductFullStockView).order_by(
            ProductFullStockView.code)
        branch_name = self.create_branch(u'Any').person.name
        self._diff_expected(ProductPriceReport, 'product-price-report',
                            list(products), branch_name=branch_name)

    def test_service_price_report(self):
        services = self.store.find(ServiceView).order_by(ServiceView.code)
        self._diff_expected(ServicePriceReport, 'service-price-report',
                            list(services))

    def test_purchase_quote_report(self):
        quoted_item = self.create_purchase_order_item()
        quote = quoted_item.order
        quote.open_date = datetime.date(2007, 1, 1)
        quote.identifier = 28
        quote.status = PurchaseOrder.ORDER_QUOTING
        self._diff_expected(PurchaseQuoteReport, 'purchase-quote-report', quote)

    def test_production_order_report(self):
        order_item = self.create_production_item()
        order = order_item.order
        order.identifier = 28
        service = self.create_production_service()
        service.order = order
        order.open_date = datetime.date(2007, 1, 1)
        self._diff_expected(ProductionOrderReport, 'production-order-report',
                            order)

    @mock.patch('stoqlib.reporting.clientcredit.localtoday')
    def test_client_credit_report(self, localtoday):
        localtoday.return_value = localdate(2013, 1, 1)
        client = self.create_client()
        client.credit_limit = 100
        self._diff_expected(ClientCreditReport, 'client-credit-report', client)
