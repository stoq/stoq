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

import gtk
import pango
from kiwi.python import Settable
from kiwi.ui.dialogs import open as open_dialog
from kiwi.ui.objectlist import ColoredColumn, Column, ObjectList, ObjectTree
from stoqlib.database.runtime import new_transaction, finish_transaction
from stoqlib.domain.account import Account
from stoqlib.domain.payment.views import InPaymentView, OutPaymentView
from stoqlib.gui.accounttree import AccountTree
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.accounteditor import AccountEditor
from stoqlib.importers.ofximporter import OFXImporter
from stoqlib.lib.message import info, yesno
from stoqlib.lib.parameters import sysparam
from stoq.gui.application import AppWindow
from kiwi.currency import currency

_ = gettext.gettext

gtk.rc_parse_string("""
style "treeview" {
  GtkTreeView::odd-row-color = "#c2e7c4"
  GtkTreeView::even-row-color = "#f5ffe0"
  GtkTreeView::grid-line-pattern = "\xff\x01"
  GtkTreeView::grid-line-width = 1
}
widget_class "*TransactionPage*" style "treeview"

""") #"

class TransactionPage(ObjectList):
    # shows either a list of:
    #   - transactions
    #   - payments
    def __init__(self, model):
        self.model = model
        self._block = False
        ObjectList.__init__(self, columns=self.get_columns())
        tree_view = self.get_treeview()
        tree_view.set_rules_hint(True)
        tree_view.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)

        if model.kind == 'account':
            self._populate_transactions()
        elif model.kind == 'payable':
            self._populate_payable_payments(OutPaymentView)
        elif model.kind == 'receivable':
            self._populate_payable_payments(InPaymentView)
        else:
            raise TypeError("unknown model kind: %r" % (model.kind, ))

    def _populate_transactions(self):
        total = decimal.Decimal('0')
        for t in self.model.transactions:
            total += t.value
            account = t.get_other_account(self.model)
            self.append(Settable(date=t.date,
                                 account=account.long_description,
                                 description=t.description,
                                 value=t.value,
                                 total=total))


    def _populate_payable_payments(self, view_class):
        for view in view_class.select():
            self.append(view)

    def get_columns(self):
        if self.model.kind in ['payable', 'receivable']:
            date_column = 'paid_date'
        else:
            date_column = 'date'
        columns = [Column(date_column, data_type=datetime.date, sorted=True),
                   Column('description', data_type=unicode, expand=True,
                          editable=True)]

        if self.model.kind == 'account':
            columns.append(Column('account', data_type=unicode))
        columns.append(Column('value', data_type=currency))
        if self.model.kind == 'account':
            columns.append(ColoredColumn('total', data_type=currency,
                                         color='red',
                                         data_func=lambda x: x < 0))
        return columns

