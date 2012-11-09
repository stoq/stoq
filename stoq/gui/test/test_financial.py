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

import gettext
import gtk
import mock

from stoq.gui.financial import FinancialApp
from stoq.gui.test.baseguitest import BaseGUITest
from stoqlib.gui.editors.accounteditor import AccountEditor
from stoqlib.gui.editors.accounttransactioneditor import AccountTransactionEditor
from stoqlib.reporting.payment import AccountTransactionReport

_ = gettext.gettext


class TestFinancial(BaseGUITest):
    def _open_page(self, app, page_name, page_child=None):
        """ This function opens a page and returns it """
        accounts = app.main_window.accounts
        for row in accounts.get_model():
            if row[0].description != page_name:
                continue

            if not page_child:
                accounts.double_click(row.path)
                page_id = app.main_window.notebook.get_current_page()
                page = app.main_window.notebook.get_children()[page_id]
                return page

            for sub in row.iterchildren():
                if sub[0].description != page_child:
                    continue
                accounts.double_click(sub.path)
                page_id = app.main_window.notebook.get_current_page()
                page = app.main_window.notebook.get_children()[page_id]
                return page

    def testInitial(self):
        app = self.create_app(FinancialApp, 'financial')
        self.check_app(app, 'financial')

    def testTransactionPage(self):
        app = self.create_app(FinancialApp, 'financial')

        self._open_page(app, "Banks", "Banco do Brasil")
        self.check_app(app, 'financial-transaction-page')

    def testPayablePage(self):
        app = self.create_app(FinancialApp, 'financial')

        page = self._open_page(app, "Accounts Payable")
        page.search()

    def testReceivablePage(self):
        app = self.create_app(FinancialApp, 'financial')

        page = self._open_page(app, "Accounts Receivable")
        page.search()

    @mock.patch('stoq.gui.financial.run_dialog')
    @mock.patch('stoq.gui.financial.api.new_transaction')
    def test_edit_transaction_dialog(self, new_transaction, run_dialog):
        new_transaction.return_value = self.trans

        at = self.create_account_transaction(self.create_account())
        at.account.description = "The Account"
        at.edited_account = at.account

        run_dialog.return_value = at

        app = self.create_app(FinancialApp, "financial")
        page = self._open_page(app, "The Account")

        olist = page.results
        olist.select(olist[0])

        with mock.patch.object(self.trans, 'commit'):
            with mock.patch.object(self.trans, 'close'):
                self.activate(app.main_window.Edit)
                self.assertEquals(run_dialog.call_count, 1)
                args, kwargs = run_dialog.call_args
                editor, _app, trans, account_transaction, model = args
                self.assertEquals(editor, AccountTransactionEditor)
                self.assertTrue(isinstance(_app, FinancialApp))
                self.assertEquals(trans, self.trans)
                self.assertEquals(account_transaction, at)
                self.assertEquals(model, at.account)

    @mock.patch('stoq.gui.financial.run_dialog')
    @mock.patch('stoq.gui.financial.api.new_transaction')
    def test_add_transaction_dialog(self, new_transaction, run_dialog):
        new_transaction.return_value = self.trans

        at = self.create_account_transaction(self.create_account())
        at.account.description = "The Account"
        at.edited_account = at.account

        run_dialog.return_value = at

        app = self.create_app(FinancialApp, "financial")
        self._open_page(app, "The Account")

        with mock.patch.object(self.trans, 'commit'):
            with mock.patch.object(self.trans, 'close'):
                self.activate(app.main_window.NewTransaction)
                self.assertEquals(run_dialog.call_count, 1)
                args, kwargs = run_dialog.call_args
                editor, _app, trans, account_transaction, model = args
                self.assertEquals(editor, AccountTransactionEditor)
                self.assertTrue(isinstance(_app, FinancialApp))
                self.assertEquals(trans, self.trans)
                self.assertEquals(account_transaction, None)
                self.assertEquals(model, at.account)

    @mock.patch('stoq.gui.financial.print_report')
    def test_print(self, print_report):
        at = self.create_account_transaction(self.create_account())
        at.account.description = "The Account"
        at.edited_account = at.account

        app = self.create_app(FinancialApp, "financial")
        page = self._open_page(app, "The Account")

        self.activate(app.main_window.Print)

        print_report.assert_called_once_with(AccountTransactionReport,
                                             page.results, list(page.results),
                                             account=page.model,
                                             filters=page.get_search_filters())

    @mock.patch('stoq.gui.financial.SpreadSheetExporter.export')
    def test_export_spreadsheet(self, export):
        at = self.create_account_transaction(self.create_account())
        at.account.description = "The Account"
        at.edited_account = at.account

        app = self.create_app(FinancialApp, "financial")
        page = self._open_page(app, "The Account")

        self.activate(app.main_window.ExportSpreadSheet)

        export.assert_called_once_with(object_list=page.results,
                                       name='Financial',
                                       filename_prefix='financial')

    @mock.patch('stoq.gui.financial.yesno')
    @mock.patch('stoq.gui.financial.api.new_transaction')
    def test_delete_account(self, new_transaction, yesno):
        yesno.return_value = False
        new_transaction.return_value = self.trans

        at = self.create_account_transaction(self.create_account())
        at.account.description = "The Account"
        at.edited_account = at.account

        app = self.create_app(FinancialApp, "financial")
        accounts = app.main_window.accounts

        for account in accounts:
            if account.description == at.account.description:
                selected_account = account

        accounts.select(selected_account)
        with mock.patch.object(self.trans, 'commit'):
            with mock.patch.object(self.trans, 'close'):
                self.activate(app.main_window.DeleteAccount)
                yesno.assert_called_once_with('Are you sure you want to remove '
                                              'account "The Account" ?',
                                              gtk.RESPONSE_YES, 'Keep account',
                                              'Remove account')
                self.assertTrue(selected_account not in accounts)

    @mock.patch('stoq.gui.financial.yesno')
    @mock.patch('stoq.gui.financial.api.new_transaction')
    def test_delete_transaction(self, new_transaction, yesno):
        yesno.return_value = False
        new_transaction.return_value = self.trans

        at = self.create_account_transaction(self.create_account())
        at.account.description = "The Account"
        at.edited_account = at.account

        app = self.create_app(FinancialApp, "financial")
        page = self._open_page(app, "The Account")

        olist = page.results
        olist.select(olist[0])

        with mock.patch.object(self.trans, 'commit'):
            with mock.patch.object(self.trans, 'close'):
                self.activate(app.main_window.DeleteTransaction)
                yesno.assert_called_once_with('Are you sure you want to remove '
                                              'transaction "Test Account '
                                              'Transaction" ?',
                                              gtk.RESPONSE_YES,
                                              'Keep transaction',
                                              'Remove transaction')
                self.assertEquals(len(olist), 0)

    @mock.patch('stoq.gui.financial.FinancialApp.run_dialog')
    @mock.patch('stoq.gui.financial.api.new_transaction')
    def test_create_new_account(self, new_transaction, run_dialog):
        new_transaction.return_value = self.trans

        app = self.create_app(FinancialApp, "financial")
        with mock.patch.object(self.trans, 'commit'):
            with mock.patch.object(self.trans, 'close'):
                self.activate(app.main_window.NewAccount)
                run_dialog.assert_called_once_with(AccountEditor, self.trans,
                                                   model=None, parent_account=None)

    @mock.patch('stoq.gui.financial.FinancialApp.run_dialog')
    @mock.patch('stoq.gui.financial.api.new_transaction')
    def test_edit_existing_account(self, new_transaction, run_dialog):
        run_dialog.return_value = True
        new_transaction.return_value = self.trans

        at = self.create_account_transaction(self.create_account())
        at.account.description = "The Account"
        at.edited_account = at.account

        app = self.create_app(FinancialApp, "financial")
        accounts = app.main_window.accounts

        for account in accounts:
            if account.description == at.account.description:
                selected_account = account

        accounts.select(selected_account)
        with mock.patch.object(self.trans, 'commit'):
            with mock.patch.object(self.trans, 'close'):
                self.activate(app.main_window.Edit)
                run_dialog.assert_called_once_with(AccountEditor, self.trans,
                                                   parent_account=None,
                                                   model=at.account)
