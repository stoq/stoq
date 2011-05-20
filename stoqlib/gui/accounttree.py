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

from kiwi.python import Settable
from kiwi.ui.objectlist import Column, ObjectTree
from stoqlib.database.runtime import get_connection
from stoqlib.domain.account import Account
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
    def __init__(self, with_code=True, create_mode=False):
        self.create_mode = create_mode
        columns = [StockTextColumn('description', data_type=str,
                   pack_end=True, sorted=True, sort_func=sort_models)]
        if with_code:
            columns.append(Column('code', data_type=str))
        ObjectTree.__init__(self, columns,
                            mode=gtk.SELECTION_SINGLE)

        def render_icon(icon):
            return self.render_icon(icon, gtk.ICON_SIZE_MENU)
        self._pixbuf_money = render_icon('stoq-money')
        self._pixbuf_payable = render_icon('stoq-payable-app')
        self._pixbuf_receivable = render_icon('stoq-bills')
        self._pixbuf_till = render_icon('stoq-till-app')

    # Order the accounts top to bottom so
    # ObjectTree.append() works as expected
    def _orderaccounts(self, conn, res=None, parent=None):
        if not res:
            res = []
        accounts = Account.selectBy(connection=conn, parent=parent)
        res.extend(accounts)
        for account in accounts:
            account.kind = 'account'
            account.selectable = True
            self._orderaccounts(conn, res, account)
        return res

    def get_pixbuf(self, model):
        kind = model.kind
        if kind == 'payable':
            pixbuf = self._pixbuf_payable
        elif kind == 'receivable':
            pixbuf = self._pixbuf_receivable
        elif kind == 'account':
            till_account = sysparam(get_connection()).TILLS_ACCOUNT
            if ((model.parent and model.parent == till_account) or
                model == till_account):
                pixbuf = self._pixbuf_till
            else:
                pixbuf = self._pixbuf_money
        else:
            return None
        return pixbuf

    def insert_initial(self, conn, ignore=None):
        till_id = sysparam(get_connection()).TILLS_ACCOUNT.id

        for account in self._orderaccounts(conn):
            if account == ignore:
                continue
            if (self.create_mode and
                (account.id == till_id or
                 account.parent and account.parent.id == till_id)):
                account.selectable = False
            self.append(account.parent, account)

        selectable = not self.create_mode
        self.append(None, Settable(description=_("Accounts Payable"),
                                   parent=None,
                                   kind='payable',
                                   selectable=selectable))
        self.append(None, Settable(description=_("Accounts Receivable"),
                                   parent=None,
                                   kind='receivable',
                                   selectable=selectable))
        self.flush()

    def add_account(self, parent, account):
        account.kind = 'account'
        self.append(parent, account)

    def refresh_accounts(self, conn, account=None):
        self.clear()
        self.insert_initial(conn)
        if account:
            self.select(account)
        self.flush()