class FinancialApp(AppWindow):

    app_name = _('Financial')
    app_icon_name = 'stoq-financial-app'
    gladefile = 'financial'
    klist_name = 'accounts'

    def __init__(self, app):
        self._pages = {}

        self.accounts = AccountTree()
        self._create_toolbar()

        AppWindow.__init__(self, app)
        self.search_holder.add(self.accounts)
        self.accounts.show()
        self.accounts.insert_initial(self.conn)

        self._attach_toolbar()
        self._create_initial_page()

    #
    # Private
    #

    def _create_toolbar(self):
        ui_string = """<ui>
          <toolbar action="toolbar">
            <toolitem action="CloseTab"/>
            <toolitem action="AddAccount"/>
            <separator/>
            <toolitem action="DeleteAccount"/>
          </toolbar>
        </ui>"""

        uimanager = self.get_uimanager()
        actions = [
            ('toolbar', None, ''),
            ('CloseTab', gtk.STOCK_CLOSE, _('Close'), '<control>w',
             _('Close the current tab')),
            ('AddAccount', gtk.STOCK_ADD, _('Create New Account'),
             '<control>a', _('Create New Account')),
            ('DeleteAccount', gtk.STOCK_DELETE, _('Delete Account'),
             '', _('Delete Account')),
            ]
        ag = gtk.ActionGroup('UsersMenuActions')
        ag.add_actions(actions)
        uimanager.insert_action_group(ag, 0)
        uimanager.add_ui_from_string(ui_string)

        self.CloseTab = ag.get_action('CloseTab')
        self.AddAccount = ag.get_action('AddAccount')
        self.DeleteAccount = ag.get_action('DeleteAccount')

    def _attach_toolbar(self):
        # FIXME: Move to Application when we finished migrating off Gazpacho
        self.get_toplevel().add_accel_group(
            self.get_uimanager().get_accel_group())

        self._update_actions()
        toolbar = self.get_uimanager().get_widget('ui/toolbar')
        self.main_vbox.pack_start(toolbar, False, False)
        self.main_vbox.reorder_child(toolbar, 1)

    def _update_actions(self):
        self.CloseTab.set_sensitive(self._can_close_tab())
        self.DeleteAccount.set_sensitive(self._can_delete_account())
        self.details_button.set_sensitive(self._can_show_details())

    def _create_initial_page(self):
        pixbuf = self.accounts.render_icon('stoq-money', gtk.ICON_SIZE_MENU)
        hbox = self._create_tab_label(_('Accounts'), pixbuf)
        page = self.notebook.get_nth_page(0)
        self.notebook.set_tab_label(page, hbox)

    def _create_new_account(self):
        if self._is_accounts_tab():
            parent = self.accounts.get_selected()
        else:
            page_id = self.notebook.get_current_page()
            page = self.notebook.get_nth_page(page_id)
            if page.account.kind == 'account':
                parent = page.account
            else:
                parent = None
        retval = self._run_account_editor(None, parent)
        if retval:
            account = Account.get(retval.id, connection=self.conn)
            self.accounts.refresh_accounts(self.conn, account)

    def _edit_existing_account(self, account):
        assert account.kind == 'account'
        account = self.accounts.get_selected()
        retval = self._run_account_editor(account, account.parent)
        if not retval:
            return
        account = Account.get(retval.id, connection=self.conn)
        # FIXME: Support incremental updating
        self.accounts.refresh_accounts(self.conn, account)

    def _run_account_editor(self, model, parent_account):
        trans = new_transaction()
        model = trans.get(model)

        retval = self.run_dialog(AccountEditor, trans, model=model,
                                 parent_account=parent_account)
        if finish_transaction(trans, retval):
            self.accounts.refresh_accounts(self.conn)

        return retval

    def _close_current_page(self):
        assert self._can_close_tab()
        page_id = self.notebook.get_current_page()
        # Do not allow the initial page to be removed
        page = self.notebook.get_children()[page_id]
        self.notebook.remove_page(page_id)
        del self._pages[page.account]
        self._update_actions()

    def _is_accounts_tab(self):
        page_id = self.notebook.get_current_page()
        return page_id == 0

    def _can_close_tab(self):
        # The first tab is not closable
        return not self._is_accounts_tab()

    def _create_tab_label(self, title, pixbuf):
        hbox = gtk.HBox()
        image = gtk.image_new_from_pixbuf(pixbuf)
        hbox.pack_start(image, False, False)
        label = gtk.Label(title)
        hbox.pack_start(label, True, False)
        if title != _("Accounts"):
            image = gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
            button = gtk.Button()
            button.set_relief(gtk.RELIEF_NONE)
            button.connect('clicked', lambda button: self._close_current_page())
            button.add(image)
            hbox.pack_end(button, False, False)
        hbox.show_all()
        return hbox

    def _new_page(self, account):
        if account in self._pages:
            page = self._pages[account]
            page_id = self.notebook.get_children().index(page)
        else:
            pixbuf = self.accounts.get_pixbuf(account)
            hbox = self._create_tab_label(account.description, pixbuf)
            page = TransactionPage(account)
            page_id = self.notebook.append_page(page, hbox)
            page.show()
            page.account = account
            self._pages[account] = page

        self.notebook.set_current_page(page_id)
        self._update_actions()

    def _import_ofx(self):
        ffilter = gtk.FileFilter()
        ffilter.set_name('OFX')
        ffilter.add_pattern('*.ofx')
        filename = open_dialog("Import", parent=self.financial,
                               filter=ffilter)
        if filename is None:
            return
        ofx = OFXImporter()
        ofx.parse(open(filename))

        imbalance_account = sysparam(self.conn).IMBALANCE_ACCOUNT
        trans = new_transaction()
        account = ofx.import_transactions(trans, imbalance_account)
        trans.commit(close=True)
        account = self.conn.get(account)

        info(_("Imported %d transactions") % account.transactions.count(),
             _("Imported %d transactions into account %s" % (
            account.transactions.count(), account.long_description)))

        self.accounts.refresh_accounts(self.conn, account=self.conn.get(account))

    def _can_show_details(self):
        if not self._is_accounts_tab():
            return False

        account = self.accounts.get_selected()
        if account is None:
            return False

        if account.kind != 'account':
            return False

        return True

    def _can_delete_account(self):
        if not self._is_accounts_tab():
            return False

        account = self.accounts.get_selected()
        if account is None:
            return False

        # Can only remove real accounts
        if account.kind != 'account':
            return False

        return account.can_remove()

    def _delete_account(self, account):
        msg = _(u'Are you sure you want to remove account "%s" ?' %
                (account.description, ))
        if yesno(msg, gtk.RESPONSE_YES,
                 _("Don't Remove"), _(u"Remove account")):
            return

        self.accounts.remove(account)
        self.accounts.flush()

        trans = new_transaction()
        account = trans.get(account)
        account.remove(trans)
        trans.commit(close=True)

    #
    # Kiwi callbacks
    #
    def key_escape(self):
        self._close_current_page()
        return True

    def key_control_w(self):
        self._close_current_page()
        return True

    def on_accounts__row_activated(self, ktree, account):
        self._new_page(account)

    def on_accounts__selection_changed(self, ktree, account):
        self._update_actions()

    def on_details_button__clicked(self, button):
        account = self.accounts.get_selected()
        self._edit_existing_account(account)

    def on_CreateAccount__activate(self, action):
        self._create_new_account()

    def on_AddAccount__activate(self, action):
        self._create_new_account()

    def on_DeleteAccount__activate(self, action):
        account = self.accounts.get_selected()
        self._delete_account(account)

    def on_Import__activate(self, action):
        self._import_ofx()

    def on_notebook__switch_page(self, notebook, page, page_id):
        self._update_actions()

    def on_Quit__activate(self, action):
        self.shutdown_application()

    def on_About__activate(self, action):
        self._run_about()
