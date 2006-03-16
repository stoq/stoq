# -*- Mode: Python; coding: utf-8 -*-
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##
""" Main gui definition for purchase application.  """

import gettext
import datetime

import gtk
from kiwi.datatypes import currency
from kiwi.ui.widgets.list import Column, SummaryLabel
from sqlobject.sqlbuilder import AND
from stoqlib.gui.base.columns import ForeignKeyColumn
from stoqlib.gui.base.dialogs import confirm_dialog, notify_dialog
from stoqlib.database import rollback_and_begin
from stoqlib.lib.defaults import ALL_ITEMS_INDEX
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import ISupplier
from stoqlib.gui.search.person import SupplierSearch, TransporterSearch
from stoqlib.gui.wizards.purchase import PurchaseWizard
from stoqlib.gui.search.category import (BaseSellableCatSearch,
                                         SellableCatSearch)
from stoqlib.gui.search.product import ProductSearch
from stoqlib.gui.search.service import ServiceSearch
from stoqlib.gui.dialogs.purchasedetails import PurchaseDetailsDialog
from stoqlib.reporting.purchase import PurchaseReport

from stoq.gui.application import SearchableAppWindow

_ = gettext.gettext

class PurchaseApp(SearchableAppWindow):
    app_name = _('Purchase')
    app_icon_name = 'stoq-purchase-app'
    gladefile = "purchase"
    searchbar_table = PurchaseOrder
    searchbar_use_dates = True
    searchbar_result_strings = (_('order'), _('orders'))
    searchbar_labels = (_('matching:'),)
    filter_slave_label = _('Show orders with status')
    klist_selection_mode = gtk.SELECTION_MULTIPLE
    klist_name = 'orders'

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)
        self._setup_widgets()
        self._update_view()

    def _setup_widgets(self):
        value_format = '<b>%s</b>'
        label = '<b>%s</b>' % _('Totals:')
        self.summary_total = SummaryLabel(klist=self.orders,
                                          column='purchase_total',
                                          label=label,
                                          value_format=value_format)
        self.summary_total.show()
        self.summary_received = SummaryLabel(klist=self.orders,
                                             column='received_total',
                                             label='',
                                             value_format=value_format)
        self.summary_received.show()
        self.summary_hbox.pack_start(self.summary_total, False)
        self.summary_hbox.pack_end(self.summary_received, False)

    def _update_totals(self):
        self.summary_total.update_total()
        self.summary_received.update_total()
        self._update_view()

    def _update_list_aware_widgets(self, has_items):
        for widget in (self.edit_button, self.details_button,
                       self.print_button,
                       self.send_to_supplier_action):
            widget.set_sensitive(has_items)

    def _update_view(self):
        self._update_list_aware_widgets(len(self.orders))
        selection = self.orders.get_selected_rows()
        can_edit = one_selected = len(selection) == 1
        if one_selected:
            can_edit = selection[0].status == PurchaseOrder.ORDER_PENDING
        self.edit_button.set_sensitive(can_edit)
        self.details_button.set_sensitive(one_selected)

    def _open_order(self, order=None, edit_mode=False):
        order = self.run_dialog(PurchaseWizard, self.conn, order,
                                edit_mode)
        if not order:
            return
        self.conn.commit()
        return order

    def _edit_order(self):
        order = self.orders.get_selected_rows()
        qty = len(order)
        if qty != 1:
            raise ValueError('You should have only one order selected, '
                             'got %d instead' % qty )
        self._open_order(order[0], edit_mode=True)
        self.searchbar.search_items()

    def _run_details_dialog(self, *args):
        orders = self.orders.get_selected_rows()
        qty = len(orders)
        if qty != 1:
            raise ValueError('You should have only one order selected '
                             'at this point, got %d' % qty)
        self.run_dialog(PurchaseDetailsDialog, self.conn, model=orders[0])

    def _send_selected_items_to_supplier(self):
        rollback_and_begin(self.conn)

        orders = self.orders.get_selected_rows()
        valid_orders = [i for i in orders
                            if i.status == PurchaseOrder.ORDER_PENDING]
        valid_orders_len = len(valid_orders)
        if not valid_orders_len:
            return notify_dialog(_("There are no orders with status "
                                   "pending in the selection"))
        elif valid_orders_len > 1:
            msg = (_("The %d selected orders will be market as sent.")
                   % valid_orders_len)
        else:
            msg = _('The selected order will be market as sent.')
        invalid_qty = len(orders) - valid_orders_len
        if valid_orders_len != len(orders):
            msg += "\n%s" % (_("Warning: there are %d order(s) with "
                               "status different than pending that "
                               "will not be included" % invalid_qty))
        title = _('Send order to supplier')
        if not confirm_dialog(msg, title, ok_label="C_onfirm"):
            return
        for order in valid_orders:
            order.confirm_order()
        self.conn.commit()
        self.searchbar.search_items()

    def _print_selected_items(self):
        items = self.orders.get_selected_rows() or self.orders
        self.searchbar.print_report(PurchaseReport, items)

    #
    # Hooks
    #

    def get_extra_query(self):
        supplier_table = Person.getAdapterClass(ISupplier)
        q1 = PurchaseOrder.q.supplierID == supplier_table.q.id
        q2 = supplier_table.q._originalID == Person.q.id
        status = self.filter_slave.get_selected_status()
        if status != ALL_ITEMS_INDEX:
            q3 = PurchaseOrder.q.status == status
            return AND(q1, q2, q3)
        return AND(q1, q2)

    def get_filter_slave_items(self):
        items = [(text, value)
                    for value, text in PurchaseOrder.statuses.items()]
        first_item = (_('Any'), ALL_ITEMS_INDEX)
        items.append(first_item)
        return items

    def on_searchbar_activate(self, slave, objs):
        SearchableAppWindow.on_searchbar_activate(self, slave, objs)
        self._update_totals()

    def get_columns(self):
        return [Column('order_number_str', title=_('Number'), sorted=True,
                       data_type=str, width=100),
                Column('open_date', title=_('Date Started'),
                       data_type=datetime.date),
                ForeignKeyColumn(Person, 'name', title=_('Supplier'),
                                 data_type=str,
                                 obj_field='supplier', adapted=True,
                                 searchable=True, width=220),
                Column('status_str', title=_('Status'), data_type=str,
                       width=100),
                Column('purchase_total', title=_('Ordered'),
                       data_type=currency, width=120),
                Column('received_total', title=_('Received'),
                       data_type=currency)]

    #
    # Kiwi Callbacks
    #

    def key_control_a(self, *args):
        # FIXME Remove this method after gazpacho bug fix.
        self._open_order()

    def on_details_button__clicked(self, *args):
        self._run_details_dialog()

    def on_orders__selection_changed(self, *args):
        self._update_view()

    def on_orders__double_click(self, *args):
        self._run_details_dialog()

    def on_print_button__clicked(self, button):
        self._print_selected_items()

    def _on_suppliers_action_clicked(self, *args):
        self.run_dialog(SupplierSearch, self.conn, hide_footer=True)

    def _on_products_action_clicked(self, *args):
        self.run_dialog(ProductSearch, self.conn, hide_price_column=True)

    def _on_order_action_clicked(self, *args):
        self._open_order()
        self.searchbar.search_items()

    def on_edit_button__clicked(self, *args):
        self._edit_order()

    def _on_send_to_supplier_action_clicked(self, *args):
        self._send_selected_items_to_supplier()

    def _on_base_categories_action_clicked(self, *args):
        self.run_dialog(BaseSellableCatSearch, self.conn)

    def _on_categories_action_clicked(self, *args):
        self.run_dialog(SellableCatSearch, self.conn)

    def _on_services_action_clicked(self, *args):
        self.run_dialog(ServiceSearch, self.conn, hide_price_column=True)

    def _on_transporters_action_clicked(self, *args):
        self.run_dialog(TransporterSearch, self.conn, hide_footer=True)

    def on_orders__has_rows(self, klist, has_items):
        self._update_list_aware_widgets(has_items)
