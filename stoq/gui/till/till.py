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
""" Implementation of till application.  """

import gettext
import datetime

import gtk
from kiwi.datatypes import currency
from kiwi.ui.widgets.list import Column, SummaryLabel
from kiwi.ui.dialogs import messagedialog
from sqlobject.sqlbuilder import AND
from stoqlib.exceptions import TillError
from stoqlib.database import rollback_and_begin, finish_transaction
from stoqlib.domain.sale import Sale
from stoqlib.domain.person import Person, PersonAdaptToClient
from stoqlib.domain.till import get_current_till_operation, Till
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.drivers import emit_read_X, emit_reduce_Z, emit_coupon
from stoqlib.gui.base.columns import ForeignKeyColumn
from stoqlib.gui.editors.till import TillOpeningEditor, TillClosingEditor
from stoqlib.gui.dialogs.tilloperation import TillOperationDialog
from stoqlib.gui.wizards.sale import SaleWizard

from stoq.gui.application import SearchableAppWindow

_ = gettext.gettext


class TillApp(SearchableAppWindow):

    app_name = _('Till')
    app_icon_name = 'stoq-till-app'
    gladefile = 'till'
    searchbar_table = Sale
    searchbar_result_strings = (_('sale'), _('sales'))
    searchbar_labels = (_('Sales Matching:'),)
    klist_name = 'sales'

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)
        if not sysparam(self.conn).CONFIRM_SALES_ON_TILL:
            self.confirm_order_button.hide()
        self._setup_widgets()
        self.searchbar.search_items()
        self._update_widgets()

    def get_title(self):
        today_format = _('%d of %B')
        today_str = datetime.datetime.today().strftime(today_format)
        return _('Stoq - %s of %s') % (self.app_name, today_str)

    def _update_total(self, *args):
        self.summary_label.update_total()

    def _setup_widgets(self):
        value_format = '<b>%s</b>'
        self.summary_label = SummaryLabel(klist=self.sales,
                                          column='total_sale_amount',
                                          label='<b>Total:</b>',
                                          value_format=value_format)
        self.summary_label.show()
        self.list_vbox.pack_start(self.summary_label, False)

    def _update_widgets(self, *args):
        has_till = get_current_till_operation(self.conn) is not None
        self.TillClose.set_sensitive(has_till)
        self.TillOpen.set_sensitive(not has_till)
        self.TillOperations.set_sensitive(has_till)
        has_sales = len(self.sales) > 0
        is_sensitive = bool(has_sales and self.sales.get_selected())
        self.confirm_order_button.set_sensitive(is_sensitive)
        self._update_total()

    def on_searchbar_activate(self, slave, objs):
        SearchableAppWindow.on_searchbar_activate(self, slave, objs)
        self._update_widgets()

    def _format_order_number(self, order_number):
        # FIXME We will remove this method after bug 2214
        if not order_number:
            return 0
        return order_number

    def get_columns(self):
        return [Column('order_number', title=_('Order'), width=100, 
                       format_func=self._format_order_number,
                       data_type=int, sorted=True),
                Column('open_date', title=_('Date'), width=120, 
                       data_type=datetime.date),
                ForeignKeyColumn(Person, 'name', title=_('Client'), expand=True,
                                 data_type=str, obj_field='client',
                                 adapted=True),
                Column('total_sale_amount', title=_('Total'), width=150, 
                       data_type=currency)]

    def get_extra_query(self):
        q1 = Sale.q.clientID == PersonAdaptToClient.q.id
        q2 = PersonAdaptToClient.q._originalID == Person.q.id
        q3 = Sale.q.status == Sale.STATUS_OPENED
        return AND(q1, q2, q3)

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

    def _confirm_order(self):
        rollback_and_begin(self.conn)
        sale = self.sales.get_selected()
        title = _('Confirm Sale')
        model = self.run_dialog(SaleWizard, self.conn, sale, title=title,
                                edit_mode=True)
        if not finish_transaction(self.conn, model, keep_transaction=True):
            return
        if not emit_coupon(sale, self.conn):
            return
        self.conn.commit()
        self.searchbar.search_items()

    #
    # Kiwi callbacks
    #
   
    def on_confirm_order_button__clicked(self, *args):
        self._confirm_order()

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

    def on_sales__double_click(self, *args):
        self._confirm_order()

    def on_sales__selection_changed(self, klist, data):
        self.confirm_order_button.set_sensitive(bool(data))
