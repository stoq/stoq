# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

#
# Copyright (C) 2006-2020 Stoq Tecnologia <http://www.stoq.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
# Author(s): Stoq Team <dev@stoq.com.br>
#

import datetime
from decimal import Decimal

from stoqlib.reporting.transfer import TransferOrderReport
from stoq.lib.gui.search.transfersearch import TransferOrderSearch
from stoqlib.api import api
from stoqlib.lib.dateutils import localdatetime
from stoqlib.database.runtime import get_current_branch, new_store
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.views import ProductFullStockView
from stoqlib.domain.inventory import InventoryItemsView
from stoqlib.domain.payment.card import CreditCardData
from stoqlib.domain.payment.views import InCheckPaymentView, OutCheckPaymentView
from stoqlib.domain.person import Branch, CallsView
from stoqlib.domain.till import Till, TillEntry
from stoqlib.domain.views import SoldItemsByBranchView
from stoqlib.domain.workorder import WorkOrderView
from stoqlib.reporting.callsreport import CallsReport
from stoqlib.reporting.inventory import InventoryReport
from stoqlib.reporting.payment import (BillCheckPaymentReport,
                                       PaymentFlowHistoryReport)
from stoqlib.reporting.test.reporttest import ReportTest
from stoqlib.reporting.product import ProductReport
from stoqlib.reporting.sale import SoldItemsByBranchReport
from stoqlib.reporting.till import TillHistoryReport, TillDailyMovementReport
from stoqlib.reporting.workorder import WorkOrdersReport


