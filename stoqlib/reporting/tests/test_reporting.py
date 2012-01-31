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
import os
import sys

from twisted.trial.unittest import SkipTest

import stoqlib
from stoqlib.database.runtime import get_current_station
from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.commission import CommissionSource, CommissionView
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.views import (InPaymentView, OutPaymentView,
                                          InCheckPaymentView,
                                          OutCheckPaymentView)
from stoqlib.domain.person import CallsView
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.service import ServiceView
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.till import Till, TillEntry
from stoqlib.domain.views import ProductFullStockView
from stoqlib.gui.base.search import StoqlibSearchSlaveDelegate
from stoqlib.lib.parameters import sysparam
from stoqlib.reporting.payments_receipt import (InPaymentReceipt,
                                               OutPaymentReceipt)
from stoqlib.reporting.calls_report import CallsReport
from stoqlib.reporting.payment import (ReceivablePaymentReport,
                                       PayablePaymentReport,
                                       BillCheckPaymentReport)
from stoqlib.reporting.product import ProductReport, ProductPriceReport
from stoqlib.reporting.production import ProductionOrderReport
from stoqlib.reporting.purchase import PurchaseQuoteReport
from stoqlib.reporting.service import ServicePriceReport
from stoqlib.reporting.sale import SaleOrderReport, SalesPersonReport
from stoqlib.reporting.till import TillHistoryReport
from stoqlib.lib.diffutils import diff_files
from stoqlib.lib.pdf import pdftohtml

_search_restore_columns = StoqlibSearchSlaveDelegate.restore_columns


