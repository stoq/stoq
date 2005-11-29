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
from kiwi.ui.widgets.list import Column, SummaryLabel
from sqlobject.sqlbuilder import AND
from stoqlib.gui.search import SearchBar
from stoqlib.gui.columns import ForeignKeyColumn
from stoqlib.gui.dialogs import confirm_dialog, notify_dialog
from stoqlib.database import rollback_and_begin, finish_transaction

from stoq.domain.purchase import PurchaseOrder
from stoq.domain.person import Person
from stoq.domain.interfaces import ISupplier
from stoq.lib.runtime import new_transaction
from stoq.lib.validators import get_formatted_price, get_price_format_str
from stoq.lib.defaults import ALL_ITEMS_INDEX
from stoq.gui.application import AppWindow
from stoq.gui.editors.service import ServiceEditor
from stoq.gui.search.person import SupplierSearch, TransporterSearch
from stoq.gui.slaves.filter import FilterSlave
from stoq.gui.wizards.purchase import PurchaseWizard
from stoq.gui.search.category import (BaseSellableCatSearch,
                                      SellableCatSearch)
from stoq.gui.search.product import ProductSearch

_ = gettext.gettext


class PurchaseApp(AppWindow):
   
    app_name = _('Purchase')
    gladefile = "purchase"
    widgets = ('purchase_list',
               'edit_button',
               'details_button',
               'summary_hbox',
               'send_to_supplier_action',
               'print_button')
               
    def __init__(self, app):
        self.conn = new_transaction()
        AppWindow.__init__(self, app)
        self._setup_widgets()
        self._setup_slaves()
        self._update_view()

    def _setup_widgets(self):
        self.purchase_list.set_columns(self._get_columns())
        self.purchase_list.set_selection_mode(gtk.SELECTION_MULTIPLE)
        value_format = '<b>%s</b>' % get_price_format_str()
        self.summary_total = SummaryLabel(klist=self.purchase_list,
                                          column='purchase_total',
                                          label='<b>Totals:</b>',
                                          value_format=value_format)
        self.summary_total.show()
        self.summary_received = SummaryLabel(klist=self.purchase_list,
                                             column='received_total',
                                             label='',
                                             value_format=value_format)
        self.summary_received.show()
        self.summary_hbox.pack_start(self.summary_total, False)
        self.summary_hbox.pack_end(self.summary_received, False)

    def _setup_slaves(self):
        combo_items = [(text, value) 
                        for value, text in PurchaseOrder.statuses.items()]
        first_item = (_('Any'), ALL_ITEMS_INDEX)
        combo_items.append(first_item)
        self.filter_slave = FilterSlave(combo_items,
                                        selected=ALL_ITEMS_INDEX)
        self.filter_slave.set_filter_label(_('Show:'))

        self.search_bar = SearchBar(self, PurchaseOrder,
                                    self._get_columns(), 
                                    filter_slave=self.filter_slave,
                                    searching_by_date=True)
        self.search_bar.set_searchbar_labels(_('orders matching:'))
        self.search_bar.set_result_strings(_('order'), _('orders'))

        self.filter_slave.connect('status-changed',
                                  self.search_bar.search_items)
        self.attach_slave("search_bar_holder", self.search_bar)

    def _update_view(self):
        has_purchases = len(self.purchase_list) > 0
        widgets = [self.edit_button, self.details_button, self.print_button,
                   self.send_to_supplier_action]
        for widget in widgets:
            widget.set_sensitive(has_purchases)
        selection = self.purchase_list.get_selected_rows()
        can_edit = one_selected = len(selection) == 1
        if one_selected:
            can_edit = (selection[0].status ==
                        PurchaseOrder.ORDER_PENDING)
        self.edit_button.set_sensitive(can_edit)
        self.details_button.set_sensitive(one_selected)
        has_item_selected = len(selection) > 0
        self.print_button.set_sensitive(has_item_selected)
        self.send_to_supplier_action.set_sensitive(has_item_selected)

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
        self.summary_total.update_total()
        self.summary_received.update_total()
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
    
    def _open_order(self, order=None, edit_mode=False):
        order = self.run_dialog(PurchaseWizard, self.conn, order,
                                edit_mode)
        if not order:
            return
        self.conn.commit()
        return order
        
    def _edit_order(self):
        order = self.purchase_list.get_selected_rows()
        qty = len(order)
        if qty != 1:
            raise ValueError('You should have only one order selected, '
                             'got %d instead' % qty )
        self._open_order(order[0], edit_mode=True)
        self.search_bar.search_items()

    #
    # Callbacks
    #

    def key_control_a(self, *args):
        # FIXME Remove this method after gazpacho bug fix.
        self._open_order()

    def on_purchase_list__selection_changed(self, *args):
        self._update_view()

    def on_purchase_list__double_click(self, *args):
        self._edit_order()

    def _on_suppliers_action_clicked(self, *args):
        self.run_dialog(SupplierSearch, hide_footer=True)
            
    def _on_products_action_clicked(self, *args):
        # TODO bug 2206
        conn = new_transaction()
        model = self.run_dialog(ProductSearch, conn)
        finish_transaction(conn, model)

    def _on_order_action_clicked(self, *args):
        self._open_order()
        self.search_bar.search_items()

    def on_edit_button__clicked(self, *args):
        self._edit_order()

    def _on_send_to_supplier_action_clicked(self, *args):
        rollback_and_begin(self.conn)
        orders = self.purchase_list.get_selected_rows()
        valid_orders = [order for order in orders 
                                  if order.status == PurchaseOrder.ORDER_PENDING]
        qty = len(orders)
        invalid_qty = qty - len(valid_orders)
        if invalid_qty == qty:
            notify_dialog('There are no orders with status pending in the '
                          'selection')
            return
        qty -= invalid_qty
        if not qty:
            raise ValueError('You should have at least one order selected '
                             'at this point')
        if qty > 1:
            msg = _('The %d selected orders will be market as sent.') % qty
        else:
            msg = _('The selected order will be market as sent.')
        if invalid_qty:
            msg += ('\nWarning: there are %d order(s) with status different '
                    'than pending that will not be included.' 
                    % invalid_qty)
        title = _('Send order to supplier')
        if not confirm_dialog(msg, title, ok_label="Confirm"):
            return
        for order in valid_orders:
            order.confirm_order()
        self.conn.commit()
        self.search_bar.search_items()

    def _on_base_categories_action_clicked(self, *args):
        self.run_dialog(BaseSellableCatSearch)

    def _on_categories_action_clicked(self, *args):
        self.run_dialog(SellableCatSearch)

    def _on_services_action_clicked(self, *args): 
        conn = new_transaction()
        model = self.run_dialog(ServiceEditor, conn)
        finish_transaction(conn, model)

    def _on_transporters_action_clicked(self, *args): 
        self.run_dialog(TransporterSearch, hide_footer=True)