class TestReport(ReportTest):
    @classmethod
    def setUpClass(cls):
        # workaround to gui tests closing stores randomly
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.store = new_store()
        self.fake.set_store(self.store)
        self.set_store(self.store)

    def tearDown(self):
        self.store.close()
        self.fake.set_store(None)

    def test_inventory_report(self):
        from stoq.lib.gui.dialogs.inventorydetails import InventoryDetailsDialog

        inventory = self.create_inventory()

        item = self.create_inventory_item(inventory=inventory)
        self.assertFalse(item.is_adjusted)
        item.counted_quantity = item.recorded_quantity - 1
        item.actual_quantity = item.recorded_quantity - 1
        item.cfop_data = self.create_cfop_data()
        item.reason = u"test adjust"
        item.adjust(self.current_user, 13)

        item2 = self.create_inventory_item(inventory=inventory)
        self.assertFalse(item2.is_adjusted)
        item2.counted_quantity = item.recorded_quantity - 1
        item2.actual_quantity = item.recorded_quantity - 1
        item2.cfop_data = self.create_cfop_data()
        item2.reason = u"test adjust2"
        item2.adjust(self.current_user, 13)
        inventory.close()

        dialog = InventoryDetailsDialog(self.store, model=inventory)
        items = list(InventoryItemsView.find_by_inventory(self.store, inventory))
        self._diff_expected(InventoryReport, 'inventory-report', dialog.items_list, items)

    def test_payable_bill_check_payment_report(self):
        from stoq.lib.gui.search.paymentsearch import OutPaymentBillCheckSearch
        search = OutPaymentBillCheckSearch(self.store)

        out_payments = list(self.store.find(OutCheckPaymentView))
        for item in out_payments:
            item.due_date = datetime.date(2007, 1, 1)
            item.open_date = datetime.date(2006, 1, 1)
            search.results.append(item)

        self._diff_expected(BillCheckPaymentReport, 'bill-check-payable-report',
                            search.results, list(search.results))

    def test_receivable_bill_check_payment_report(self):
        from stoq.lib.gui.search.paymentsearch import InPaymentBillCheckSearch
        search = InPaymentBillCheckSearch(self.store)

        in_payments = list(self.store.find(InCheckPaymentView))
        for item in in_payments:
            item.due_date = datetime.date(2007, 1, 1)
            item.open_date = datetime.date(2006, 1, 1)
            search.results.append(item)

        self._diff_expected(BillCheckPaymentReport, 'bill-check-receivable-report',
                            search.results, list(search.results))

    def test_payment_flow_history_report(self):
        from stoq.lib.gui.dialogs.paymentflowhistorydialog import PaymentFlowDay
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

    def test_product_report(self):
        from stoq.lib.gui.search.productsearch import ProductSearch
        search = ProductSearch(self.store)
        search.width = 1000
        # the order_by clause is only needed by the test
        products = self.store.find(ProductFullStockView)
        search.results.clear()
        search.results.search_completed(products)
        self._diff_expected(ProductReport, 'product-report',
                            search.results, list(search.results))

    def test_till_history_report(self):
        from stoq.lib.gui.dialogs.tillhistory import TillHistoryDialog
        dialog = TillHistoryDialog(self.store)

        till = Till(station=self.current_station, branch=self.current_branch, store=self.store)
        till.open_till(self.current_user)

        sale = self.create_sale()
        sellable = self.create_sellable()
        sale.add_sellable(sellable, price=100)
        method = PaymentMethod.get_by_name(self.store, u'bill')
        payment = method.create_payment(sale.branch, sale.station, Payment.TYPE_IN, sale.group,
                                        Decimal(100))
        TillEntry(value=25,
                  identifier=20,
                  description=u"Cash In",
                  payment=None,
                  till=till,
                  branch=till.station.branch,
                  station=self.current_station,
                  date=datetime.date(2007, 1, 1),
                  store=self.store)
        TillEntry(value=-5,
                  identifier=21,
                  description=u"Cash Out",
                  payment=None,
                  till=till,
                  branch=till.station.branch,
                  station=self.current_station,
                  date=datetime.date(2007, 1, 1),
                  store=self.store)

        TillEntry(value=100,
                  identifier=22,
                  description=sellable.get_description(),
                  payment=payment,
                  till=till,
                  branch=till.station.branch,
                  station=self.current_station,
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

    def test_till_daily_movement(self):
        from stoq.lib.gui.dialogs.tilldailymovement import TillDailyMovementDialog
        branch = get_current_branch(self.store)
        branch2 = self.store.find(Branch, Branch.id != branch.id).any()

        # Data used to create the examples
        device = self.create_card_device(description=u'MAQ1')
        provider = self.create_credit_provider(u'PRO1')
        date = datetime.date(2013, 1, 1)

        # First, create one sale
        sale = self.create_sale(branch=branch)
        sellable = self.create_sellable()
        sale.add_sellable(sellable, price=100)
        sale.identifier = 1000
        sale.order(self.current_user)

        # With two card payments
        card_data1 = self.create_credit_card_data(
            device=device,
            provider=provider,
            payment_type=Payment.TYPE_IN,
            payment_value=sale.get_sale_subtotal())
        card_data1.auth = '1234'
        card_data1.card_type = CreditCardData.TYPE_CREDIT
        card_data1.payment.group = sale.group
        card_data1.payment.branch = sale.branch
        card_data1.payment.identifier = 1010

        card_data2 = self.create_credit_card_data(
            device=device,
            provider=provider,
            payment_type=Payment.TYPE_IN,
            payment_value=sale.get_sale_subtotal())
        card_data2.auth = '1234'
        card_data2.card_type = CreditCardData.TYPE_DEBIT

        card_data2.payment.group = sale.group
        card_data2.payment.branch = sale.branch
        card_data2.payment.identifier = 1011

        # Confirm the sale and pay the payments
        sale.confirm(self.current_user)
        sale.group.pay()

        sale.confirm_date = date

        # After calling sale.group.pay(), we need to fix the paid_date
        card_data1.payment.open_date = date
        card_data2.payment.open_date = date

        # create lonely input payment
        payer = self.create_client()
        address = self.create_address()
        address.person = payer.person

        method = PaymentMethod.get_by_name(self.store, u'money')
        group = self.create_payment_group()
        payment_lonely_input = method.create_payment(branch, self.current_station, Payment.TYPE_IN,
                                                     group, Decimal(100))
        payment_lonely_input.description = u"Test receivable account"
        payment_lonely_input.group.payer = payer.person
        payment_lonely_input.set_pending()
        payment_lonely_input.pay()
        payment_lonely_input.identifier = 1001
        payment_lonely_input.open_date = date

        # create purchase payment
        drawee = self.create_supplier()
        address = self.create_address()
        address.person = drawee.person

        method = PaymentMethod.get_by_name(self.store, u'money')
        purchase = self.create_purchase_order(branch=branch)
        purchase.identifier = 12345
        payment = method.create_payment(branch, self.current_station, Payment.TYPE_OUT,
                                        purchase.group, Decimal(100))
        payment.description = u"Test payable account"
        payment.group.recipient = drawee.person
        payment.set_pending()
        payment.pay()
        payment.identifier = 1002
        payment.open_date = date

        # Create a returned sale
        sale = self.create_sale(branch=branch)
        self.add_product(sale)
        self.add_product(sale)
        payment = self.add_payments(sale, date=date)[0]
        sale.order(self.current_user)
        sale.confirm(self.current_user)
        sale.identifier = 23456
        returned_sale = sale.create_sale_return_adapter(self.current_branch, self.current_user,
                                                        self.current_station)
        returned_sale.return_(self.current_user)
        sale.return_date = date
        payment.open_date = date

        payment = returned_sale.group.get_items()[1]
        payment.branch = branch
        payment.identifier = 1003
        payment.pay()
        payment.open_date = date

        # create lonely output payment
        group = self.create_payment_group()
        method = PaymentMethod.get_by_name(self.store, u'money')
        payment = method.create_payment(branch, self.current_station, Payment.TYPE_OUT, group,
                                        Decimal(100))
        payment.branch = branch
        payment.identifier = 1004
        payment.open_date = date
        payment.status = Payment.STATUS_PAID

        # create lonely input payment on a second branch
        payer = self.create_client()
        address = self.create_address()
        address.person = payer.person

        method = PaymentMethod.get_by_name(self.store, u'money')
        group = self.create_payment_group()
        payment_lonely_input = method.create_payment(branch2, self.current_station, Payment.TYPE_IN,
                                                     group, Decimal(100))
        payment_lonely_input.description = u"Other branch lonely payment"
        payment_lonely_input.group.payer = payer.person
        payment_lonely_input.set_pending()
        payment_lonely_input.pay()
        payment_lonely_input.identifier = 1005
        payment_lonely_input.open_date = date

        # Run the dialog the precedes the report
        data = TillDailyMovementDialog(self.store)
        data.model.branch = branch
        data.set_daterange(date, date)
        data.search_button.clicked()

        daterange = (date, None)
        self._diff_expected(TillDailyMovementReport,
                            'till-daily-movement-report', self.store, branch,
                            daterange, data)

        end_date = datetime.date(2013, 6, 1)
        data.set_daterange(date, end_date)
        data.search_button.clicked()
        daterange = (date, end_date)
        self._diff_expected(TillDailyMovementReport,
                            'till-daily-movement-report-end', self.store,
                            branch, daterange, data)

        # Generate report for all branches
        data.model.branch = None
        data.search_button.clicked()
        self._diff_expected(TillDailyMovementReport,
                            'till-daily-movement-all-branches-report-end',
                            self.store, None, daterange, data)

    def test_sold_items_by_branch_report(self):
        from stoq.lib.gui.search.salesearch import SoldItemsByBranchSearch
        search = SoldItemsByBranchSearch(self.store)
        search.width = 1000
        sold_items = self.store.find(SoldItemsByBranchView).order_by(SoldItemsByBranchView.code)
        search.results.add_list(sold_items, clear=True)
        self._diff_expected(SoldItemsByBranchReport, 'sold-items-by-branch-report',
                            search.results, list(search.results))

    def test_calls_report(self):
        from stoq.lib.gui.search.callsearch import CallsSearch
        person = self.create_person()
        self.create_call()
        search = CallsSearch(self.store, person)
        search.width = 1000
        # the order_by clause is only needed by the test
        calls = self.store.find(CallsView)
        search.results.add_list(calls, clear=True)

        self._diff_expected(CallsReport, 'calls-report',
                            search.results, list(search.results), person=person)

    def test_work_orders_report(self):
        from stoq.lib.gui.search.workordersearch import WorkOrderSearch
        for i in range(5):
            wo = self.create_workorder(description=u'Work order %d' % i)
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


class TestTransferReport(ReportTest):
    """Transfer Report tests"""

    def test_transfer_report(self):
        source_branch = self.create_branch(name=u'Stoq Sapatos')
        destination_branch = api.get_current_branch(self.store)
        order = self.create_transfer_order(source_branch=source_branch,
                                           dest_branch=destination_branch)

        for i in range(5):
            self.create_transfer_order_item(order)

        order.send(self.current_user)
        order.identifier = 1337
        order.open_date = localdatetime(2012, 12, 12)
        dialog = TransferOrderSearch(self.store)
        dialog.search.refresh()
        self._diff_expected(TransferOrderReport, 'transfer-report', dialog.results,
                            list(dialog.results))
