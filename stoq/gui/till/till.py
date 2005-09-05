# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):       Henrique Romano     <henrique@async.com.br>
##
"""
stoq/gui/till/till.py:
    Implementation of till application.
"""

import gettext
from datetime import date
import gtk

from sqlobject.sqlbuilder import AND
from kiwi.ui.widgets.list import Column
from stoqlib.gui.search import BaseListSlave, SearchBar
from stoqlib.gui.columns import ForeignKeyColumn
from stoqlib.exceptions import TillError
from stoqlib.database import rollback_and_begin

from stoq.gui.application import AppWindow
from stoq.domain.sale import Sale
from stoq.domain.person import Person, PersonAdaptToClient
from stoq.domain.payment import get_current_till_operation, Till
from stoq.domain.sellable import get_formatted_price
from stoq.lib.runtime import new_transaction
from stoq.lib.parameters import sysparam
from stoq.gui.editors.till import TillOpeningEditor, TillClosingEditor

_ = gettext.gettext

class TillApp(AppWindow):
    gladefile = 'till'
    widgets = ('searchbar_holder',
               'klist_holder',
               'confirm_order_button',
               'TillMenu',
               'TillOpen',
               'TillClose',
               'CurrentTill',
               'quit_action')

    def __init__(self, app):
        AppWindow.__init__(self, app)
        self.conn = new_transaction()
        self._setup_widgets()
        self._setup_slaves()

    def _setup_widgets(self):
        self._update_widgets()
        # TODO: Waiting for bug #1862
        self.confirm_order_button.set_sensitive(False)
        # TODO: Implement Current Till Operation dialog
        self.CurrentTill.set_sensitive(False)

    def _update_widgets(self):
        has_till = get_current_till_operation(self.conn) is not None
        self.TillClose.set_sensitive(has_till)
        self.TillOpen.set_sensitive(not has_till)

    def _setup_slaves(self):
        list_slave = BaseListSlave(columns=self.get_columns())
        self.attach_slave('klist_holder', list_slave)
        self.sale_list = list_slave.klist

        self.searchbar = SearchBar(self, Sale, self.get_columns(),
                                   search_lbl_text=_('Find Sales'))
        self.searchbar.search_items()
        self.attach_slave('searchbar_holder', self.searchbar)

    #
    # BaseListSlave hooks
    #

    def get_columns(self):
        return [Column('code', title=_('Order'), width=100, data_type=int,
                       sorted=True),
                Column('open_date', title=_('Date'), width=120, 
                       data_type=date, justify=gtk.JUSTIFY_RIGHT),
                ForeignKeyColumn(Person, 'name', title=_('Client'), expand=True,
                                 data_type=str, obj_field='client._original'),
                Column('total', title=_('Total'), width=150, data_type=float,
                       justify=gtk.JUSTIFY_RIGHT, format='%.2f')]

    def get_extra_query(self):
        q1 = Sale.q.clientID == PersonAdaptToClient.q.id
        q2 = PersonAdaptToClient.q._originalID == Person.q.id
        q3 = Sale.q.status == Sale.STATUS_OPENED
        return AND(q1, q2, q3)

    def update_klist(self, items=[]):
        self.sale_list.clear()
        total_value = 0.00

        for item in items:
            self.sale_list.add_instance(item)
            total_value += item.total

    #
    # Kiwi callbacks
    #

    def open_till(self, *args):
        rollback_and_begin(self.conn)

        if get_current_till_operation(self.conn) is not None:
            raise TillError("You already have a till operation opened. "
                            "Close the current Till and open another one.")
        
        # Trying get the operation created by the last till
        # operation closed.  This operation has all the sales
        # not confirmed in the last operation.
        result = Till.select(Till.q.status == Till.STATUS_PENDING,
                             connection=self.conn)
        if result.count() == 0:
            till = Till(connection=self.conn, 
                        branch=sysparam(self.conn).CURRENT_BRANCH)
        elif result.count() == 1:
            till = result[0]
        else:
            raise TillError("You have more than one till operation "
                            "pending.")

        if self.run_dialog(TillOpeningEditor, self.conn, till):
            self.conn.commit()
            self._update_widgets()
            return
        rollback_and_begin(self.conn)

    def close_till(self, *args):
        till = get_current_till_operation(self.conn)
        if till is None:
            raise ValueError("You should have a till operation opened at "
                             "this point")

        if not self.run_dialog(TillClosingEditor, self.conn, till):
            rollback_and_begin(self.conn)
            return

        self.conn.commit()
        self._update_widgets()

        opened_sales = Sale.select(Sale.q.status == Sale.STATUS_OPENED,
                                   connection=self.conn)
        if opened_sales.count() == 0:
            return

        # A new till object to "store" the sales that weren't
        # confirmed. Note that this new till operation isn't
        # opened yet, but it will be considered when opening a
        # new operation
        new_till = Till(connection=self.conn, 
                        branch=sysparam(self.conn).CURRENT_BRANCH)
        for sale in opened_sales:
            sale.till = new_till

        self.conn.commit()


