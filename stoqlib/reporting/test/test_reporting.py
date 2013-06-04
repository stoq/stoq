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

from nose.exc import SkipTest

from stoqlib.database.runtime import get_current_station
from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.commission import CommissionSource, CommissionView
from stoqlib.domain.sale import Sale
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import (InPaymentView, OutPaymentView,
                                          InCheckPaymentView,
                                          OutCheckPaymentView)
from stoqlib.domain.person import CallsView
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.service import ServiceView
from stoqlib.domain.till import Till, TillEntry
from stoqlib.domain.views import ProductFullStockView
from stoqlib.domain.workorder import WorkOrderView
from stoqlib.lib.parameters import sysparam
from stoqlib.reporting.paymentsreceipt import (InPaymentReceipt,
                                               OutPaymentReceipt)
from stoqlib.reporting.callsreport import CallsReport
from stoqlib.reporting.payment import (BillCheckPaymentReport,
                                       PaymentFlowHistoryReport)
from stoqlib.reporting.product import ProductReport, ProductPriceReport
from stoqlib.reporting.production import ProductionOrderReport
from stoqlib.reporting.purchase import PurchaseQuoteReport
from stoqlib.reporting.service import ServicePriceReport
from stoqlib.reporting.sale import SaleOrderReport, SalesPersonReport
from stoqlib.reporting.till import TillHistoryReport
from stoqlib.reporting.test.reporttest import ReportTest
from stoqlib.reporting.workorder import WorkOrdersReport


