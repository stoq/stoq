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
## Author(s):       Henrique Romano             <henrique@async.com.br>
##                  Evandro Vale Miquelito      <evandro@async.com.br>
##
"""
stoq/gui/till/till.py:

    Implementation of till application.
"""

import gettext
import datetime

import gtk
from sqlobject.sqlbuilder import AND
from kiwi.ui.widgets.list import Column, SummaryLabel
from kiwi.ui.dialogs import messagedialog
from stoqlib.gui.search import SearchBar
from stoqlib.gui.columns import ForeignKeyColumn
from stoqlib.exceptions import TillError
from stoqlib.database import rollback_and_begin, finish_transaction

from stoq.domain.sale import Sale
from stoq.domain.person import Person, PersonAdaptToClient
from stoq.domain.till import get_current_till_operation, Till
from stoq.lib.runtime import new_transaction
from stoq.lib.parameters import sysparam
from stoq.lib.validators import get_formatted_price, get_price_format_str
from stoq.lib.drivers import emit_read_X, emit_reduce_Z, emit_coupon
from stoq.gui.application import AppWindow
from stoq.gui.editors.till import TillOpeningEditor, TillClosingEditor
from stoq.gui.till.operation import TillOperationDialog
from stoq.gui.wizards.sale import SaleWizard

_ = gettext.gettext


class TillApp(AppWindow):

    app_name = _('Till')
    gladefile = 'till'
    widgets = ('searchbar_holder',
               'sales_list',
               'list_vbox',
               'confirm_order_button',
               'TillMenu',
               'TillOpen',
               'TillClose',
               'TillOperations',
               'CurrentTill',
               'quit_action')

    def __init__(self, app):
        AppWindow.__init__(self, app)
        self.conn = new_transaction()
        if not sysparam(self.conn).CONFIRM_SALES_ON_TILL:
            self.confirm_order_button.hide()
        self._setup_slaves()
        self._setup_widgets()
        self.searchbar.search_items()
        self._update_widgets()

    def _select_first_item(self, list):
        if len(list):
            # XXX this part will be removed after bug 2178
            list.select(list[0])

    def get_title(self):
        today_format = _('%d of %B')
        today_str = datetime.datetime.today().strftime(today_format)
        return _('Stoq - %s of %s') % (self.app_name, today_str)

    def _update_total(self, *args):
        self.summary_label.update_total()

    def _setup_widgets(self):
        value_format = '<b>%s</b>' % get_price_format_str()
        self.summary_label = SummaryLabel(klist=self.sales_list,
                                          column='total_sale_amount',
                                          label='<b>Total:</b>',
                                          value_format=value_format)
        self.summary_label.show()
        self.list_vbox.pack_start(self.summary_label, False)

    def _update_widgets(self):
        has_till = get_current_till_operation(self.conn) is not None
        self.TillClose.set_sensitive(has_till)
        self.TillOpen.set_sensitive(not has_till)
        self.TillOperations.set_sensitive(has_till)
        has_sales = len(self.sales_list) > 0
        self.confirm_order_button.set_sensitive(has_sales)
        self._update_total()

    def _setup_slaves(self):
        self.sales_list.set_columns(self._get_columns())
        self.searchbar = SearchBar(self, Sale, self._get_columns())
        self.searchbar.set_result_strings(_('sale'), _('sales'))
        self.searchbar.set_searchbar_labels(_('Sales Matching:'))
        self.attach_slave('searchbar_holder', self.searchbar)

    def _format_order_number(self, order_number):
        # FIXME We will remove this method after bug 2214
        if not order_number:
            return 0
        return order_number

    def _get_columns(self):
        return [Column('order_number', title=_('Order'), width=100, 
                       format_func=self._format_order_number,
                       data_type=int, sorted=True),
                Column('open_date', title=_('Date'), width=120, 
                       data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT),
                ForeignKeyColumn(Person, 'name', title=_('Client'), expand=True,
                                 data_type=str, obj_field='client',
                                 adapted=True),
                Column('total_sale_amount', title=_('Total'), width=150, 
                       data_type=float, justify=gtk.JUSTIFY_RIGHT,
                       format_func=get_formatted_price)]

    def get_extra_query(self):
        q1 = Sale.q.clientID == PersonAdaptToClient.q.id
        q2 = PersonAdaptToClient.q._originalID == Person.q.id
        q3 = Sale.q.status == Sale.STATUS_OPENED
        return AND(q1, q2, q3)

    def update_klist(self, sales=[]):
        rollback_and_begin(self.conn)
        self.sales_list.clear()
        for sale in sales:
            # Since search bar change the connection internally we must get
            # the objects back in our main connection
            obj = Sale.get(sale.id, connection=self.conn)
            self.sales_list.append(obj)
        self._select_first_item(self.sales_list)
        self._update_widgets()

    def open_till(self):
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

    #
    # Kiwi callbacks
    #
   
    def on_confirm_order_button__clicked(self, *args):
        rollback_and_begin(self.conn)
        sale = self.sales_list.get_selected()
        title = _('Confirm Sale')
        model = self.run_dialog(SaleWizard, self.conn, sale, title=title,
                                edit_mode=True)
        if not finish_transaction(self.conn, model, keep_transaction=True):
            return
        sale.confirm_sale()

        if not emit_coupon(self.conn, sale):
            return
        self.conn.commit()
        self.searchbar.search_items()

    def _on_close_till_action__clicked(self, *args):
        if not emit_reduce_Z(self.conn):
            short = _("It's not possible to emit a reduce Z")
            long = _("It's not possible to emit a reduce Z for the "
                     "configured printer.\nWould you like to ignore "
                     "this error and continue?")
            buttons = ((_("Cancel Operation"), gtk.RESPONSE_CANCEL),
                       (_("Ignore this error"), gtk.RESPONSE_YES))
            parent = self.get_toplevel()
            if messagedialog(gtk.MESSAGE_QUESTION, short, long,
                             parent, buttons) != gtk.RESPONSE_YES:
                return
        self.close_till()

    def _on_open_till_action__clicked(self, *args):
        if not emit_read_X(self.conn):
            short = _("It's not possible to emit a read X")
            long = _("It's not possible to emit a read X for the "
                     "configured printer.\nWould you like to ignore "
                     "this error and continue?")
            buttons = ((_("Cancel Operation"), gtk.RESPONSE_CANCEL),
                       (_("Ignore this error"), gtk.RESPONSE_YES))
            parent = self.get_toplevel()
            if messagedialog(gtk.MESSAGE_QUESTION, short, long,
                             parent, buttons) != gtk.RESPONSE_YES:
                return
        self.open_till()

    def _on_operations_action__clicked(self, *args):
        dialog = TillOperationDialog(self.conn)
        dialog.connect('close-till', self.close_till)
        self.run_dialog(dialog, self.conn)

