# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
"""
stoq/gui/financial/financial.py:

    Implementation of financial application.
"""

import datetime
import decimal
import gettext

from dateutil.relativedelta import relativedelta
import gobject
import gtk
from kiwi.currency import currency
from kiwi.db.query import DateQueryState, DateIntervalQueryState
from kiwi.db.sqlobj import SQLObjectQueryExecuter
from kiwi.python import Settable
from kiwi.ui.dialogs import open as open_dialog
from kiwi.ui.objectlist import ColoredColumn, Column, ObjectList
from kiwi.ui.search import Any, DateSearchFilter, DateSearchOption, SearchContainer
from stoqlib.api import api
from stoqlib.database.orm import const, OR, AND
from stoqlib.domain.account import Account, AccountTransaction, AccountTransactionView
from stoqlib.domain.payment.views import InPaymentView, OutPaymentView
from stoqlib.gui.accounttree import AccountTree
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.accounteditor import AccountEditor
from stoqlib.gui.editors.accounttransactioneditor import AccountTransactionEditor
from stoqlib.gui.dialogs.csvexporterdialog import CSVExporterDialog
from stoqlib.gui.dialogs.importerdialog import ImporterDialog
from stoqlib.gui.keybindings import get_accels
from stoqlib.gui.printing import print_report
from stoqlib.lib.dateconstants import get_month_names
from stoqlib.lib.message import yesno
from stoqlib.reporting.payment import AccountTransactionReport

from stoq.gui.application import AppWindow

_ = gettext.gettext


class NotebookCloseButton(gtk.Button):
    pass
gobject.type_register(NotebookCloseButton)


class FinancialSearchResults(ObjectList):
    pass
gobject.type_register(FinancialSearchResults)


class TransactionSearchContainer(SearchContainer):
    results_class = FinancialSearchResults

    def __init__(self, page, columns):
        self.page = page
        self.model = page.model
        SearchContainer.__init__(self, columns)

    def add_results(self, results):
        self.page.search.results.clear()
        if self.page.query.table == AccountTransactionView:
            self.page.append_transactions(results)
        else:
            self.page.search.results.extend(results)


class MonthOption(DateSearchOption):
    name = None
    year = None
    month = None

    def get_interval(self):
        start = datetime.date(self.year, self.month, 1)
        end = start + relativedelta(months=1, days=-1)
        return start, end