class TestReport(ReportTest):

    def testPayablePaymentReport(self):
        raise SkipTest('We need a SearchDialog to test this report.')

        out_payments = list(self.store.find(OutPaymentView))
        for item in out_payments:
            item.payment.due_date = datetime.date(2007, 1, 1)
        # self.checkPDF(PayablePaymentReport, out_payments, date=datetime.date(2007, 1, 1))

    def testReceivablePaymentReport(self):
        raise SkipTest('We need a SearchDialog to test this report.')

        payments = self.store.find(InPaymentView).order_by(InPaymentView.identifier)
        in_payments = list(payments)
        for item in in_payments:
            item.due_date = datetime.date(2007, 1, 1)
        # self.checkPDF(ReceivablePaymentReport, in_payments, date=datetime.date(2007, 1, 1))

    def testPayableBillCheckPaymentReport(self):
        from stoqlib.gui.search.paymentsearch import OutPaymentBillCheckSearch
        search = OutPaymentBillCheckSearch(self.store)

        out_payments = list(self.store.find(OutCheckPaymentView))
        for item in out_payments:
            item.due_date = datetime.date(2007, 1, 1)
            search.results.append(item)

        self._diff_expected(BillCheckPaymentReport, 'bill-check-payable-report',
                            search.results, list(search.results))

    def testReceivableBillCheckPaymentReport(self):
        from stoqlib.gui.search.paymentsearch import InPaymentBillCheckSearch
        search = InPaymentBillCheckSearch(self.store)

        in_payments = list(self.store.find(InCheckPaymentView))
        for item in in_payments:
            item.due_date = datetime.date(2007, 1, 1)
            search.results.append(item)

        self._diff_expected(BillCheckPaymentReport, 'bill-check-receivable-report',
                            search.results, list(search.results))

    def testInPaymentReceipt(self):
        payer = self.create_client()
        address = self.create_address()
        address.person = payer.person

        method = PaymentMethod.get_by_name(self.store, u'money')
        group = self.create_payment_group()
        branch = self.create_branch()
        payment = method.create_payment(Payment.TYPE_IN, group, branch, Decimal(100))
        payment.description = u"Test receivable account"
        payment.group.payer = payer.person
        payment.set_pending()
        payment.pay()
        payment.identifier = 36
        date = datetime.date(2012, 1, 1)

        self._diff_expected(InPaymentReceipt, 'in-payment-receipt-report',
                            payment, None, date)

    def testOutPaymentReceipt(self):
        drawee = self.create_supplier()
        address = self.create_address()
        address.person = drawee.person

        method = PaymentMethod.get_by_name(self.store, u'money')
        group = self.create_payment_group()
        branch = self.create_branch()
        payment = method.create_payment(Payment.TYPE_OUT, group, branch, Decimal(100))
        payment.description = u"Test payable account"
        payment.group.recipient = drawee.person
        payment.set_pending()
        payment.pay()
        payment.identifier = 35
        date = datetime.date(2012, 1, 1)

        self._diff_expected(OutPaymentReceipt, 'out-payment-receipt-report',
                            payment, None, date)

    def testPaymentFlowHistoryReport(self):
        from stoqlib.gui.dialogs.paymentflowhistorydialog import PaymentFlowDay
        # Pending payment
        payment1 = self.create_payment()
        payment1.identifier = 130
        payment1.open_date = datetime.date(2012, 1, 1)
        payment1.due_date = datetime.date(2012, 1, 1)
        payment1.set_pending()

        # Paid payment
        payment2 = self.create_payment()
        payment2.identifier = 131
        payment2.open_date = datetime.date(2012, 1, 1)
        payment2.due_date = datetime.date(2012, 1, 1)
        payment2.value = 10
        payment2.set_pending()
        paid_date = datetime.date(2012, 1, 2)
        payment2.pay(paid_date, paid_value=10)

        start = datetime.date(2012, 1, 1)
        end = datetime.date(2012, 1, 2)
        payments = PaymentFlowDay.get_flow_history(self.store, start, end)

        self._diff_expected(PaymentFlowHistoryReport, 'payment-flow-history',
                            payments)

    def testProductReport(self):
        from stoqlib.gui.search.productsearch import ProductSearch
        search = ProductSearch(self.store)
        search.width = 1000
        # the order_by clause is only needed by the test
        products = self.store.find(ProductFullStockView)
        search.results.add_list(products, clear=True)
        self._diff_expected(ProductReport, 'product-report',
                            search.results, list(search.results))

    def testTillHistoryReport(self):
        from stoqlib.gui.dialogs.tillhistory import TillHistoryDialog
        dialog = TillHistoryDialog(self.store)

        till = Till(station=get_current_station(self.store),
                    store=self.store)
        till.open_till()

        sale = self.create_sale()
        sellable = self.create_sellable()
        sale.add_sellable(sellable, price=100)
        method = PaymentMethod.get_by_name(self.store, u'bill')
        payment = method.create_payment(Payment.TYPE_IN, sale.group, sale.branch, Decimal(100))
        TillEntry(value=25,
                  identifier=20,
                  description=u"Cash In",
                  payment=None,
                  till=till,
                  branch=till.station.branch,
                  date=datetime.date(2007, 1, 1),
                  store=self.store)
        TillEntry(value=-5,
                  identifier=21,
                  description=u"Cash Out",
                  payment=None,
                  till=till,
                  branch=till.station.branch,
                  date=datetime.date(2007, 1, 1),
                  store=self.store)

        TillEntry(value=100,
                  identifier=22,
                  description=sellable.get_description(),
                  payment=payment,
                  till=till,
                  branch=till.station.branch,
                  date=datetime.date(2007, 1, 1),
                  store=self.store)
        till_entry = list(self.store.find(TillEntry, till=till))
        today = datetime.date.today().strftime('%x')
        for item in till_entry:
            if today in item.description:
                date = datetime.date(2007, 1, 1).strftime('%x')
                item.description = item.description.replace(today, date)

            item.date = datetime.date(2007, 1, 1)
            dialog.results.append(item)

        self._diff_expected(TillHistoryReport, 'till-history-report',
                            dialog.results, list(dialog.results))

    def testSalesPersonReport(self):
        sysparam(self.store).SALE_PAY_COMMISSION_WHEN_CONFIRMED = 1
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

        sale.order()

        method = PaymentMethod.get_by_name(self.store, u'money')
        till = Till.get_last_opened(self.store)
        method.create_payment(Payment.TYPE_IN, sale.group, sale.branch,
                              sale.get_sale_subtotal(),
                              till=till)
        sale.confirm()
        sale.group.pay()

        salesperson_name = salesperson.person.name
        commissions = list(self.store.find(CommissionView))
        commissions[0].identifier = 1
        commissions[1].identifier = 139

        self._diff_expected(SalesPersonReport, 'sales-person-report', commissions,
                            salesperson_name)

    def testSaleOrderReport(self):
        product = self.create_product(price=100)
        sellable = product.sellable
        default_date = datetime.date(2007, 1, 1)
        sale = self.create_sale()
        sale.open_date = default_date
        # workaround to make the sale order number constant.
        sale.identifier = 9090

        sale.add_sellable(sellable, quantity=1)
        self.create_storable(product, get_current_branch(self.store), stock=100)
        sale.order()
        self._diff_expected(SaleOrderReport, 'sale-order-report', sale)

    def testSaleOrderReportAsQuote(self):
        product = self.create_product(price=238)
        sellable = product.sellable
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

    def testProductPriceReport(self):
        # the order_by clause is only needed by the test
        products = self.store.find(ProductFullStockView).order_by(
            ProductFullStockView.code)
        branch_name = self.create_branch(u'Any').person.name
        self._diff_expected(ProductPriceReport, 'product-price-report',
                            list(products), branch_name=branch_name)

    def testServicePriceReport(self):
        services = self.store.find(ServiceView).order_by(ServiceView.code)
        self._diff_expected(ServicePriceReport, 'service-price-report',
                            list(services))

    def testPurchaseQuoteReport(self):
        quoted_item = self.create_purchase_order_item()
        quote = quoted_item.order
        quote.open_date = datetime.date(2007, 1, 1)
        quote.identifier = 28
        quote.status = PurchaseOrder.ORDER_QUOTING
        self._diff_expected(PurchaseQuoteReport, 'purchase-quote-report', quote)

    def testProductionOrderReport(self):
        order_item = self.create_production_item()
        order = order_item.order
        order.identifier = 28
        service = self.create_production_service()
        service.order = order
        order.open_date = datetime.date(2007, 1, 1)
        self._diff_expected(ProductionOrderReport, 'production-order-report',
                            order)

    def testCallsReport(self):
        from stoqlib.gui.search.callsearch import CallsSearch
        person = self.create_person()
        self.create_call()
        search = CallsSearch(self.store, person)
        search.width = 1000
        # the order_by clause is only needed by the test
        calls = self.store.find(CallsView)
        search.results.add_list(calls, clear=True)

        self._diff_expected(CallsReport, 'calls-report',
                            search.results, list(search.results), person=person)

    def testWorkOrdersReport(self):
        from stoqlib.gui.search.workordersearch import WorkOrderSearch
        for i in range(5):
            wo = self.create_workorder(u'Work order %d' % i)
            sellable = self.create_sellable(description=u'Sellable %d' % i)
            wo.client = self.create_client(u'Client %d' % i)
            wo.add_sellable(sellable, price=10 * i)
            wo.identifier = 666 + i
            wo.open_date = datetime.date(2007, 8, 4)

        search = WorkOrderSearch(self.store)
        workorders = self.store.find(
            WorkOrderView).order_by(WorkOrderView.identifier)
        search.results.add_list(workorders, clear=True)

        self._diff_expected(WorkOrdersReport, 'workorders-report',
                            search.results, list(search.results))
