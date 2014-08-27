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

import gtk
import mock

from stoq.gui.financial import FinancialApp
from stoq.gui.test.baseguitest import BaseGUITest
from stoqlib.domain.account import AccountTransaction
from stoqlib.gui.editors.accounteditor import AccountEditor
from stoqlib.gui.editors.accounttransactioneditor import AccountTransactionEditor
from stoqlib.reporting.payment import AccountTransactionReport


class TestFinancial(BaseGUITest):
    def _open_page(self, app, page_name, page_child=None):
        """ This function opens a page and returns it """

        def activate(row):
            accounts.double_click(row.path)
            return app.get_current_page()

        accounts = app.accounts
        for row in accounts.get_model():
            if row[0].description != page_name:
                continue

            if not page_child:
                return activate(row)

            for sub in row.iterchildren():
                if sub[0].description == page_child:
                    return activate(sub)

    def test_initial(self):
        app = self.create_app(FinancialApp, u'financial')
        self.check_app(app, u'financial')

    def test_transaction_page(self):
        app = self.create_app(FinancialApp, u'financial')

        self._open_page(app, u"Banks", u"Banco do Brasil")
        self.check_app(app, u'financial-transaction-page')

    def test_payable_page(self):
        app = self.create_app(FinancialApp, u'financial')

        page = self._open_page(app, u"Accounts Payable")
        page.search.search()

    def test_receivable_page(self):
        app = self.create_app(FinancialApp, u'financial')

        page = self._open_page(app, u"Accounts Receivable")
        page.search.search()

    @mock.patch('stoq.gui.financial.run_dialog')
    @mock.patch('stoq.gui.financial.api.new_store')
    def test_edit_transaction_dialog(self, new_store, run_dialog):
        new_store.return_value = self.store

        at = self.create_account_transaction(self.create_account())
        at.account.description = u"The Account"
        at.edited_account = at.account

        run_dialog.return_value = at

        app = self.create_app(FinancialApp, u"financial")
        page = self._open_page(app, u"The Account")

        olist = page.result_view
        olist.select(olist[0])

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.activate(app.Edit)
                self.assertEquals(run_dialog.call_count, 1)
                args, kwargs = run_dialog.call_args
                editor, _app, store, account_transaction, model = args
                self.assertEquals(editor, AccountTransactionEditor)
                self.assertTrue(isinstance(_app, FinancialApp))
                self.assertEquals(store, self.store)
                self.assertEquals(account_transaction, at)
                self.assertEquals(model, at.account)

    @mock.patch('stoq.gui.financial.run_dialog')
    @mock.patch('stoq.gui.financial.api.new_store')
    def test_add_transaction_dialog(self, new_store, run_dialog):
        new_store.return_value = self.store

        at = self.create_account_transaction(self.create_account())
        at.account.description = u"The Account"
        at.edited_account = at.account

        run_dialog.return_value = at

        app = self.create_app(FinancialApp, u"financial")
        self._open_page(app, u"The Account")

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.activate(app.NewTransaction)
                self.assertEquals(run_dialog.call_count, 1)
                args, kwargs = run_dialog.call_args
                editor, _app, store, account_transaction, model = args
                self.assertEquals(editor, AccountTransactionEditor)
                self.assertTrue(isinstance(_app, FinancialApp))
                self.assertEquals(store, self.store)
                self.assertEquals(account_transaction, None)
                self.assertEquals(model, at.account)

    @mock.patch('stoq.gui.financial.yesno')
    @mock.patch('stoq.gui.financial.api.new_store')
    def test_transaction_with_same_accounts(self, new_store, yesno):
        # When we have an account transaction with source account equal to destination,
        # the Financial app must show a new transaction, with the same data of
        # original transaction, but with inverted value.

        # Create a new account transaction
        new_store.return_value = self.store
        account = self.create_account(u"Account")
        original_transaction = self.create_account_transaction(account, value=100)
        original_transaction.description = u"Test transaction"

        app = self.create_app(FinancialApp, u"financial")
        page = self._open_page(app, u"Account")
        accounts = page.result_view
        original = self.store.find(AccountTransaction, account=account).count()
        self.assertEquals(original, 1)
        self.assertEquals(len(accounts), 1)

        # Check the new transaction is shown.
        original_transaction.source_account = account
        page.refresh()
        self.assertEquals(len(accounts), 2)
        reversed_transaction = accounts[1]
        self.assertEquals(reversed_transaction.description, original_transaction.description)
        self.assertEquals(reversed_transaction.value, -100)

        # Delete the inverted transaction.
        accounts.select(reversed_transaction)

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.activate(app.DeleteTransaction)
                yesno.assert_called_once_with(u'Are you sure you want to remove '
                                              u'transaction "Test transaction" ?',
                                              gtk.RESPONSE_YES,
                                              u'Remove transaction',
                                              u'Keep transaction')
        # The original transaction, also must have been deleted.
        original = self.store.find(AccountTransaction, account=account).count()
        self.assertEquals(original, 0)
        page.refresh()
        self.assertEquals(len(accounts), 0)

    @mock.patch('stoq.gui.financial.print_report')
    def test_print(self, print_report):
        at = self.create_account_transaction(self.create_account())
        at.account.description = u"The Account"
        at.edited_account = at.account

        app = self.create_app(FinancialApp, u"financial")
        page = self._open_page(app, u"The Account")

        self.activate(app.Print)

        print_report.assert_called_once_with(
            AccountTransactionReport,
            page.result_view, list(page.result_view),
            account=page.model,
            filters=page.search.get_search_filters())

    @mock.patch('stoq.gui.financial.SpreadSheetExporter.export')
    def test_export_spreadsheet(self, export):
        at = self.create_account_transaction(self.create_account())
        at.account.description = u"The Account"
        at.edited_account = at.account

        app = self.create_app(FinancialApp, u"financial")
        page = self._open_page(app, u"The Account")

        self.activate(app.ExportSpreadSheet)

        export.assert_called_once_with(object_list=page.result_view,
                                       name=u'Financial',
                                       filename_prefix=u'financial')

    @mock.patch('stoq.gui.financial.yesno')
    @mock.patch('stoq.gui.financial.api.new_store')
    def test_delete_account(self, new_store, yesno):
        yesno.return_value = True
        new_store.return_value = self.store

        at = self.create_account_transaction(self.create_account())
        at.account.description = u"The Account"
        at.edited_account = at.account

        app = self.create_app(FinancialApp, u"financial")
        accounts = app.accounts

        for account in accounts:
            if account.description == at.account.description:
                selected_account = account

        accounts.select(selected_account)
        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.activate(app.DeleteAccount)
                yesno.assert_called_once_with(u'Are you sure you want to remove '
                                              u'account "The Account" ?',
                                              gtk.RESPONSE_NO,
                                              u'Remove account', u'Keep account')
                self.assertTrue(selected_account not in accounts)

    @mock.patch('stoq.gui.financial.yesno')
    @mock.patch('stoq.gui.financial.api.new_store')
    def test_delete_transaction(self, new_store, yesno):
        yesno.return_value = True
        new_store.return_value = self.store

        at = self.create_account_transaction(self.create_account())
        at.account.description = u"The Account"
        at.edited_account = at.account

        app = self.create_app(FinancialApp, u"financial")
        page = self._open_page(app, u"The Account")

        olist = page.result_view
        olist.select(olist[0])

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.activate(app.DeleteTransaction)
                yesno.assert_called_once_with(u'Are you sure you want to remove '
                                              u'transaction "Test Account '
                                              u'Transaction" ?',
                                              gtk.RESPONSE_YES,
                                              u'Remove transaction',
                                              u'Keep transaction')
                self.assertEquals(len(olist), 0)

    @mock.patch('stoq.gui.financial.FinancialApp.run_dialog')
    @mock.patch('stoq.gui.financial.api.new_store')
    def test_create_new_account(self, new_store, run_dialog):
        new_store.return_value = self.store

        app = self.create_app(FinancialApp, u"financial")
        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.activate(app.NewAccount)
                run_dialog.assert_called_once_with(AccountEditor, self.store,
                                                   model=None, parent_account=None)

    @mock.patch('stoq.gui.financial.FinancialApp.run_dialog')
    @mock.patch('stoq.gui.financial.api.new_store')
    def test_edit_existing_account(self, new_store, run_dialog):
        run_dialog.return_value = True
        new_store.return_value = self.store

        at = self.create_account_transaction(self.create_account())
        at.account.description = u"The Account"
        at.edited_account = at.account

        app = self.create_app(FinancialApp, u"financial")
        accounts = app.accounts

        for account in accounts:
            if account.description == at.account.description:
                selected_account = account

        accounts.select(selected_account)
        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.activate(app.Edit)
                run_dialog.assert_called_once_with(AccountEditor, self.store,
                                                   parent_account=None,
                                                   model=at.account)
