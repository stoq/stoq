# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
stoq/gui/wizards/receiving.py:

    Receiving wizard definition
"""

import datetime
import gettext

import gtk
from kiwi.datatypes import currency
from kiwi.ui.widgets.list import Column
from stoqlib.gui.base.wizards import BaseWizardStep, BaseWizard
from stoqlib.gui.base.search import SearchBar
from stoqlib.gui.base.columns import ForeignKeyColumn
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.editors import NoteEditor
from sqlobject.sqlbuilder import AND

from stoqlib.lib.parameters import sysparam
from stoqlib.lib.runtime import get_current_user
from stoqlib.lib.validators import format_quantity, get_price_format_str
from stoqlib.domain.person import Person
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.product import Product
from stoqlib.domain.receiving import (ReceivingOrder, ReceivingOrderItem,
                                      get_receiving_items_by_purchase_order)
from stoqlib.domain.interfaces import IUser, ISupplier, ISellable, ITransporter
from stoqlib.gui.slaves.sale import DiscountChargeSlave
from stoq.gui.search.product import ProductSearch
from stoq.gui.wizards.abstract import AbstractProductStep
from stoq.gui.purchase.details import PurchaseDetailsDialog

_ = gettext.gettext


#
# Wizard Steps
#


class ReceivingInvoiceStep(BaseWizardStep):
    gladefile = 'ReceivingInvoiceStep'
    model_type = ReceivingOrder
    proxy_widgets = ('transporter',
                     'products_total',
                     'order_total',
                     'freight',
                     'ipi',
                     'supplier',
                     'order_number',
                     'invoice_total',
                     'invoice_number',
                     'icms_total')

    def _update_totals(self, *args):
        self.proxy.update_many(['products_total_str', 'order_total_str'])

    # We will avoid duplicating code like when setting up entry completions
    # on bug 2275.
    def _setup_transporter_entry(self):
        table = Person.getAdapterClass(ITransporter)
        transporters = table.get_active_transporters(self.conn)
        names = [t.get_adapted().name for t in transporters]
        self.transporter.set_completion_strings(names, list(transporters))

    def _setup_supplier_entry(self):
        table = Person.getAdapterClass(ISupplier)
        suppliers = table.get_active_suppliers(self.conn)
        names = [t.get_adapted().name for t in suppliers]
        self.supplier.set_completion_strings(names, list(suppliers))

    def _setup_widgets(self):
        if self.model.purchase:
            self.supplier.set_sensitive(False)
        self._setup_transporter_entry()
        self._setup_supplier_entry()
        format_str = get_price_format_str()
        for widget in [self.freight, self.icms_total, self.invoice_total, 
                       self.ipi]:
            widget.set_data_format(format_str)
        
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
        self.model.invoice_total = self.model.get_order_total()
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
                                 purchase.freight / 100.0)
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


class PurchaseSelectionStep(BaseWizardStep):
    gladefile = 'PurchaseSelectionStep'
    model_type = ReceivingOrder

    def __init__(self, wizard, conn, model):
        BaseWizardStep.__init__(self, conn, wizard, model)
        self._update_view()

    def _refresh_next(self, validation_value):
        if sysparam(self.conn).RECEIVE_PRODUCTS_WITHOUT_ORDER:
            validation_value = True
        else:
            validation_value = len(self.orders) == 1
        self.wizard.refresh_next(validation_value)

    def _get_columns(self):
        return [Column('order_number_str', title=_('Number'), sorted=True,
                       data_type=str, width=100),
                Column('open_date', title=_('Date Started'),
                       data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT),
                ForeignKeyColumn(Person, 'name', title=_('Supplier'), 
                                 data_type=str,
                                 obj_field='supplier', adapted=True,
                                 searchable=True, width=270),
                Column('purchase_total', title=_('Ordered'), 
                       data_type=currency, width=120),
                Column('received_total', title=_('Received'), 
                       data_type=currency)]

    def _get_extra_query(self):
        supplier_table = Person.getAdapterClass(ISupplier)
        q1 = PurchaseOrder.q.supplierID == supplier_table.q.id
        q2 = supplier_table.q._originalID == Person.q.id
        q3 = PurchaseOrder.q.status == PurchaseOrder.ORDER_CONFIRMED
        return AND(q1, q2, q3)

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
        self.model.purchase = self.orders.get_selected()
        return ReceivingOrderProductStep(self.wizard, self, self.conn, 
                                         self.model)
              
    def has_previous_step(self):
        return False

    def setup_slaves(self):
        self.order_label.set_size('large')
        self.order_label.set_bold(True)
        self.orders.set_columns(self._get_columns())
        self.searchbar = SearchBar(self.conn, PurchaseOrder, 
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
        order = self.orders.get_selected()
        if not order:
            raise ValueError('You should have one order selected '
                             'at this point, got nothing')
        run_dialog(PurchaseDetailsDialog, self, self.conn, model=order)


#
# Main wizard
#

class ReceivingOrderWizard(BaseWizard):
    title = _("Receiving Order")
    size = (750, 500)
    
    def __init__(self, conn):
        model = self._create_model(conn)
        first_step = PurchaseSelectionStep(self, conn, model)
        BaseWizard.__init__(self, conn, first_step, model)

    def _create_model(self, conn):
        current_user = get_current_user()
        current_user = Person.iget(IUser, current_user.id, connection=conn)
        branch = sysparam(conn).CURRENT_BRANCH
        return ReceivingOrder(responsible=current_user, supplier=None,
                              branch=branch, connection=conn)

    #
    # WizardStep hooks
    #

    def finish(self):
        if not self.model.get_valid():
            self.model.set_valid()
        self.retval = self.model
        self.model.confirm()
        self.close()