class TransactionPage(object):
    # shows either a list of:
    #   - transactions
    #   - payments
    def __init__(self, model, app, parent):
        self.model = model
        self.app = app
        self.parent_window = parent
        self._block = False

        self._create_search()
        self._add_date_filter()

        self._setup_search()
        self.refresh()

    def get_toplevel(self):
        return self.parent_window

    def _create_search(self):
        self.search = TransactionSearchContainer(
            self, columns=self._get_columns(self.model.kind))
        self.query = SQLObjectQueryExecuter()
        self.search.set_query_executer(self.query)
        self.search.results.connect('row-activated', self._on_row__activated)
        self.results = self.search.results
        tree_view = self.search.results.get_treeview()
        tree_view.set_rules_hint(True)
        tree_view.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)

    def _add_date_filter(self):
        self.date_filter = DateSearchFilter(_('Date:'))
        self.date_filter.clear_options()
        self.date_filter.add_option(Any, 0)
        year = datetime.datetime.today().year
        month_names = get_month_names()
        for i, month in enumerate(month_names):
            name = month_names[i]
            option = type(name + 'Option', (MonthOption, ),
                          {'name': gettext.gettext(name),
                           'month': i + 1,
                           'year': year})
            self.date_filter.add_option(option, i + 1)
        self.date_filter.add_custom_options()
        self.date_filter.mode.select_item_by_position(0)
        self.search.add_filter(self.date_filter)

    def _append_date_query(self, field):
        date = self.date_filter.get_state()
        queries = []
        if isinstance(date, DateQueryState) and date.date is not None:
            queries.append(field == date.date)
        elif isinstance(date, DateIntervalQueryState):
            queries.append(const.DATE(field) >= date.start)
            queries.append(const.DATE(field) <= date.end)
        return queries

    def _payment_query(self, query, having, conn):
        queries = []
        queries.extend(self._append_date_query(self.query.table.q.due_date))
        if query:
            queries.append(query)
        return self.query.table.select(AND(*queries), connection=conn)

    def _transaction_query(self, query, having, conn):
        queries = [OR(self.model.id == AccountTransaction.q.accountID,
                      self.model.id == AccountTransaction.q.source_accountID)]

        queries.extend(self._append_date_query(AccountTransaction.q.date))

        if query:
            queries.append(query)
        return AccountTransactionView.select(AND(*queries), connection=conn)

    def show(self):
        self.search.show()

    def _setup_search(self):
        if self.model.kind == 'account':
            self.query.set_table(AccountTransactionView)
            self.search.set_text_field_columns(['description'])
            self.query.set_query(self._transaction_query)
        elif self.model.kind == 'payable':
            self.search.set_text_field_columns(['description', 'supplier_name'])
            self.query.set_table(OutPaymentView)
            self.query.set_query(self._payment_query)
        elif self.model.kind == 'receivable':
            self.search.set_text_field_columns(['description', 'drawee'])
            self.query.set_table(InPaymentView)
            self.query.set_query(self._payment_query)
        else:
            raise TypeError("unknown model kind: %r" % (self.model.kind, ))

    def refresh(self):
        self.search.results.clear()
        if self.model.kind == 'account':
            transactions = AccountTransactionView.get_for_account(self.model, self.app.conn)
            self.append_transactions(transactions)
        elif self.model.kind == 'payable':
            self._populate_payable_payments(OutPaymentView)
        elif self.model.kind == 'receivable':
            self._populate_payable_payments(InPaymentView)
        else:
            raise TypeError("unknown model kind: %r" % (self.model.kind, ))

    def _get_columns(self, kind):
        if kind in ['payable', 'receivable']:
            return self._get_payment_columns()
        else:
            return self._get_account_columns()

    def _get_account_columns(self):
        def format_withdrawal(value):
            if value < 0:
                return '%.2f' % (abs(value), )

        def format_deposit(value):
            if value > 0:
                return '%.2f' % (value, )

        if self.model.account_type == Account.TYPE_INCOME:
            color_func = lambda x: False
        else:
            color_func = lambda x: x < 0
        return [Column('date', title=_("Date"), data_type=datetime.date, sorted=True),
                Column('code', title=_("Code"), data_type=unicode),
                Column('description', title=_("Description"),
                       data_type=unicode, expand=True),
                Column('account', title=_("Account"), data_type=unicode),
                Column('value',
                       title=self.model.account.get_type_label(out=False),
                       data_type=currency,
                       format_func=format_deposit),
                Column('value',
                       title=self.model.account.get_type_label(out=True),
                       data_type=currency,
                       format_func=format_withdrawal),
                ColoredColumn('total', title=_("Total"), data_type=currency,
                              color='red',
                              data_func=color_func)]

    def _get_payment_columns(self):
        return [Column('due_date', title=_("Due date"), data_type=datetime.date, sorted=True),
                Column('id', title=_("Code"), data_type=unicode),
                Column('description', title=_("Description"), data_type=unicode, expand=True),
                Column('value', title=_("Value"),
                       data_type=currency)]

    def append_transactions(self, transactions):
        for transaction in transactions:
            description = transaction.get_account_description(self.model)
            value = transaction.get_value(self.model)
            self._add_transaction(transaction, description, value)
        self.update_totals()

    def _populate_payable_payments(self, view_class):
        for view in view_class.select():
            self.search.results.append(view)

    def _add_transaction(self, transaction, description, value):
        item = Settable(transaction=transaction)
        self._update_transaction(item, transaction, description, value)
        self.search.results.append(item)
        return item

    def _update_transaction(self, item, transaction, description, value):
        item.account = description
        item.date = transaction.date
        item.description = transaction.description
        item.value = value
        item.code = transaction.code

    def update_totals(self):
        total = decimal.Decimal('0')
        for item in self.search.results:
            total += item.value
            item.total = total

    def _edit_transaction_dialog(self, item):
        trans = api.new_transaction()
        if isinstance(item.transaction, AccountTransactionView):
            account_transaction = trans.get(item.transaction.transaction)
        else:
            account_transaction = trans.get(item.transaction)
        model = getattr(self.model, 'account', self.model)

        transaction = run_dialog(AccountTransactionEditor, self,
                                 trans, account_transaction, model)

        if transaction:
            transaction.syncUpdate()
            self._update_transaction(item, transaction,
                                     transaction.edited_account.description,
                                     transaction.value)
            self.update_totals()
            self.search.results.update(item)
            self.app.accounts.refresh_accounts(self.app.conn)
        api.finish_transaction(trans, transaction)

    def on_dialog__opened(self, dialog):
        dialog.connect('account-added', self.on_dialog__account_added)

    def on_dialog__account_added(self, dialog):
        self.app.accounts.refresh_accounts(self.app.conn)

    def add_transaction_dialog(self):
        trans = api.new_transaction()
        model = getattr(self.model, 'account', self.model)
        model = trans.get(model)

        transaction = run_dialog(AccountTransactionEditor, self,
                                 trans, None, model)
        if transaction:
            transaction.sync()
            value = transaction.value
            other = transaction.get_other_account(model)
            if other == model:
                value = -value
            item = self._add_transaction(transaction, other.description, value)
            self.update_totals()
            self.search.results.update(item)
            self.app.accounts.refresh_accounts(self.app.conn)
        api.finish_transaction(trans, transaction)

    def _on_row__activated(self, objectlist, item):
        if self.model.kind == 'account':
            self._edit_transaction_dialog(item)


