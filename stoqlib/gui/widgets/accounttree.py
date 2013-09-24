##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

import gtk

from kiwi.currency import currency
from kiwi.python import Settable
from kiwi.ui.objectlist import ColoredColumn, Column, ObjectTree

from stoqlib.domain.views import Account, AccountView
from stoqlib.gui.stockicons import (STOQ_MONEY, STOQ_PAYABLE_APP, STOQ_BILLS,
                                    STOQ_TILL_APP)
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class StockTextColumn(Column):
    "A column which you can add a stock item and a text"
    def __init__(self, *args, **kwargs):
        Column.__init__(self, *args, **kwargs)

    def attach(self, objectlist):
        column = Column.attach(self, objectlist)
        self._pixbuf_renderer = gtk.CellRendererPixbuf()
        column.pack_start(self._pixbuf_renderer, False)
        return column

    def cell_data_func(self, tree_column, renderer,
                       model, treeiter, (column, renderer_prop)):
        row = model[treeiter]
        data = column.get_attribute(row[0], column.attribute, None)
        text = column.as_string(data)
        renderer.set_property(renderer_prop, text)
        pixbuf = self._objectlist.get_pixbuf(row[0])
        self._pixbuf_renderer.set_property('pixbuf', pixbuf)


def sort_models(a, b):
    return cmp(a.lower(),
               b.lower())


class AccountTree(ObjectTree):
    __gtype_name__ = 'AccountTree'

    def __init__(self, with_code=True, create_mode=False):
        self.create_mode = create_mode
        self._accounts = {}

        columns = [StockTextColumn('description', title=_("Account name"),
                                   data_type=str, pack_end=True, expand=True,
                                   sorted=True, sort_func=sort_models)]
        if with_code:
            columns.append(Column('code', title=_("Code"), data_type=str,
                                  width=120))
        if not create_mode:
            # FIXME: This needs to be much better colorized, and moved to the
            #        domain classes
            def colorize(account):
                if (account.kind == 'account' and
                    account.account_type == Account.TYPE_INCOME):
                    return False
                else:
                    return account.total < 0
            columns.append(ColoredColumn('total', title=_("Total"), width=100,
                                         data_type=currency,
                                         color='red',
                                         data_func=colorize,
                                         use_data_model=True))
        ObjectTree.__init__(self, columns,
                            mode=gtk.SELECTION_SINGLE)

        def render_icon(icon):
            return self.render_icon(icon, gtk.ICON_SIZE_MENU)
        self._pixbuf_money = render_icon(STOQ_MONEY)
        self._pixbuf_payable = render_icon(STOQ_PAYABLE_APP)
        self._pixbuf_receivable = render_icon(STOQ_BILLS)
        self._pixbuf_till = render_icon(STOQ_TILL_APP)
        if self.create_mode:
            self.set_headers_visible(False)

    # Order the accounts top to bottom so
    # ObjectTree.append() works as expected
    def _orderaccounts(self, all_accounts, res=None, parent=None):
        if not res:
            res = []
        if parent is None:
            accounts = [a for a in all_accounts if a.parent_id is None]
        else:
            accounts = [a for a in all_accounts if a.parent_id == parent.id]

        res.extend(accounts)
        for account in accounts:
            account.selectable = True
            self._orderaccounts(all_accounts, res, account)
        return res

    def _calculate_total(self, all_accounts, account):
        total = account.get_combined_value()
        for a in all_accounts:
            if a.parent_id == account.id:
                total += self._calculate_total(all_accounts, a)
        return total

    def get_pixbuf(self, model):
        kind = model.kind
        if kind == 'payable':
            pixbuf = self._pixbuf_payable
        elif kind == 'receivable':
            pixbuf = self._pixbuf_receivable
        elif kind == 'account':
            till_account_id = sysparam.get_object_id('TILLS_ACCOUNT')
            if model.matches(till_account_id):
                pixbuf = self._pixbuf_till
            else:
                pixbuf = self._pixbuf_money
        else:
            return None
        return pixbuf

    def insert_initial(self, store, edited_account=None):
        """ Insert accounts and parent accounts in a ObjectTree.

        :param store: a store
        :param edited_account: If not None, this is the account being edited.
          In this case, this acount (and its decendents) will not be shown in
          the account tree.
        """
        till_id = sysparam.get_object_id('TILLS_ACCOUNT')

        if self.create_mode and edited_account:
            accounts = list(store.find(AccountView,
                                       AccountView.id != edited_account.id))
        else:
            accounts = list(store.find(AccountView))
        accounts = self._orderaccounts(accounts)

        for account in accounts:
            account.total = self._calculate_total(accounts, account)
            if self.create_mode and account.matches(till_id):
                account.selectable = False
            self.add_account(account.parent_id, account)

        selectable = not self.create_mode

        # Tabs cache requires unique ids
        self.append(None, Settable(description=_("Accounts Payable"),
                                   id=-1,
                                   parent=None,
                                   kind='payable',
                                   selectable=selectable,
                                   total=None))
        self.append(None, Settable(description=_("Accounts Receivable"),
                                   id=-2,
                                   parent=None,
                                   kind='receivable',
                                   selectable=selectable,
                                   total=None))
        self.flush()

    def add_account(self, parent_id, account):
        account.kind = 'account'
        parent = self._accounts.get(parent_id)
        self.append(parent, account)
        self._accounts[account.id] = account

    def get_account_by_id(self, account_id):
        return self._accounts.get(account_id)

    def refresh_accounts(self, store, account=None):
        self._accounts = {}
        self.clear()
        self.insert_initial(store)
        if account:
            self.select(account)
        self.flush()
