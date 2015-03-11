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

import contextlib
import datetime

import mock
from stoqlib.api import api
from stoqlib.domain.sale import Sale, SaleComment, SaleView
from stoqlib.domain.invoice import InvoiceLayout, InvoiceField, InvoicePrinter
from stoqlib.gui.dialogs.invoicedialog import SaleInvoicePrinterDialog
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.editors.saleeditor import SalesPersonEditor
from stoqlib.gui.search.callsearch import ClientCallsSearch
from stoqlib.gui.search.commissionsearch import CommissionSearch
from stoqlib.gui.search.creditcheckhistorysearch import CreditCheckHistorySearch
from stoqlib.gui.search.deliverysearch import DeliverySearch
from stoqlib.gui.search.loansearch import LoanItemSearch, LoanSearch
from stoqlib.gui.search.personsearch import ClientSearch
from stoqlib.gui.search.productsearch import ProductSearch
from stoqlib.gui.search.returnedsalesearch import ReturnedSaleSearch
from stoqlib.gui.search.salesearch import (SoldItemsByBranchSearch,
                                           SalesByPaymentMethodSearch,
                                           UnconfirmedSaleItemsSearch)
from stoqlib.gui.search.salespersonsearch import SalesPersonSalesSearch
from stoqlib.gui.search.searchresultview import SearchResultListView
from stoqlib.gui.search.servicesearch import ServiceSearch
from stoqlib.gui.wizards.loanwizard import NewLoanWizard, CloseLoanWizard
from stoqlib.gui.wizards.salequotewizard import SaleQuoteWizard
from stoqlib.gui.wizards.salereturnwizard import SaleReturnWizard
from stoqlib.lib.invoice import SaleInvoice
from stoqlib.reporting.sale import SalesReport

from stoq.gui.sales import SalesApp
from stoq.gui.test.baseguitest import BaseGUITest


