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
from decimal import Decimal

import gtk
from kiwi.datatypes import currency
from kiwi.python import all
from kiwi.ui.widgets.list import Column, SummaryLabel
from stoqlib.database.database import rollback_and_begin
from stoqlib.lib.message import warning, yesno
from stoqlib.domain.purchase import PurchaseOrder, PurchaseOrderView
from stoqlib.domain.interfaces import IPaymentGroup
from stoqlib.domain.payment.methods import MoneyPM
from stoqlib.domain.payment.payment import Payment
from stoqlib.gui.search.personsearch import SupplierSearch, TransporterSearch
from stoqlib.gui.wizards.purchasewizard import PurchaseWizard
from stoqlib.gui.search.categorysearch import (SellableCategorySearch,
                                               BaseSellableCatSearch)
from stoqlib.gui.search.productsearch import ProductSearch
from stoqlib.gui.search.servicesearch import ServiceSearch
from stoqlib.gui.dialogs.purchasedetails import PurchaseDetailsDialog
from stoqlib.reporting.purchase import PurchaseReport
from stoqlib.lib.defaults import ALL_ITEMS_INDEX, METHOD_MONEY
from stoqlib.lib.validators import format_quantity
from stoqlib.lib.parameters import sysparam

from stoq.gui.application import SearchableAppWindow

_ = gettext.gettext

