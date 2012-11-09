# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
import gtk
import mock

from stoqlib.api import api
from stoqlib.domain.sale import Sale
from stoqlib.domain.invoice import InvoiceLayout, InvoiceField, InvoicePrinter
from stoqlib.gui.dialogs.invoicedialog import SaleInvoicePrinterDialog
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.search.callsearch import ClientCallsSearch
from stoqlib.gui.search.commissionsearch import CommissionSearch
from stoqlib.gui.search.creditcheckhistorysearch import CreditCheckHistorySearch
from stoqlib.gui.search.deliverysearch import DeliverySearch
from stoqlib.gui.search.loansearch import LoanItemSearch, LoanSearch
from stoqlib.gui.search.personsearch import ClientSearch
from stoqlib.gui.search.productsearch import ProductSearch
from stoqlib.gui.search.salesearch import (SoldItemsByBranchSearch,
                                           SalesByPaymentMethodSearch)
from stoqlib.gui.search.salespersonsearch import SalesPersonSalesSearch
from stoqlib.gui.search.servicesearch import ServiceSearch
from stoqlib.gui.wizards.loanwizard import NewLoanWizard, CloseLoanWizard
from stoqlib.gui.wizards.salequotewizard import SaleQuoteWizard
from stoqlib.gui.wizards.salereturnwizard import SaleReturnWizard
from stoqlib.lib.invoice import SaleInvoice

from stoq.gui.sales import SalesApp
from stoq.gui.test.baseguitest import BaseGUITest


