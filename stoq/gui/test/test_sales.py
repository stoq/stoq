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
    @mock.patch('stoq.gui.sales.api.new_store')
    def _check_run_dialog(self, action, dialog, other_args, other_kwargs,
                          new_store, run_dialog):
        new_store.return_value = self.store

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.activate(action)
                expected_args = [dialog, self.store]
                if other_args:
                    expected_args.extend(other_args)
                run_dialog.assert_called_once_with(*expected_args, **other_kwargs)

    def testInitial(self):
        app = self.create_app(SalesApp, u'sales')
        for sales in app.results:
            sales.open_date = datetime.datetime(2012, 1, 1)
            sales.confirm_date = datetime.datetime(2012, 2, 3)
            sales.close_date = datetime.datetime(2012, 4, 5)
        self.check_app(app, u'sales')

    def testSelect(self):
        app = self.create_app(SalesApp, u'sales')
        results = app.results
        results.select(results[0])

    @mock.patch('stoq.gui.sales.api.new_store')
    @mock.patch('stoq.gui.sales.SalesApp.run_dialog')
    @mock.patch('stoq.gui.sales.print_sale_invoice')
    @mock.patch('stoq.gui.sales.info')
    def test_print_invoice(self, info, print_sale_invoice, run_dialog,
                           new_store):
        new_store.return_value = self.store

        app = self.create_app(SalesApp, u'sales')
        results = app.results
        results.select(results[0])

        self.activate(app.SalesPrintInvoice)
        info.assert_called_once_with(u"There are no invoice printer configured "
                                     u"for this station")

        layout = InvoiceLayout(description=u'layout',
                               width=10,
                               height=20,
                               store=self.store)
        printer = InvoicePrinter(store=self.store,
                                 description=u'test invoice',
                                 layout=layout,
                                 device_name=u'/dev/lp0',
                                 station=api.get_current_station(self.store))
        self.activate(app.SalesPrintInvoice)
        self.assertEquals(print_sale_invoice.call_count, 1)
        args, kwargs = print_sale_invoice.call_args
        invoice, called_printer = args
        self.assertTrue(isinstance(invoice, SaleInvoice))
        self.assertEquals(printer, called_printer)

        results[0].sale.invoice_number = None
        InvoiceField(layout=layout, x=0, y=0, width=1, height=1,
                     field_name=u'INVOICE_NUMBER',
                     store=self.store)
        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.activate(app.SalesPrintInvoice)
                run_dialog.assert_called_once_with(SaleInvoicePrinterDialog,
                                                   self.store, results[0].sale,
                                                   printer)

    def test_run_dialogs(self):
        app = self.create_app(SalesApp, u'sales')
        results = app.results
        results.select(results[0])

        self._check_run_dialog(app.SaleQuote,
                               SaleQuoteWizard, [], {})
        self._check_run_dialog(app.SearchProduct,
                               ProductSearch, [], {u'hide_footer': True,
                                                   u'hide_toolbar': True,
                                                   u'hide_cost_column': True})
        self._check_run_dialog(app.LoanNew,
                               NewLoanWizard, [], {})
        self._check_run_dialog(app.LoanClose,
                               CloseLoanWizard, [], {})
        self._check_run_dialog(app.LoanSearch,
                               LoanSearch, [], {})
        self._check_run_dialog(app.LoanSearchItems,
                               LoanItemSearch, [], {})
        self._check_run_dialog(app.SearchClient,
                               ClientSearch, [], {u'hide_footer': True})
        self._check_run_dialog(app.SearchCommission,
                               CommissionSearch, [], {})
        self._check_run_dialog(app.SearchClientCalls,
                               ClientCallsSearch, [], {})
        self._check_run_dialog(app.SearchCreditCheckHistory,
                               CreditCheckHistorySearch, [], {})
        self._check_run_dialog(app.SearchService,
                               ServiceSearch, [], {u'hide_toolbar': True})
        self._check_run_dialog(app.SearchSoldItemsByBranch,
                               SoldItemsByBranchSearch, [], {})
        self._check_run_dialog(app.SearchSalesByPaymentMethod,
                               SalesByPaymentMethodSearch, [], {})
        self._check_run_dialog(app.SearchDelivery,
                               DeliverySearch, [], {})
        self._check_run_dialog(app.SearchSalesPersonSales,
                               SalesPersonSalesSearch, [], {})

    @mock.patch('stoqlib.gui.slaves.saleslave.run_dialog')
    @mock.patch('stoq.gui.sales.api.new_store')
    def test_details(self, new_store, run_dialog):
        new_store.return_value = self.store

        app = self.create_app(SalesApp, u'sales')
        results = app.results
        results.select(results[0])

        self.activate(app.Details)
        run_dialog.assert_called_once_with(SaleDetailsDialog, app,
                                           self.store, results[0])

    @mock.patch('stoqlib.gui.slaves.saleslave.api.new_store')
    @mock.patch('stoqlib.gui.slaves.saleslave.run_dialog')
    def test_return(self, run_dialog, new_store):
        new_store.return_value = self.store

        app = self.create_app(SalesApp, u'sales')
        results = app.results
        results.select(results[0])

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.activate(app.Return)
                self.assertEquals(run_dialog.call_count, 1)
                args, kwargs = run_dialog.call_args
                wizard, parent, store, returned_sale = args
                self.assertEquals(wizard, SaleReturnWizard)
                self.assertEquals(parent, app)
                self.assertEquals(store, self.store)
                self.assertEquals(returned_sale.sale, results[0].sale)

    @mock.patch('stoqlib.gui.slaves.saleslave.run_dialog')
    @mock.patch('stoq.gui.sales.api.new_store')
    def test_edit(self, new_store, run_dialog):
        new_store.return_value = self.store

        app = self.create_app(SalesApp, u'sales')
        results = app.results
        results.select(results[0])

        results[0].status = Sale.STATUS_QUOTE
        results[0].sale.status = Sale.STATUS_QUOTE
        app._update_toolbar()

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.activate(app.Edit)
                run_dialog.assert_called_once_with(SaleQuoteWizard,
                                                   app, self.store,
                                                   results[0].sale)

    @mock.patch('stoq.gui.sales.yesno')
    @mock.patch('stoq.gui.sales.api.new_store')
    def test_sales_cancel(self, new_store, yesno):
        new_store.return_value = self.store
        yesno.return_value = True

        app = self.create_app(SalesApp, u'sales')
        results = app.results
        results.select(results[0])

        results[0].status = Sale.STATUS_QUOTE
        app._update_toolbar()

        for item in results[0].sale.get_items():
            item.quantity = 2

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.activate(app.SalesCancel)
                self.assertEquals(results[0].status, Sale.STATUS_CANCELLED)
                yesno.assert_called_once_with(u'This will cancel the selected '
                                              u'quote. Are you sure?',
                                              gtk.RESPONSE_NO,
                                              u"Cancel quote", u"Don't cancel")
