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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##
"""
stoq/gui/purchase/purchase.py:

    Main gui definition for purchase application.
"""

import gettext
import datetime

import gtk
from kiwi.ui.widgets.list import Column
from stoqlib.gui.search import SearchBar
from stoqlib.gui.columns import ForeignKeyColumn
from stoqlib.database import rollback_and_begin
from sqlobject.sqlbuilder import AND

from stoq.gui.application import AppWindow
from stoq.gui.search.person import SupplierSearch
from stoq.gui.slaves.filter import FilterSlave
from stoq.domain.purchase import PurchaseOrder
from stoq.domain.person import Person
from stoq.domain.interfaces import ISupplier
from stoq.lib.runtime import new_transaction
from stoq.lib.validators import get_formatted_price
from stoq.lib.defaults import ALL_ITEMS_INDEX

_ = gettext.gettext


class PurchaseApp(AppWindow):
   
    app_name = _('Purchase')
    gladefile = "purchase"
    
    widgets = ('total_ordered_lbl',
               'ordered_lbl',
               'received_lbl',
               'total_received_lbl',
               'purchase_list',
               'edit_button',
               'confirm_button',
               'print_button')
               
    
    def __init__(self, app):
        self.conn = new_transaction()
        AppWindow.__init__(self, app)
        self._setup_widgets()
        self._setup_slaves()
        self._update_view()

    def _setup_widgets(self):
        labels = [self.ordered_lbl, self.received_lbl,
                  self.total_ordered_lbl, self.total_received_lbl]
        for label in labels:
            label.set_size('medium')
            label.set_bold(True)
        self.purchase_list.set_columns(self._get_columns())
        self.purchase_list.set_selection_mode(gtk.SELECTION_MULTIPLE)

    def _setup_slaves(self):
        combo_items = [(text, value) 
                        for value, text in PurchaseOrder.statuses.items()]
        first_item = (_('All Orders'), ALL_ITEMS_INDEX)
        combo_items.append(first_item)
        self.filter_slave = FilterSlave(combo_items,
                                        selected=ALL_ITEMS_INDEX)

        self.search_bar = SearchBar(self, PurchaseOrder,
                                    self._get_columns(), 
                                    filter_slave=self.filter_slave,
                                    searching_by_date=True)
        self.search_bar.set_searchbar_labels(_('Containing:'),
                                             _('Find orders from:')) 
        self.search_bar.set_result_strings(_('order'), _('orders'))

        self.filter_slave.connect('status-changed',
                                  self.search_bar.search_items)
        self.attach_slave("search_bar_holder", self.search_bar)

    def _update_view(self):
        has_purchases = len(self.purchase_list) > 0
        widgets = [self.edit_button, self.confirm_button, self.print_button]
        for widget in widgets:
            widget.set_sensitive(has_purchases)
        one_selected = len(self.purchase_list.get_selected_rows()) == 1
        self.edit_button.set_sensitive(one_selected)
        self._update_totals()

    def _update_totals(self):
        total_ordered = 0.0
        total_received = 0.0
        for order in self.purchase_list:
            total_ordered += order.get_purchase_total()
            total_received += order.get_received_total()
        self.total_ordered_lbl.set_text(get_formatted_price(total_ordered))
        self.total_received_lbl.set_text(get_formatted_price(total_received))

    def _get_columns(self):
        return [Column('order_number', title=_('Number'), sorted=True,
                       data_type=int, width=100, format='%03d'),
                Column('open_date', title=_('Date Started'),
                       data_type=datetime.date, width=100),
                ForeignKeyColumn(Person, 'name', title=_('Supplier'), 
                                 data_type=str,
                                 obj_field='supplier._original',
                                 searchable=True, width=270),
                Column('status_str', title=_('Status'), data_type=str,
                       width=100),
                Column('purchase_total', title=_('Ordered'), 
                       data_type=float, width=100,
                       format_func=get_formatted_price,
                       justify=gtk.JUSTIFY_RIGHT),
                Column('received_total', title=_('Received'), 
                       format_func=get_formatted_price,
                       data_type=float, justify=gtk.JUSTIFY_RIGHT)]



    #
    # Hooks
    #



    def update_klist(self, purchases=None):
        """Hook called by SearchBar"""
        rollback_and_begin(self.conn)
        self.purchase_list.clear()
        for purchase in purchases:
            # Since search bar change the connection internally we must get
            # the objects back in our main connection
            obj = PurchaseOrder.get(purchase.id, connection=self.conn)
            self.purchase_list.append(obj)
        self._update_view()


    def get_extra_query(self):
        supplier_table = Person.getAdapterClass(ISupplier)
        q1 = PurchaseOrder.q.supplierID == supplier_table.q.id
        q2 = supplier_table.q._originalID == Person.q.id
        status = self.filter_slave.get_selected_status()
        if status != ALL_ITEMS_INDEX:
            q3 = PurchaseOrder.q.status == status
            return AND(q1, q2, q3)
        return AND(q1, q2)



    #
    # Callbacks
    #

    

    def on_purchase_list__selection_changed(self, *args):
        self._update_view()

    def _on_suppliers_action__clicked(self, *args):
        self.run_dialog(SupplierSearch, hide_footer=True)
            
    def _on_products_action__clicked(self, *args):
        # TODO bug 2206
        pass

    def _on_order_action__clicked(self, *args):
        # TODO bug 2211
        pass