class PurchaseApp(SearchableAppWindow):
    app_name = _('Purchase')
    app_icon_name = 'stoq-purchase-app'
    gladefile = "purchase"
    searchbar_table = PurchaseOrderView
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
        label = '<b>%s</b>' % _('Total:')
        self.summary_total = SummaryLabel(klist=self.orders,
                                          column='total',
                                          label=label,
                                          value_format=value_format)
        self.summary_total.show()
        self.summary_hbox.pack_start(self.summary_total, False)
        self.send_to_supplier_button.set_sensitive(False)

    def _update_totals(self):
        self.summary_total.update_total()
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
        if selection:
            can_send_supplier = all(
                order.status == PurchaseOrder.ORDER_PENDING
                for order in selection)
        else:
            can_send_supplier = False

        if one_selected:
            can_edit = selection[0].status == PurchaseOrder.ORDER_PENDING
        self.edit_button.set_sensitive(can_edit)
        self.send_to_supplier_button.set_sensitive(can_send_supplier)
        self.details_button.set_sensitive(one_selected)

    def _open_order(self, order=None, edit_mode=False):
        order = self.run_dialog(PurchaseWizard, self.conn, order,
                                edit_mode)
        if not order:
            return
        self.conn.commit()
        return order

    def _edit_order(self):
        selected = self.orders.get_selected_rows()
        qty = len(selected)
        if qty != 1:
            raise ValueError('You should have only one order selected, '
                             'got %d instead' % qty )
        order = PurchaseOrder.get(selected[0].id, connection=self.conn)
        self._open_order(order, edit_mode=True)
        self.searchbar.search_items()

    def _confirm_order(self, order):
        # FIXME: HACK to avoid creating till entry when payment method
        # is money.  So, directly from PurchaseOrder's confirm_order()
        # implementation, we have:
        if order.status != PurchaseOrder.ORDER_PENDING:
            raise ValueError('Invalid order status, it should be '
                             'ORDER_PENDING, got %s'
                             % PurchaseOrder.get_status_str(order.status))
        if sysparam(self.conn).USE_PURCHASE_PREVIEW_PAYMENTS:
            group = IPaymentGroup(order, None)
            if not group:
                raise ValueError('You must have a IPaymentGroup facet '
                                 'defined at this point')
            if group.default_method == METHOD_MONEY:
                destination = sysparam(self.conn).DEFAULT_PAYMENT_DESTINATION
                method = MoneyPM.selectOne(connection=self.conn)
                first_due_date = order.expected_receival_date
                Payment(value=order.get_purchase_total(), method=method,
                        due_date=first_due_date, group=group, till=None,
                        destination=destination, connection=self.conn)
            else:
                group.create_preview_outpayments()
        order.status = PurchaseOrder.ORDER_CONFIRMED
        order.confirm_date = datetime.datetime.now()

    def _run_details_dialog(self):
        orders = self.orders.get_selected_rows()
        qty = len(orders)
        if qty != 1:
            raise ValueError('You should have only one order selected '
                             'at this point, got %d' % qty)
        order = PurchaseOrder.get(orders[0].id, connection=self.conn)
        self.run_dialog(PurchaseDetailsDialog, self.conn, model=order)

    def _send_selected_items_to_supplier(self):
        rollback_and_begin(self.conn)

        orders = self.orders.get_selected_rows()
        valid_orders = [order for order in orders
                                  if order.status ==
                                     PurchaseOrder.ORDER_PENDING]

        valid_orders_len = len(valid_orders)
        if not valid_orders_len:
            return warning(_("There are no orders with status "
                             "pending in the selection"))
        elif valid_orders_len > 1:
            msg = (_("The %d selected orders will be marked as sent.")
                   % valid_orders_len)
        else:
            msg = _('The selected order will be marked as sent.')
        invalid_qty = len(orders) - valid_orders_len
        if valid_orders_len != len(orders):
            msg += "\n"
            msg += _(u"Warning: there are %d order(s) with "
                     "status different than pending that "
                     "will not be included") % invalid_qty
        if yesno(msg, gtk.RESPONSE_NO, _(u"Cancel"), _(u"Confirm")):
            return
        for item in valid_orders:
            order = PurchaseOrder.get(item.id, connection=self.conn)
            self._confirm_order(order)
        self.conn.commit()
        self.searchbar.search_items()

    def _print_selected_items(self):
        items = self.orders.get_selected_rows() or self.orders
        self.searchbar.print_report(PurchaseReport, items)

    #
    # Hooks
    #

    def get_extra_query(self):
        status = self.filter_slave.get_selected_status()
        if status != ALL_ITEMS_INDEX:
            return PurchaseOrderView.q.status == status

    def get_filterslave_default_selected_item(self):
        return PurchaseOrder.ORDER_CONFIRMED

    def get_filter_slave_items(self):
        items = [(text, value)
                    for value, text in PurchaseOrder.statuses.items()]
        items.insert(0, (_('Any'), ALL_ITEMS_INDEX))
        return items

    def on_searchbar_activate(self, slave, objs):
        SearchableAppWindow.on_searchbar_activate(self, slave, objs)
        self._update_totals()

    def get_columns(self):
        return [Column('order_number', title=_('Number'), sorted=True,
                       data_type=str, width=80),
                Column('open_date', title=_('Date Started'),
                       data_type=datetime.date),
                Column('supplier_name', title=_('Supplier'),
                       data_type=str, searchable=True, width=200,
                       expand=True),
                Column('ordered_quantity', title=_('Qty Ordered'),
                       data_type=Decimal, width=120,
                       format_func=format_quantity),
                Column('received_quantity', title=_('Qty Received'),
                       data_type=Decimal, width=150,
                       format_func=format_quantity),
                Column('total', title=_('Order Total'),
                       data_type=currency, width=110)]

    #
    # Kiwi Callbacks
    #

    def key_control_a(self, *args):
        # FIXME Remove this method after gazpacho bug fix.
        self._open_order()

    def on_orders__row_activated(self, klist, purchase_order_view):
        self._run_details_dialog()

    def on_details_button__clicked(self, button):
        self._run_details_dialog()

    def on_orders__selection_changed(self, orders, selected):
        self._update_view()

    def _on_orders__double_click(self, orders, order):
        self._run_details_dialog()

    def _on_orders__has_rows(self, orders, has_items):
        self._update_list_aware_widgets(has_items)

    def on_edit_button__clicked(self, button):
        self._edit_order()

    def on_print_button__clicked(self, button):
        self._print_selected_items()

    def on_send_to_supplier_button__clicked(self, button):
        self._send_selected_items_to_supplier()

    def on_Categories__activate(self, action):
        self.run_dialog(SellableCategorySearch, self.conn)

    # FIXME: Kiwi autoconnection OR rename, see #2323

    def _on_suppliers_action_clicked(self, action):
        self.run_dialog(SupplierSearch, self.conn, hide_footer=True)

    def _on_products_action_clicked(self, action):
        self.run_dialog(ProductSearch, self.conn, hide_price_column=True)

    def _on_order_action_clicked(self, action):
        self._open_order()
        self.searchbar.search_items()

    def _on_send_to_supplier_action_clicked(self, action):
        self._send_selected_items_to_supplier()

    def _on_base_categories_action_clicked(self, action):
        self.run_dialog(BaseSellableCatSearch, self.conn)

    def _on_services_action_clicked(self, action):
        self.run_dialog(ServiceSearch, self.conn, hide_price_column=True)

    def _on_transporters_action_clicked(self, action):
        self.run_dialog(TransporterSearch, self.conn, hide_footer=True)

