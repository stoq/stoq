# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##
##
""" Receiving wizard definition """

import datetime
from decimal import Decimal

import gtk
from kiwi.datatypes import currency
from kiwi.ui.widgets.list import Column

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.base.search import SearchBar
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.editors import NoteEditor
from stoqlib.gui.slaves.sale import DiscountChargeSlave
from stoqlib.gui.search.product import ProductSearch
from stoqlib.gui.wizards.abstract import AbstractProductStep
from stoqlib.gui.dialogs.purchasedetails import PurchaseDetailsDialog
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.runtime import get_current_user
from stoqlib.lib.validators import format_quantity
from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.person import Person
from stoqlib.domain.purchase import PurchaseOrder, PurchaseOrderView
from stoqlib.domain.product import Product
from stoqlib.domain.receiving import (ReceivingOrder, ReceivingOrderItem,
                                      get_receiving_items_by_purchase_order)
from stoqlib.domain.interfaces import IUser, ISupplier, ISellable, ITransporter

_ = stoqlib_gettext


#
# Wizard Steps
#


class ReceivingInvoiceStep(WizardEditorStep):
    gladefile = 'ReceivingInvoiceStep'
    model_type = ReceivingOrder
    proxy_widgets = ('transporter',
                     'products_total',
                     'freight',
                     'ipi',
                     'cfop',
                     'receiving_number',
                     'branch',
                     'supplier',
                     'supplier_label',
                     'order_number',
                     'invoice_total',
                     'invoice_number',
                     'icms_total')

    def _update_totals(self, *args):
        self.proxy.update('products_total')

    # We will avoid duplicating code like when setting up entry completions
    # on bug 2275.
    def _setup_transporter_entry(self):
        table = Person.getAdapterClass(ITransporter)
        transporters = table.get_active_transporters(self.conn)
        items = [(t.get_adapted().name, t) for t in transporters]
        self.transporter.prefill(items)

    def _setup_supplier_entry(self):
        table = Person.getAdapterClass(ISupplier)
        suppliers = table.get_active_suppliers(self.conn)
        items = [(s.get_adapted().name, s) for s in suppliers]
        self.supplier.prefill(items)

    def _setup_widgets(self):
        purchase_widgets = (self.purchase_details_label,
                            self.purchase_number_label,
                            self.purchase_supplier_label,
                            self.order_number, self.supplier_label)
        if self.model.purchase:
            for widget in purchase_widgets:
                widget.show()
            self.receiving_supplier_label.hide()
            self.supplier.hide()
        else:
            for widget in purchase_widgets:
                widget.hide()
            self.receiving_supplier_label.show()
            self.supplier.show()
        self._setup_transporter_entry()
        self._setup_supplier_entry()
        cfop_items = [(item.get_full_description(), item)
                        for item in CfopData.select(connection=self.conn)]
        self.cfop.prefill(cfop_items)

    #
    # WizardStep hooks
    #

    def has_next_step(self):
        return False

    def post_init(self):
        self.transporter.grab_focus()
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    ReceivingInvoiceStep.proxy_widgets)
        if self.wizard.edit_mode:
            return
        self.model.invoice_total = self.model.get_products_total()
        self.proxy.update('invoice_total')
        purchase = self.model.purchase
        if purchase:
            transporter = purchase.transporter
            self.model.transporter = transporter
            self.proxy.update('transporter')
            self.model.supplier = purchase.supplier
            self.proxy.update('supplier')
            if purchase.freight:
                freight_value = (self.model.get_products_total() *
                                 purchase.freight / 100)
                self.model.freight_total = freight_value
                self.proxy.update('freight_total')

    def setup_slaves(self):
        slave_holder = 'discount_charge_holder'
        if self.get_slave(slave_holder):
            return
        if not self.wizard.edit_mode:
            self.model.reset_discount_and_charge()
        self.discount_charge_slave = DiscountChargeSlave(self.conn, self.model,
                                                         ReceivingOrder)
        self.attach_slave(slave_holder, self.discount_charge_slave)
        self.discount_charge_slave.connect('discount-changed',
                                           self._update_totals)
        self._update_totals()

    #
    # Callbacks
    #

    def after_ipi__changed(self, *args):
        self._update_totals()

    def after_freight__changed(self, *args):
        self._update_totals()

    def on_notes_button__clicked(self, *args):
        run_dialog(NoteEditor, self, self.conn, self.model, 'notes',
                   title=_('Additional Information'))