class TestReport(DomainTest):

    def setUp(self):
        super(TestReport, self).setUp()

        # Some tests in here use searchs to populate the report. Avoid
        # restoring the cache, if any, or we will have inexplicable diff.
        StoqlibSearchSlaveDelegate.restore_columns = lambda s: None

    def tearDown(self):
        super(TestReport, self).tearDown()

        # Restore original restore_columns, to avoid breaking other tests
        StoqlibSearchSlaveDelegate.restore_columns = _search_restore_columns

    def checkPDF(self, report_class, *args, **kwargs):
        exists_pdf = False
        frame = sys._getframe(1)
        filename = "%s.pdf" % (frame.f_code.co_name[4:], )
        filename = os.path.join(os.path.dirname(stoqlib.__file__),
                               "reporting", "tests", "data", filename)
        if os.path.exists(filename):
            original_filename = filename
            exists_pdf = True
            filename = filename + '.tmp'
        report = report_class(filename, *args, **kwargs)
        report.save()

        if exists_pdf:
            path = os.path.split(filename)[0]
            olddir = os.getcwd()
            os.chdir(path)

            for name in (original_filename, filename):
                pdftohtml(name, name)
            try:
                self._comparePDF(original_filename, filename)
            finally:
                os.chdir(olddir)

        if filename.endswith('.tmp'):
            os.unlink(filename)

    def _comparePDF(self, original_filename, filename):
        original_filename_html = "%s.html" % (original_filename, )
        tmp_html = "%s.html" % (filename, )

        out_original_filename = "%s.htm" % (original_filename, )
        out_tmp = "%s.htm" % (filename, )

        input_original = open(original_filename_html)
        input_filename = open(tmp_html)
        output_original = open(out_original_filename, "w")
        output_tmp = open(out_tmp, "w")

        for line in input_original:
            if line.startswith("<META"):
                continue
            output_original.write(line, )
        for line in input_filename:
            if line.startswith("<META"):
                continue
            output_tmp.write(line, )
        for file in (input_original, input_filename, output_original,
                     output_tmp):
            file.close()
        retval = diff_files(out_original_filename, out_tmp)
        os.unlink(tmp_html)
        os.unlink(out_tmp)
        os.unlink(out_original_filename)
        os.unlink(original_filename_html)
        if retval:
            if filename.endswith('.tmp'):
                os.unlink(filename)
            raise AssertionError("Files differ, check output above")

    def testPayablePaymentReport(self):
        raise SkipTest('We need a SearchDialog to test this report.')

        out_payments = list(OutPaymentView.select(connection=self.trans))
        for item in out_payments:
            item.payment.due_date = datetime.date(2007, 1, 1)
        self.checkPDF(PayablePaymentReport, out_payments, date=datetime.date(2007, 1, 1))

    def testReceivablePaymentReport(self):
        raise SkipTest('We need a SearchDialog to test this report.')

        payments = InPaymentView.select(connection=self.trans).orderBy('id')
        in_payments = list(payments)
        for item in in_payments:
            item.due_date = datetime.date(2007, 1, 1)
        self.checkPDF(ReceivablePaymentReport, in_payments, date=datetime.date(2007, 1, 1))

    def testPayableBillCheckPaymentReport(self):
        from stoqlib.gui.search.paymentsearch import OutPaymentBillCheckSearch
        search = OutPaymentBillCheckSearch(self.trans)

        out_payments = list(OutCheckPaymentView.select(connection=self.trans))
        for item in out_payments:
            item.due_date = datetime.date(2007, 1, 1)
            search.results.append(item)

        # Resize the columns in order to generate the correct report.
        for column in search.results.get_columns():
            column.width = 90

        self.checkPDF(BillCheckPaymentReport, search.results, list(search.results),
                      date=datetime.date(2007, 1, 1))

    def testReceivableBillCheckPaymentReport(self):
        from stoqlib.gui.search.paymentsearch import InPaymentBillCheckSearch
        search = InPaymentBillCheckSearch(self.trans)

        in_payments = list(InCheckPaymentView.select(connection=self.trans))
        for item in in_payments:
            item.due_date = datetime.date(2007, 1, 1)
            search.results.append(item)

        # Resize the columns in order to generate the correct report.
        for column in search.results.get_columns():
            column.width = 90

        self.checkPDF(BillCheckPaymentReport, search.results, list(search.results),
                      date=datetime.date(2007, 1, 1))

    def testInPaymentReceipt(self):
        payer = self.create_client()
        address = self.create_address()
        address.person = payer.person

        method = PaymentMethod.get_by_name(self.trans, 'money')
        group = self.create_payment_group()
        inpayment = method.create_inpayment(group, Decimal(100))
        payment = inpayment.get_adapted()

        payment.description = "Test receivable account"
        payment.group.payer = payer.person
        payment.set_pending()
        payment.pay()
        payment.get_payment_number_str = lambda: '00036'
        date = datetime.date(2012, 1, 1)

        self.checkPDF(InPaymentReceipt, payment, order=None, date=date)

    def testOutPaymentReceipt(self):
        drawee = self.create_supplier()
        address = self.create_address()
        address.person = drawee.person

        method = PaymentMethod.get_by_name(self.trans, 'money')
        group = self.create_payment_group()
        outpayment = method.create_outpayment(group, Decimal(100))
        payment = outpayment.get_adapted()

        payment.description = "Test payable account"
        payment.group.recipient = drawee.person
        payment.set_pending()
        payment.pay()
        payment.get_payment_number_str = lambda: '00035'
        date = datetime.date(2012, 1, 1)

        self.checkPDF(OutPaymentReceipt, payment, order=None, date=date)

    def testTransferOrderReceipt(self):
        raise SkipTest('Issues with pdftohtml version.')

        from stoqlib.domain.transfer import TransferOrder, TransferOrderItem
        from stoqlib.reporting.transfer_receipt import TransferOrderReceipt
        orders = list(TransferOrder.select(connection=self.trans))
        items = TransferOrderItem.selectBy(transfer_order=orders[0],
                                           connection=self.trans)
        self.checkPDF(TransferOrderReceipt, orders[0], items)

    def testProductReport(self):
        from stoqlib.gui.search.productsearch import ProductSearch
        search = ProductSearch(self.trans)
        search.width = 1000
        # the orderBy clause is only needed by the test
        products = ProductFullStockView.select(connection=self.trans)\
                                       .orderBy('id')
        search.results.add_list(products, clear=True)
        branch_name = self.create_branch('Any').person.name
        self.checkPDF(ProductReport, search.results, list(search.results),
                      branch_name=branch_name,
                      date=datetime.date(2007, 1, 1))

    def testTillHistoryReport(self):
        from stoqlib.gui.dialogs.tillhistory import TillHistoryDialog
        dialog = TillHistoryDialog(self.trans)

        till = Till(station=get_current_station(self.trans),
                    connection=self.trans)
        till.open_till()

        sale = self.create_sale()
        sellable = self.create_sellable()
        sale.add_sellable(sellable, price=100)
        method = PaymentMethod.get_by_name(self.trans, 'bill')
        payment = method.create_inpayment(sale.group, Decimal(100))
        inpayment = payment.get_adapted()

        TillEntry(value=25, id=20,
                  description="Cash In",
                  payment=None,
                  till=till,
                  date=datetime.date(2007, 1, 1),
                  connection=self.trans)
        TillEntry(value=-5, id=21,
                  description="Cash Out",
                  payment=None,
                  till=till,
                  date=datetime.date(2007, 1, 1),
                  connection=self.trans)

        TillEntry(value=100, id=22,
                  description=sellable.get_description(),
                  payment=inpayment,
                  till=till,
                  date=datetime.date(2007, 1, 1),
                  connection=self.trans)
        till_entry = list(TillEntry.selectBy(connection=self.trans, till=till))
        today = datetime.date.today().strftime('%x')
        for item in till_entry:
            if today in item.description:
                date = datetime.date(2007, 1, 1).strftime('%x')
                item.description = item.description.replace(today, date)

            item.date = datetime.date(2007, 1, 1)
            dialog.results.append(item)

        self.checkPDF(TillHistoryReport, dialog.results, list(dialog.results),
                      date=datetime.date(2007, 1, 1))

    def testSalesPersonReport(self):
        sysparam(self.trans).SALE_PAY_COMMISSION_WHEN_CONFIRMED = 1
        salesperson = self.create_sales_person()
        product = self.create_product(price=100)
        sellable = product.sellable

        sale = self.create_sale()
        sale.salesperson = salesperson
        sale.add_sellable(sellable, quantity=1)

        storable = product.addFacet(IStorable, connection=self.trans)
        storable.increase_stock(100, get_current_branch(self.trans))

        CommissionSource(sellable=sellable,
                         direct_value=Decimal(10),
                         installments_value=1,
                         connection=self.trans)

        sale.order()

        method = PaymentMethod.get_by_name(self.trans, 'money')
        till = Till.get_last_opened(self.trans)
        method.create_inpayment(sale.group,
                                sale.get_sale_subtotal(),
                                till=till)
        sale.confirm()
        sale.set_paid()

        salesperson_name = salesperson.person.name
        commissions = CommissionView.select(connection=self.trans)
        self.checkPDF(SalesPersonReport, list(commissions), salesperson_name,
                      date=datetime.date(2007, 1, 1))

    def testSaleOrderReport(self):
        product = self.create_product(price=100)
        sellable = product.sellable
        default_date = datetime.date(2007, 1, 1)
        sale = self.create_sale()
        sale.open_date = default_date
        # workaround to make the sale order number constant.
        sale.get_order_number_str = lambda: '9090'

        sale.add_sellable(sellable, quantity=1)
        storable = product.addFacet(IStorable, connection=self.trans)
        storable.increase_stock(100, get_current_branch(self.trans))
        sale.order()
        self.checkPDF(SaleOrderReport, sale, date=default_date)

    def testProductPriceReport(self):
        # the orderBy clause is only needed by the test
        products = ProductFullStockView.select(connection=self.trans)\
                                       .orderBy('id')
        branch_name = self.create_branch('Any').person.name
        self.checkPDF(ProductPriceReport, list(products),
                      branch_name=branch_name, date=datetime.date(2007, 1, 1))

    def testServicePriceReport(self):
        services = ServiceView.select(connection=self.trans).orderBy('id')
        self.checkPDF(ServicePriceReport, list(services),
                      date=datetime.date(2007, 1, 1))

    def testPurchaseQuoteReport(self):
        quoted_item = self.create_purchase_order_item()
        quote = quoted_item.order
        quote.open_date = datetime.date(2007, 1, 1)
        quote.get_order_number_str = lambda: '0028'
        quote.status = PurchaseOrder.ORDER_QUOTING
        self.checkPDF(PurchaseQuoteReport, quote, date=quote.open_date)

    def testProductionOrderReport(self):
        order_item = self.create_production_item()
        order = order_item.order
        order.get_order_number = lambda: '0028'
        service = self.create_production_service()
        service.order = order
        order.open_date = datetime.date(2007, 1, 1)
        self.checkPDF(ProductionOrderReport, order, date=order.open_date)

    def testCallsReport(self):
        from stoqlib.gui.search.callsearch import CallsSearch
        person = self.create_person()
        self.create_call()
        search = CallsSearch(self.trans, person)
        search.width = 1000
        # the orderBy clause is only needed by the test
        calls = CallsView.select(connection=self.trans).orderBy('id')
        search.results.add_list(calls, clear=True)
        self.checkPDF(CallsReport, search.results, list(search.results),
                      date=datetime.date(2011, 1, 1), person=person)