class TestSales(BaseGUITest):
    @mock.patch('stoq.gui.sales.SalesApp.run_dialog')
    @mock.patch('stoq.gui.sales.api.new_transaction')
    def _check_run_dialog(self, action, dialog, other_args, other_kwargs,
                          new_transaction, run_dialog):
        new_transaction.return_value = self.trans

        with mock.patch.object(self.trans, 'commit'):
            with mock.patch.object(self.trans, 'close'):
                self.activate(action)
                expected_args = [dialog, self.trans]
                if other_args:
                    expected_args.extend(other_args)
                run_dialog.assert_called_once_with(*expected_args, **other_kwargs)

    def testInitial(self):
        app = self.create_app(SalesApp, 'sales')
        for sales in app.main_window.results:
            sales.open_date = datetime.datetime(2012, 1, 1)
            sales.confirm_date = datetime.datetime(2012, 2, 3)
        self.check_app(app, 'sales')

    def testSelect(self):
        app = self.create_app(SalesApp, 'sales')
        results = app.main_window.results
        results.select(results[0])

    @mock.patch('stoq.gui.sales.api.new_transaction')
    @mock.patch('stoq.gui.sales.SalesApp.run_dialog')
    @mock.patch('stoq.gui.sales.print_sale_invoice')
    @mock.patch('stoq.gui.sales.info')
    def test_print_invoice(self, info, print_sale_invoice, run_dialog,
                           new_transaction):
        new_transaction.return_value = self.trans

        app = self.create_app(SalesApp, 'sales')
        results = app.main_window.results
        results.select(results[0])

        self.activate(app.main_window.SalesPrintInvoice)
        info.assert_called_once_with("There are no invoice printer configured "
                                     "for this station")

        layout = InvoiceLayout(description='layout',
                               width=10,
                               height=20,
                               connection=self.trans)
        printer = InvoicePrinter(connection=self.trans,
                                 description='test invoice',
                                 layout=layout,
                                 device_name='/dev/lp0',
                                 station=api.get_current_station(self.trans))
        self.activate(app.main_window.SalesPrintInvoice)
        self.assertEquals(print_sale_invoice.call_count, 1)
        args, kwargs = print_sale_invoice.call_args
        invoice, called_printer = args
        self.assertTrue(isinstance(invoice, SaleInvoice))
        self.assertEquals(printer, called_printer)

        results[0].sale.invoice_number = None
        InvoiceField(layout=layout, x=0, y=0, width=1, height=1,
                             field_name='INVOICE_NUMBER',
                             connection=self.trans)
        with mock.patch.object(self.trans, 'commit'):
            with mock.patch.object(self.trans, 'close'):
                self.activate(app.main_window.SalesPrintInvoice)
                run_dialog.assert_called_once_with(SaleInvoicePrinterDialog,
                                                   self.trans, results[0].sale,
                                                   printer)

    def test_run_dialogs(self):
        app = self.create_app(SalesApp, 'sales')
        results = app.main_window.results
        results.select(results[0])

        self._check_run_dialog(app.main_window.SaleQuote,
                               SaleQuoteWizard, [], {})
        self._check_run_dialog(app.main_window.SearchProduct,
                               ProductSearch, [], {'hide_footer': True,
                                                   'hide_toolbar': True,
                                                   'hide_cost_column': True})
        self._check_run_dialog(app.main_window.LoanNew,
                               NewLoanWizard, [], {})
        self._check_run_dialog(app.main_window.LoanClose,
                               CloseLoanWizard, [], {})
        self._check_run_dialog(app.main_window.LoanSearch,
                               LoanSearch, [], {})
        self._check_run_dialog(app.main_window.LoanSearchItems,
                               LoanItemSearch, [], {})
        self._check_run_dialog(app.main_window.SearchClient,
                               ClientSearch, [], {'hide_footer': True})
        self._check_run_dialog(app.main_window.SearchCommission,
                               CommissionSearch, [], {})
        self._check_run_dialog(app.main_window.SearchClientCalls,
                               ClientCallsSearch, [], {})
        self._check_run_dialog(app.main_window.SearchCreditCheckHistory,
                               CreditCheckHistorySearch, [], {})
        self._check_run_dialog(app.main_window.SearchService,
                               ServiceSearch, [], {'hide_toolbar': True})
        self._check_run_dialog(app.main_window.SearchSoldItemsByBranch,
                               SoldItemsByBranchSearch, [], {})
        self._check_run_dialog(app.main_window.SearchSalesByPaymentMethod,
                               SalesByPaymentMethodSearch, [], {})
        self._check_run_dialog(app.main_window.SearchDelivery,
                               DeliverySearch, [], {})
        self._check_run_dialog(app.main_window.SearchSalesPersonSales,
                               SalesPersonSalesSearch, [], {})

    @mock.patch('stoqlib.gui.slaves.saleslave.run_dialog')
    @mock.patch('stoq.gui.sales.api.new_transaction')
    def test_details(self, new_transaction, run_dialog):
        new_transaction.return_value = self.trans

        app = self.create_app(SalesApp, 'sales')
        results = app.main_window.results
        results.select(results[0])

        self.activate(app.main_window.Details)
        run_dialog.assert_called_once_with(SaleDetailsDialog, app.main_window,
                                           self.trans, results[0])

    @mock.patch('stoqlib.gui.slaves.saleslave.api.new_transaction')
    @mock.patch('stoqlib.gui.slaves.saleslave.run_dialog')
    def test_return(self, run_dialog, new_transaction):
        new_transaction.return_value = self.trans

        app = self.create_app(SalesApp, 'sales')
        results = app.main_window.results
        results.select(results[0])

        with mock.patch.object(self.trans, 'commit'):
            with mock.patch.object(self.trans, 'close'):
                self.activate(app.main_window.Return)
                self.assertEquals(run_dialog.call_count, 1)
                args, kwargs = run_dialog.call_args
                wizard, parent, trans, returned_sale = args
                self.assertEquals(wizard, SaleReturnWizard)
                self.assertEquals(parent, app.main_window)
                self.assertEquals(trans, self.trans)
                self.assertEquals(returned_sale.sale, results[0].sale)

    @mock.patch('stoqlib.gui.slaves.saleslave.run_dialog')
    @mock.patch('stoq.gui.sales.api.new_transaction')
    def test_edit(self, new_transaction, run_dialog):
        new_transaction.return_value = self.trans

        app = self.create_app(SalesApp, 'sales')
        results = app.main_window.results
        results.select(results[0])

        results[0].status = Sale.STATUS_QUOTE
        results[0].sale.status = Sale.STATUS_QUOTE
        app.main_window._update_toolbar()

        with mock.patch.object(self.trans, 'commit'):
            with mock.patch.object(self.trans, 'close'):
                self.activate(app.main_window.Edit)
                run_dialog.assert_called_once_with(SaleQuoteWizard,
                                                   app.main_window, self.trans,
                                                   results[0].sale)

    @mock.patch('stoq.gui.sales.yesno')
    @mock.patch('stoq.gui.sales.api.new_transaction')
    def test_sales_cancel(self, new_transaction, yesno):
        new_transaction.return_value = self.trans
        yesno.return_value = False

        app = self.create_app(SalesApp, 'sales')
        results = app.main_window.results
        results.select(results[0])

        results[0].status = Sale.STATUS_QUOTE
        app.main_window._update_toolbar()

        for item in results[0].sale.get_items():
            item.quantity = 2

        with mock.patch.object(self.trans, 'commit'):
            with mock.patch.object(self.trans, 'close'):
                self.activate(app.main_window.SalesCancel)
                self.assertEquals(results[0].status, Sale.STATUS_CANCELLED)
                yesno.assert_called_once_with('This will cancel the selected '
                                              'quote. Are you sure?',
                                              gtk.RESPONSE_NO, "Don't cancel",
                                              "Cancel quote")