class ReceivingOrderProductStep(AbstractProductStep):
    model_type = ReceivingOrder
    item_table = ReceivingOrderItem
    summary_label_text = "<b>%s</b>" % _('Total Received:')

    def __init__(self, wizard, previous, conn, model):
        AbstractProductStep.__init__(self, wizard, previous, conn, model)
        self.add_product_button.hide()

    def get_columns(self):
        return [Column('sellable.base_sellable_info.description',
                       title=_('Description'),
                       data_type=str, expand=True, searchable=True),
                Column('quantity_received', title=_('Quantity'),
                       data_type=float, width=90,
                       format_func=format_quantity, editable=True),
                Column('sellable.unit_description', title=_('Unit'),
                        data_type=str, width=50),
                Column('cost', title=_('Cost'), data_type=currency,
                       editable=True, width=90),
                Column('total', title=_('Total'), data_type=currency,
                       width=100)]

    def get_order_item(self, sellable, cost, quantity):
        return ReceivingOrderItem(connection=self.conn, sellable=sellable,
                                  receiving_order=self.model,
                                  cost=cost, quantity_received=quantity)

    def get_saved_items(self):
        if not self.model.purchase:
            return []
        return get_receiving_items_by_purchase_order(self.model.purchase,
                                                     self.model)
    #
    # WizardStep hooks
    #

    def next_step(self):
        return ReceivingInvoiceStep(self.conn, self.wizard,
                                    self.model, self)

    #
    # callbacks
    #

    def on_product_button__clicked(self, *args):
        # We are going to call a SearchEditor subclass which means
        # database synchronization... Outch, time to commit !
        table = Product.getAdapterClass(ISellable)
        product_statuses = [table.STATUS_AVAILABLE, table.STATUS_SOLD]
        self.conn.commit()
        products = run_dialog(ProductSearch, self, self.conn,
                              hide_footer=False, hide_toolbar=True,
                              hide_price_column=True,
                              selection_mode=gtk.SELECTION_MULTIPLE,
                              use_product_statuses=product_statuses)
        for product in products:
            self._update_list(product)


class PurchaseSelectionStep(WizardEditorStep):
    gladefile = 'PurchaseSelectionStep'
    model_type = ReceivingOrder

    def __init__(self, wizard, conn, model):
        WizardEditorStep.__init__(self, conn, wizard, model)
        self._update_view()

    def _refresh_next(self, validation_value):
        if sysparam(self.conn).RECEIVE_PRODUCTS_WITHOUT_ORDER:
            validation_value = True
        else:
            validation_value = len(self.orders) == 1
        self.wizard.refresh_next(validation_value)

    def _get_columns(self):
        return [Column('order_number', title=_('Number'), sorted=True,
                       data_type=str, width=100),
                Column('open_date', title=_('Date Started'),
                       data_type=datetime.date),
                Column('supplier_name', title=_('Supplier'),
                       data_type=str, searchable=True, width=160),
                Column('ordered_quantity', title=_('Qty Ordered'),
                       data_type=Decimal, width=120,
                       format_func=format_quantity),
                Column('received_quantity', title=_('Qty Received'),
                       data_type=Decimal, width=120,
                       format_func=format_quantity),
                Column('total', title=_('Order Total'),
                       data_type=currency, width=120)]

    def _get_extra_query(self):
        return PurchaseOrderView.q.status == PurchaseOrder.ORDER_CONFIRMED

    def on_searchbar_before_activate(self, *args):
        self.conn.commit()

    def on_searchbar_activate(self, slave, objs):
        """Use this callback with SearchBar search-activate signal"""
        self.orders.add_list(objs, clear=True)

    def _update_view(self):
        has_selection = self.orders.get_selected() is not None
        self.details_button.set_sensitive(has_selection)

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.register_validate_function(self._refresh_next)
        self.force_validation()

    def next_step(self):
        selected = self.orders.get_selected()
        if selected:
            self.model.purchase = PurchaseOrder.get(selected.id,
                                                    connection=self.conn)
            self.model.supplier = self.model.purchase.supplier
            self.model.transporter = self.model.purchase.transporter
        else:
            self.model.purchase = None
        return ReceivingOrderProductStep(self.wizard, self, self.conn,
                                         self.model)

    def has_previous_step(self):
        return False

    def setup_slaves(self):
        self.order_label.set_size('large')
        self.order_label.set_bold(True)
        self.orders.set_columns(self._get_columns())
        self.searchbar = SearchBar(self.conn, PurchaseOrderView,
                                   self._get_columns(),
                                   searching_by_date=True)
        self.searchbar.register_extra_query_callback(self._get_extra_query)
        self.searchbar.set_result_strings(_('order'), _('orders'))
        self.searchbar.set_searchbar_labels(_('Orders Maching:'))
        self.searchbar.connect('before-search-activate',
                               self.on_searchbar_before_activate)
        self.searchbar.connect('search-activate', self.on_searchbar_activate)
        self.attach_slave('searchbar_holder', self.searchbar)
        self.searchbar.set_focus()

    #
    # Kiwi callbacks
    #

    def on_orders__selection_changed(self, *args):
        self.force_validation()
        self._update_view()

    def on_details_button__clicked(self, *args):
        selected = self.orders.get_selected()
        if not selected:
            raise ValueError('You should have one order selected '
                             'at this point, got nothing')
        order = PurchaseOrder.get(selected.id, connection=self.conn)
        run_dialog(PurchaseDetailsDialog, self, self.conn, model=order)


#
# Main wizard
#

class ReceivingOrderWizard(BaseWizard):
    title = _("Receiving Order")
    size = (750, 550)

    def __init__(self, conn):
        model = self._create_model(conn)
        first_step = PurchaseSelectionStep(self, conn, model)
        BaseWizard.__init__(self, conn, first_step, model)

    def _create_model(self, conn):
        current_user = get_current_user()
        current_user = Person.iget(IUser, current_user.id, connection=conn)
        branch = sysparam(conn).CURRENT_BRANCH
        cfop = sysparam(conn).DEFAULT_RECEIVING_CFOP
        return ReceivingOrder(responsible=current_user, supplier=None,
                              invoice_number=None, branch=branch, cfop=cfop,
                              connection=conn)

    #
    # WizardStep hooks
    #

    def finish(self):
        if not self.model.get_valid():
            self.model.set_valid()
        self.retval = self.model
        self.model.confirm()
        self.close()
