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
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##
"""
stoq/gui/receivable/receivable.py:

    Implementation of receivable application.
"""

import gtk
import gettext
import datetime

from kiwi.ui.widgets.list import Column, SummaryLabel
from stoqlib.gui.search import SearchBar
from stoqlib.database import rollback_and_begin

from stoq.domain.payment.base import Payment
from stoq.lib.runtime import new_transaction
from stoq.lib.validators import get_formatted_price, get_price_format_str
from stoq.lib.defaults import ALL_ITEMS_INDEX
from stoq.gui.application import AppWindow
from stoq.gui.slaves.filter import FilterSlave

_ = gettext.gettext

class ReceivableApp(AppWindow):

    app_name = _('Receivable')
    gladefile = 'receivable'
    widgets = ('receivable_list',
               'list_vbox',
               'cancel_button',
               'edit_button',
               'add_button',
               'details_button')

    def __init__(self, app):
        AppWindow.__init__(self, app)
        self.conn = new_transaction()
        self._setup_slaves()
        self._setup_widgets()
        self._update_widgets()

    def _setup_widgets(self):
        self.receivable_list.set_columns(self._get_columns())
        self.receivable_list.set_selection_mode(gtk.SELECTION_MULTIPLE)
        value_format = '<b>%s</b>' % get_price_format_str()
        self.summary_label = SummaryLabel(klist=self.receivable_list,
                                          column='value',
                                          label='<b>Total:</b>',
                                          value_format=value_format)
        self.summary_label.show()
        self.list_vbox.pack_start(self.summary_label, False)


    def _update_widgets(self):
        has_sales = len(self.receivable_list) > 0
        widgets = [self.cancel_button, self.details_button,
                   self.edit_button, self.add_button]
        for widget in widgets:
            widget.set_sensitive(has_sales)
        self._update_total_label()

    def _update_total_label(self):
        self.summary_label.update_total()

    def _setup_slaves(self):
        items = [(value, key) for key, value in Payment.statuses.items()]
        items.append((_('Any'), ALL_ITEMS_INDEX))
        self.filter_slave = FilterSlave(items, selected=ALL_ITEMS_INDEX)
        self.filter_slave.set_filter_label(_('Show:'))
        self.searchbar = SearchBar(self, Payment, self._get_columns(),
                                   filter_slave=self.filter_slave,
                                   searching_by_date=True)
        self.searchbar.set_result_strings(_('payment'), _('payments'))
        self.searchbar.set_searchbar_labels(_('payments matching:'))
        self.filter_slave.connect('status-changed', 
                                  self.searchbar.search_items)
        self.attach_slave('searchbar_holder', self.searchbar)

    def _get_payment_id(self, value):
        if not value:
            return
        return '%03d' % value

    #
    # SearchBar hooks
    #

    def _get_columns(self):
        return [Column('payment_id', title=_('Number'), width=100, 
                       data_type=str, sorted=True,
                       justify=gtk.JUSTIFY_RIGHT,
                       format_func=self._get_payment_id),
                Column('description', title=_('Description'), width=220, 
                       data_type=str),
                Column('thirdparty_name', title=_('Drawee'), data_type=str,
                       width=170),
                Column('due_date', title=_('Due Date'),
                       justify=gtk.JUSTIFY_RIGHT,
                       data_type=datetime.date, width=90),
                Column('status_str', title=_('Status'), width=80, 
                       data_type=str), 
                Column('value', title=_('Value'), 
                       data_type=float, justify=gtk.JUSTIFY_RIGHT,
                       format_func=get_formatted_price)]

    def get_extra_query(self):
        status = self.filter_slave.get_selected_status()
        if status == ALL_ITEMS_INDEX:
            return
        return Payment.q.status == status

    def update_klist(self, payments=[]):
        rollback_and_begin(self.conn)
        self.receivable_list.clear()
        for payment in payments:
            # Since search bar change the connection internally we must get
            # the objects back in our main connection
            obj = Payment.get(payment.id, connection=self.conn)
            self.receivable_list.append(obj)
        self._update_widgets()

    #
    # Kiwi callbacks
    #

    def _on_conference_action_clicked(self, *args):
        pass

    def _on_bills_action_clicked(self, *args):
        pass