class FinancialApp(AppWindow):

    app_name = _('Financial')
    gladefile = 'financial'
    embedded = True

    def __init__(self, app):
        self._pages = {}
        self.accounts = AccountTree()
        AppWindow.__init__(self, app)
        self._tills_account = api.sysparam(self.conn).TILLS_ACCOUNT
        self._banks_account = api.sysparam(self.conn).BANKS_ACCOUNT

    #
    # AppWindow overrides
    #

    def create_actions(self):
        group = get_accels('app.financial')
        actions = [
            ('TransactionMenu', None, _('Transaction')),
            ('AccountMenu', None, _('Account')),
            ('Import', gtk.STOCK_ADD, _('Import...'),
             group.get('import'), _('Import a GnuCash or OFX file')),
            ('DeleteAccount', gtk.STOCK_DELETE, _('Delete...'),
             group.get('delete_account'),
             _('Delete the selected account')),
            ('DeleteTransaction', gtk.STOCK_DELETE, _('Delete...'),
             group.get('delete_transaction'),
             _('Delete the selected transaction')),
            ("NewAccount", gtk.STOCK_NEW, _("Account..."),
             group.get('new_account'),
             _("Add a new account")),
            ("NewTransaction", gtk.STOCK_NEW, _("Transaction..."),
             group.get('new_transaction'),
             _("Add a new transaction")),
            ("Edit", gtk.STOCK_EDIT, _("Edit..."),
             group.get('edit')),
            ]
        self.financial_ui = self.add_ui_actions('', actions,
                                                filename='financial.xml')
        self.set_help_section(_("Financial help"), 'app-financial')
        self.Edit.set_short_label(_('Edit'))
        self.DeleteAccount.set_short_label(_('Delete'))
        self.DeleteTransaction.set_short_label(_('Delete'))

    def create_ui(self):
        self.trans_popup = self.uimanager.get_widget('/TransactionSelection')
        self.acc_popup = self.uimanager.get_widget('/AccountSelection')

        self.app.launcher.add_new_items([self.NewAccount,
                                         self.NewTransaction])

        self.search_holder.add(self.accounts)
        self.accounts.show()
        self._create_initial_page()
        self._refresh_accounts()

    def activate(self, params):
        for page in self._pages.values():
            page.refresh()
        self._update_actions()
        self._update_tooltips()
        self.app.launcher.SearchToolItem.set_sensitive(False)

    def deactivate(self):
        self.uimanager.remove_ui(self.financial_ui)
        self.app.launcher.SearchToolItem.set_sensitive(True)

    def print_activate(self):
        self._print_transaction_report()

    def export_csv_activate(self):
        self._export_csv()

    #
    # Private
    #

    def _update_actions(self):
        is_accounts_tab = self._is_accounts_tab()
        self.AccountMenu.set_visible(is_accounts_tab)
        self.TransactionMenu.set_visible(not is_accounts_tab)
        self.DeleteAccount.set_visible(is_accounts_tab)
        self.DeleteTransaction.set_visible(not is_accounts_tab)
        self.app.launcher.ExportCSV.set_sensitive(not is_accounts_tab)
        self.app.launcher.Print.set_sensitive(not is_accounts_tab)

        self.NewAccount.set_sensitive(self._can_add_account())
        self.DeleteAccount.set_sensitive(self._can_delete_account())
        self.NewTransaction.set_sensitive(self._can_add_transaction())
        self.DeleteTransaction.set_sensitive(self._can_delete_transaction())
        self.Edit.set_sensitive(self._can_edit_account() or
                                self._can_edit_transaction())

    def _update_tooltips(self):
        if self._is_accounts_tab():
            self.Edit.set_tooltip(_("Edit the selected account"))
            self.app.launcher.Print.set_tooltip("")
        else:
            self.Edit.set_tooltip(_("Edit the selected transaction"))
            self.app.launcher.Print.set_tooltip(
                _("Print a report of these transactions"))

    def _create_initial_page(self):
        pixbuf = self.accounts.render_icon('stoq-money', gtk.ICON_SIZE_MENU)
        page = self.notebook.get_nth_page(0)
        hbox = self._create_tab_label(_('Accounts'), pixbuf)
        self.notebook.set_tab_label(page, hbox)

    def _create_new_account(self):
        parent_view = None
        if self._is_accounts_tab():
            parent_view = self.accounts.get_selected()
        else:
            page_id = self.notebook.get_current_page()
            page = self.notebook.get_nth_page(page_id)
            if page.account_view.kind == 'account':
                parent_view = page.account_view
        retval = self._run_account_editor(None, parent_view)
        if retval:
            self.accounts.refresh_accounts(self.conn)

    def _refresh_accounts(self):
        self.accounts.clear()
        self.accounts.insert_initial(self.conn)

    def _edit_existing_account(self, account_view):
        assert account_view.kind == 'account'
        retval = self._run_account_editor(account_view,
                                          self.accounts.get_parent(account_view))
        if not retval:
            return
        self.accounts.refresh_accounts(self.conn)

    def _run_account_editor(self, model, parent_account):
        trans = api.new_transaction()
        if model:
            model = trans.get(model.account)
        if parent_account:
            if parent_account.kind in ['payable', 'receivable']:
                parent_account = None
            if parent_account == api.sysparam(self.conn).IMBALANCE_ACCOUNT:
                parent_account = None
        retval = self.run_dialog(AccountEditor, trans, model=model,
                                 parent_account=parent_account)
        if api.finish_transaction(trans, retval):
            self.accounts.refresh_accounts(self.conn)

        return retval

    def _close_current_page(self):
        assert self._can_close_tab()
        page = self._get_current_page_widget()
        self._close_page(page)

    def _get_current_page_widget(self):
        page_id = self.notebook.get_current_page()
        page = self.notebook.get_children()[page_id]
        if isinstance(page, TransactionSearchContainer):
            return page.page
        return page

    def _close_page(self, page):
        for page_id, child in enumerate(self.notebook.get_children()):
            if getattr(child, 'page', None) == page:
                break
        else:
            raise AssertionError(page)
        self.notebook.remove_page(page_id)
        del self._pages[page.account_view.id]

    def _is_accounts_tab(self):
        page_id = self.notebook.get_current_page()
        return page_id == 0

    def _is_transaction_tab(self):
        page = self._get_current_page_widget()
        if not isinstance(page, TransactionPage):
            return False

        if page.model.kind != 'account':
            return False

        if (page.model == self._tills_account or
            page.model.parentID == self._tills_account.id):
            return False
        return True

    def _can_close_tab(self):
        # The first tab is not closable
        return not self._is_accounts_tab()

    def _create_tab_label(self, title, pixbuf, page=None):
        hbox = gtk.HBox()
        image = gtk.image_new_from_pixbuf(pixbuf)
        hbox.pack_start(image, False, False)
        label = gtk.Label(title)
        hbox.pack_start(label, True, False)
        if title != _("Accounts"):
            image = gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
            button = NotebookCloseButton()
            button.set_relief(gtk.RELIEF_NONE)
            if page:
                button.connect('clicked', lambda button: self._close_page(page))
            button.add(image)
            hbox.pack_end(button, False, False)
        hbox.show_all()
        return hbox

    def _new_page(self, account_view):
        if account_view.id in self._pages:
            page = self._pages[account_view.id]
            page_id = self.notebook.page_num(page.search)
        else:
            pixbuf = self.accounts.get_pixbuf(account_view)
            page = TransactionPage(account_view,
                                   self, self.get_toplevel())
            page.search.results.connect('selection-changed',
                                        self._on_transaction__selection_changed)
            page.search.results.connect('right-click',
                                        self._on_transaction__right_click)
            hbox = self._create_tab_label(account_view.description, pixbuf, page)
            page_id = self.notebook.append_page(page.search, hbox)
            page.show()
            page.account_view = account_view
            self._pages[account_view.id] = page

        self.notebook.set_current_page(page_id)
        self._update_actions()

    def _import(self):
        ffilters = []

        all_filter = gtk.FileFilter()
        all_filter.set_name(_('All supported formats'))
        all_filter.add_pattern('*.ofx')
        all_filter.add_mime_type('application/xml')
        all_filter.add_mime_type('application/x-gzip')
        ffilters.append(all_filter)

        ofx_filter = gtk.FileFilter()
        ofx_filter.set_name(_('Open Financial Exchange (OFX)'))
        ofx_filter.add_pattern('*.ofx')
        ffilters.append(ofx_filter)

        gnucash_filter = gtk.FileFilter()
        gnucash_filter.set_name(_('GNUCash xml format'))
        gnucash_filter.add_mime_type('application/xml')
        gnucash_filter.add_mime_type('application/x-gzip')
        ffilters.append(gnucash_filter)

        filename, file_chooser = open_dialog("Import", parent=self.financial,
                                             filter=ffilters, with_file_chooser=True)
        if filename is None:
            file_chooser.destroy()
            return

        ffilter = file_chooser.get_filter()
        if ffilter == gnucash_filter:
            format = 'gnucash.xml'
        elif ffilter == ofx_filter:
            format = 'account.ofx'
        elif ffilter == all_filter:
            # Guess
            if filename.endswith('.ofx'):
                format = 'account.ofx'
            else:
                format = 'gnucash.xml'

        file_chooser.destroy()

        run_dialog(ImporterDialog, self.financial, format, filename)

        # Refresh everthing after an import
        self.accounts.refresh_accounts(self.conn)
        for page in self._pages.values():
            page.refresh()

    def _export_csv(self):
        """Runs a dialog to export the current search results to a CSV file.
        """
        assert not self._is_accounts_tab()

        page = self._get_current_page_widget()
        self.run_dialog(CSVExporterDialog, self, AccountTransactionView,
                        page.results)

    def _can_add_account(self):
        if self._is_accounts_tab():
            return True

        return False

    def _can_edit_account(self):
        if not self._is_accounts_tab():
            return False

        account_view = self.accounts.get_selected()
        if account_view is None:
            return False

        # Can only remove real accounts
        if account_view.kind != 'account':
            return False

        if account_view.id == self._banks_account.id:
            return
        return True

    def _can_delete_account(self):
        if not self._is_accounts_tab():
            return False

        account_view = self.accounts.get_selected()
        if account_view is None:
            return False

        # Can only remove real accounts
        if account_view.kind != 'account':
            return False

        return account_view.account.can_remove()

    def _can_add_transaction(self):
        if self._is_transaction_tab():
            return True
        return False

    def _can_delete_transaction(self):
        if not self._is_transaction_tab():
            return False

        page = self._get_current_page_widget()
        transaction = page.results.get_selected()
        if transaction is None:
            return False

        return True

    def _can_edit_transaction(self):
        if not self._is_transaction_tab():
            return False

        page = self._get_current_page_widget()
        transaction = page.results.get_selected()
        if transaction is None:
            return False

        return True

    def _add_transaction(self):
        page = self._get_current_page_widget()
        page.add_transaction_dialog()
        self._refresh_accounts()

    def _delete_account(self, account_view):
        msg = _('Are you sure you want to remove account "%s" ?' %
                (account_view.description, ))
        if yesno(msg, gtk.RESPONSE_YES,
                 _("Keep account"), _("Remove account")):
            return

        if account_view.id in self._pages:
            account_page = self._pages[account_view.id]
            self._close_page(account_page)

        self.accounts.remove(account_view)
        self.accounts.flush()

        trans = api.new_transaction()
        account = trans.get(account_view.account)
        account.remove(trans)
        trans.commit(close=True)

    def _delete_transaction(self, item):
        msg = _('Are you sure you want to remove transaction "%s" ?' %
                (item.description))
        if yesno(msg, gtk.RESPONSE_YES,
                 _("Keep transaction"), _("Remove transaction")):
            return

        account_transactions = self._get_current_page_widget()
        account_transactions.results.remove(item)

        trans = api.new_transaction()
        if isinstance(item.transaction, AccountTransactionView):
            account_transaction = trans.get(item.transaction.transaction)
        else:
            account_transaction = trans.get(item.transaction)
        account_transaction.delete(account_transaction.id, connection=trans)
        trans.commit(close=True)
        account_transactions.update_totals()

    def _print_transaction_report(self):
        assert not self._is_accounts_tab()

        page = self._get_current_page_widget()
        print_report(AccountTransactionReport, page.results, list(page.results),
                     account=page.model,
                     filters=page.search.get_search_filters())

    #
    # Kiwi callbacks
    #

    def key_escape(self):
        if self._can_close_tab():
            self._close_current_page()
        return True

    def key_control_w(self):
        if self._can_close_tab():
            self._close_current_page()
        return True

    def on_accounts__row_activated(self, ktree, account_view):
        self._new_page(account_view)

    def _on_transaction__selection_changed(self, ktree, account_transaction):
        self._update_actions()

    def on_accounts__selection_changed(self, ktree, account_view):
        self._update_actions()

    def _on_transaction__right_click(self, results, result, event):
        self.trans_popup.popup(None, None, None, event.button, event.time)

    def on_accounts__right_click(self, results, result, event):
        self.acc_popup.popup(None, None, None, event.button, event.time)

    def on_Edit__activate(self, button):
        account_view = self.accounts.get_selected()
        self._edit_existing_account(account_view)

    def after_notebook__switch_page(self, notebook, page, page_id):
        self._update_actions()
        self._update_tooltips()

    # Toolbar

    def new_activate(self):
        if self._is_accounts_tab() and self._can_add_account():
            self._create_new_account()
        elif self._is_transaction_tab() and self._can_add_transaction():
            self._add_transaction()

    def on_NewAccount__activate(self, action):
        self._create_new_account()

    def on_NewTransaction__activate(self, action):
        self._add_transaction()

    def on_DeleteAccount__activate(self, action):
        account_view = self.accounts.get_selected()
        self._delete_account(account_view)

    def on_DeleteTransaction__activate(self, action):
        transactions = self._get_current_page_widget()
        transaction = transactions.results.get_selected()
        self._delete_transaction(transaction)
        self._refresh_accounts()

    # Financial

    def on_Import__activate(self, action):
        self._import()