class TestSales(BaseGUITest):
    def _check_run_dialog(self, action, dialog, other_args, other_kwargs):
        with contextlib.nested(
                mock.patch('stoq.gui.sales.SalesApp.run_dialog'),
                mock.patch('stoq.gui.sales.api.new_store'),
                mock.patch.object(self.store, 'commit'),
                mock.patch.object(self.store, 'close')) as ctx:
            new_store = ctx[1]
            new_store.return_value = self.store

            self.activate(action)
            expected_args = [dialog, self.store]
            if other_args:
                expected_args.extend(other_args)

            run_dialog = ctx[0]
            run_dialog.assert_called_once_with(*expected_args, **other_kwargs)

    def test_initial(self):
        app = self.create_app(SalesApp, u'sales')
        for sales in app.results:
            sales.open_date = datetime.datetime(2012, 1, 1)
            sales.confirm_date = datetime.datetime(2012, 2, 3)
            sales.close_date = datetime.datetime(2012, 4, 5)
        self.check_app(app, u'sales')

    def test_select(self):
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

    @mock.patch('stoq.gui.sales.SalesApp.print_report')
    def test_print_report(self, print_report):
        api.sysparam.set_bool(self.store, 'SMART_LIST_LOADING', False)
        app = self.create_app(SalesApp, u'sales')

        self.activate(app.window.Print)
        self.assertEquals(print_report.call_count, 1)

        args, kwargs = print_report.call_args
        report, results, views = args
        self.assertEquals(report, SalesReport)
        self.assertTrue(isinstance(results, SearchResultListView))
        for view in views:
            self.assertTrue(isinstance(view, SaleView))

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
        self._check_run_dialog(app.SearchUnconfirmedSaleItems,
                               UnconfirmedSaleItemsSearch, [], {})
        self._check_run_dialog(app.ReturnedSaleSearch,
                               ReturnedSaleSearch, [], {})
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

    @mock.patch('stoq.gui.financial.SpreadSheetExporter.export')
    def test_export_spreadsheet(self, export):
        app = self.create_app(SalesApp, u'sales')
        self.activate(app.ExportSpreadSheet)
        export.assert_called_once_with(object_list=app.results, name='sales',
                                       filename_prefix='sales')

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

    @mock.patch('stoq.gui.sales.api.new_store')
    def test_change_client(self, new_store):
        with self.sysparam(CHANGE_CLIENT_AFTER_CONFIRMED=True):
            new_store.return_value = self.store

            app = self.create_app(SalesApp, u'sales')
            results = app.results
            results.select(results[0])

            results[0].status = Sale.STATUS_CONFIRMED
            results[0].sale.status = Sale.STATUS_CONFIRMED
            app._update_toolbar()

            with contextlib.nested(
                    mock.patch.object(app, 'run_dialog'),
                    mock.patch.object(self.store, 'commit'),
                    mock.patch.object(self.store, 'close')) as context:
                run_dialog = context[0]
                self.activate(app.ChangeClient)
                args, kwargs = run_dialog.call_args
                self.assertEquals(kwargs['model'], results[0].sale)
                self.assertEquals(kwargs['store'], self.store)
                self.assertEquals(run_dialog.call_count, 1)

    @mock.patch('stoq.gui.sales.api.new_store')
    def test_change_salesperson(self, new_store):
        with self.sysparam(CHANGE_SALESPERSON_AFTER_CONFIRMED=True):
            new_store.return_value = self.store

            app = self.create_app(SalesApp, u'sales')
            results = app.results
            results.select(results[0])

            results[0].status = Sale.STATUS_CONFIRMED
            results[0].sale.status = Sale.STATUS_CONFIRMED
            app._update_toolbar()

            with contextlib.nested(
                    mock.patch.object(app, 'run_dialog'),
                    mock.patch.object(self.store, 'commit'),
                    mock.patch.object(self.store, 'close')) as context:
                run_dialog = context[0]
                self.activate(app.ChangeSalesperson)
                args, kwargs = run_dialog.call_args
                self.assertEquals(kwargs['model'], results[0].sale)
                self.assertEquals(kwargs['store'], self.store)
                run_dialog.assert_called_once_with(SalesPersonEditor,
                                                   store=self.store,
                                                   model=results[0].sale)

    @mock.patch('stoq.gui.sales.api.new_store')
    def test_not_sale_cancel(self, new_store):
        new_store.return_value = self.store

        with self.sysparam(ALLOW_CANCEL_CONFIRMED_SALES=True):
            app = self.create_app(SalesApp, u'sales')
            sale_view = app.results[0]
            app.results.select(sale_view)

            sale_view.status = Sale.STATUS_CONFIRMED
            sale_view.sale.status = Sale.STATUS_CONFIRMED
            app._update_toolbar()

            for item in sale_view.sale.get_items():
                item.quantity = 2

            with contextlib.nested(
                    mock.patch.object(app, 'run_dialog'),
                    mock.patch.object(self.store, 'commit'),
                    mock.patch.object(self.store, 'close')) as context:
                run_dialog = context[0]
                run_dialog.return_value = None
                self.activate(app.SalesCancel)

                msg_text = u"This will cancel the sale, Are you sure?"
                args, kwargs = run_dialog.call_args
                self.assertEquals(args, (NoteEditor, self.store))
                self.assertTrue(isinstance(kwargs['model'], SaleComment))
                self.assertEquals(kwargs['attr_name'], 'comment')
                self.assertEquals(kwargs['message_text'], msg_text)
                self.assertEquals(kwargs['label_text'], u"Reason")
                self.assertEquals(kwargs['mandatory'], True)
                self.assertEquals(kwargs['ok_button_label'], u"Cancel sale")
                self.assertEquals(kwargs['cancel_button_label'], u"Don't cancel")
                self.assertEquals(NoteEditor.retval, None)
                self.assertEquals(run_dialog.call_count, 1)
                self.assertEquals(sale_view.sale.status, Sale.STATUS_CONFIRMED)

    @mock.patch('stoq.gui.sales.api.new_store')
    def test_sales_cancel(self, new_store):
        new_store.return_value = self.store

        app = self.create_app(SalesApp, u'sales')
        sale_view = app.results[0]
        app.results.select(sale_view)

        sale_view.status = Sale.STATUS_QUOTE
        sale_view.sale.status = Sale.STATUS_QUOTE
        app._update_toolbar()

        for item in sale_view.sale.get_items():
            item.quantity = 2

        with contextlib.nested(
                mock.patch.object(app, 'run_dialog'),
                mock.patch.object(self.store, 'commit'),
                mock.patch.object(self.store, 'close')) as context:
            run_dialog = context[0]
            run_dialog.return_value = True
            self.activate(app.SalesCancel)

            msg_text = u"This will cancel the sale, Are you sure?"
            args, kwargs = run_dialog.call_args
            self.assertEquals(args, (NoteEditor, self.store))
            self.assertTrue(isinstance(kwargs['model'], SaleComment))
            self.assertEquals(kwargs['attr_name'], 'comment')
            self.assertEquals(kwargs['message_text'], msg_text)
            self.assertEquals(kwargs['label_text'], u"Reason")
            self.assertEquals(kwargs['mandatory'], True)
            self.assertEquals(kwargs['ok_button_label'], u"Cancel sale")
            self.assertEquals(kwargs['cancel_button_label'], u"Don't cancel")

            self.assertEquals(run_dialog.call_count, 1)
            self.assertEquals(sale_view.sale.status, Sale.STATUS_CANCELLED)

    @mock.patch('stoq.gui.sales.api.new_store')
    def test_confirmed_sales_cancel(self, new_store):
        with self.sysparam(ALLOW_CANCEL_CONFIRMED_SALES=True):
            new_store.return_value = self.store

            app = self.create_app(SalesApp, u'sales')
            sale_view = app.results[0]
            app.results.select(sale_view)

            sale_view.status = Sale.STATUS_CONFIRMED
            sale_view.sale.status = Sale.STATUS_CONFIRMED
            app._update_toolbar()

            for item in sale_view.sale.get_items():
                item.quantity = 2

            with contextlib.nested(
                    mock.patch.object(app, 'run_dialog'),
                    mock.patch.object(self.store, 'commit'),
                    mock.patch.object(self.store, 'close')) as context:
                run_dialog = context[0]
                run_dialog.return_value = True
                self.activate(app.SalesCancel)

                msg_text = u"This will cancel the sale, Are you sure?"
                args, kwargs = run_dialog.call_args
                self.assertEquals(args, (NoteEditor, self.store))
                self.assertTrue(isinstance(kwargs['model'], SaleComment))
                self.assertEquals(kwargs['attr_name'], 'comment')
                self.assertEquals(kwargs['message_text'], msg_text)
                self.assertEquals(kwargs['label_text'], u"Reason")
                self.assertEquals(kwargs['mandatory'], True)
                self.assertEquals(kwargs['ok_button_label'], u"Cancel sale")
                self.assertEquals(kwargs['cancel_button_label'], u"Don't cancel")
                self.assertEquals(run_dialog.call_count, 1)
                self.assertEquals(sale_view.sale.status, Sale.STATUS_CANCELLED)

    @mock.patch('stoq.gui.sales.api.new_store')
    def test_paid_sales_cancel(self, new_store):
        with self.sysparam(ALLOW_CANCEL_CONFIRMED_SALES=True):
            new_store.return_value = self.store

            app = self.create_app(SalesApp, u'sales')
            sale_view = app.results[0]
            app.results.select(sale_view)

            sale_view.status = Sale.STATUS_CONFIRMED
            sale_view.sale.status = Sale.STATUS_CONFIRMED
            app._update_toolbar()

            for item in sale_view.sale.get_items():
                item.quantity = 2

            with contextlib.nested(
                    mock.patch.object(app, 'run_dialog'),
                    mock.patch.object(self.store, 'commit'),
                    mock.patch.object(self.store, 'close')) as context:
                run_dialog = context[0]
                run_dialog.return_value = True
                self.activate(app.SalesCancel)

                msg_text = u"This will cancel the sale, Are you sure?"
                args, kwargs = run_dialog.call_args
                self.assertEquals(args, (NoteEditor, self.store))
                self.assertTrue(isinstance(kwargs['model'], SaleComment))
                self.assertEquals(kwargs['attr_name'], 'comment')
                self.assertEquals(kwargs['message_text'], msg_text)
                self.assertEquals(kwargs['label_text'], u"Reason")
                self.assertEquals(kwargs['mandatory'], True)
                self.assertEquals(kwargs['ok_button_label'], u"Cancel sale")
                self.assertEquals(kwargs['cancel_button_label'], u"Don't cancel")
                self.assertEquals(run_dialog.call_count, 1)
                self.assertEquals(sale_view.sale.status, Sale.STATUS_CANCELLED)
