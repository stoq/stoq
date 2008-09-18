# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
##              Fabio Morbec                <fabio@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
##
""" Receiving wizard definition """

import datetime
from decimal import Decimal

import gtk
from kiwi.datatypes import currency
from kiwi.db.sqlobj import SQLObjectQueryExecuter
from kiwi.ui.search import SearchSlaveDelegate, DateSearchFilter
from kiwi.ui.widgets.list import Column

from stoqlib.database.runtime import get_current_user
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.slaves.receivingslave import ReceivingInvoiceSlave
from stoqlib.gui.search.productsearch import ProductSearch
from stoqlib.gui.wizards.abstractwizard import SellableItemStep
from stoqlib.gui.dialogs.purchasedetails import PurchaseDetailsDialog
from stoqlib.gui.editors.sellableeditor import SellableItemEditor
from stoqlib.lib.validators import format_quantity
from stoqlib.domain.purchase import PurchaseOrder, PurchaseOrderView, PurchaseItem
from stoqlib.domain.receiving import (ReceivingOrder, ReceivingOrderItem,
                                      get_receiving_items_by_purchase_order)
from stoqlib.domain.sellable import ASellable

_ = stoqlib_gettext


# Workaround, so PurchaseSelectionStep does not complain about empty model
class _FakeReceivingOrder(object):
    pass

#
# Wizard Steps
#


class PurchaseSelectionStep(WizardEditorStep):
    gladefile = 'PurchaseSelectionStep'
    model_type = _FakeReceivingOrder

    def __init__(self, wizard, conn, model):
        self._next_step = None
        WizardEditorStep.__init__(self, conn, wizard, model)

    def _refresh_next(self, validation_value):
        has_selection = self.search.results.get_selected() is not None
        self.wizard.refresh_next(has_selection)

    def _create_search(self):
        self.search = SearchSlaveDelegate(self._get_columns())
        self.attach_slave('searchbar_holder', self.search)
        self.executer = SQLObjectQueryExecuter()
        self.search.set_query_executer(self.executer)
        self.executer.set_table(PurchaseOrderView)
        self.executer.add_query_callback(self._get_extra_query)
        self._create_filters()
        self.search.results.connect('selection-changed',
                                    self._on_results__selection_changed)
        self.search.results.connect('row-activated',
                                    self._on_results__row_activated)
        self.search.focus_search_entry()

    def _create_filters(self):
        self.search.set_text_field_columns(['supplier_name'])
        date_filter = DateSearchFilter(_('Date:'))
        self.search.add_filter(date_filter, columns=['open_date'])

    def _get_extra_query(self, states):
        return PurchaseOrderView.q.status == PurchaseOrder.ORDER_CONFIRMED

    def _get_columns(self):
        return [Column('id', title=_('Number'), sorted=True,
                       data_type=str, width=80),
                Column('open_date', title=_('Date Started'),
                       data_type=datetime.date, width=100),
                Column('supplier_name', title=_('Supplier'),
                       data_type=str, searchable=True, width=130,
                       expand=True),
                Column('ordered_quantity', title=_('Qty Ordered'),
                       data_type=Decimal, width=110,
                       format_func=format_quantity),
                Column('received_quantity', title=_('Qty Received'),
                       data_type=Decimal, width=145,
                       format_func=format_quantity),
                Column('total', title=_('Order Total'),
                       data_type=currency, width=120)]

    def _update_view(self):
        has_selection = self.search.results.get_selected() is not None
        self.details_button.set_sensitive(has_selection)

    #
    # WizardStep hooks
    #

    def post_init(self):
        self._update_view()
        self.register_validate_function(self._refresh_next)
        self.force_validation()

    def next_step(self):
        selected = self.search.results.get_selected()
        purchase = selected.purchase

        # We cannot create the model in the wizard since we haven't
        # selected a PurchaseOrder yet which ReceivingOrder depends on
        # Create the order here since this is the first place where we
        # actually have a purchase selected
        if not self.wizard.model:
            self.wizard.model = self.model = ReceivingOrder(
                responsible=get_current_user(self.conn),
                supplier=None, invoice_number=None,
                branch=None, purchase=purchase,
                connection=self.conn)

        # Remove all the items added previously, used if we hit back
        # at any point in the wizard.
        if self.model.purchase != purchase:
            self.model.remove_items()
            # This forces ReceivingOrderProductStep to create a new model
            self._next_step = None

        if selected:
            self.model.purchase = purchase
            self.model.branch = purchase.branch
            self.model.supplier = purchase.supplier
            self.model.transporter = purchase.transporter
        else:
            self.model.purchase = None

        # FIXME: Improve the infrastructure to avoid this local caching of
        #        Wizard steps.
        if not self._next_step:
            # Remove all the items added previously, used if we hit back
            # at any point in the wizard.
            self._next_step = ReceivingOrderProductStep(self.wizard,
                                                        self, self.conn,
                                                        self.model)
        return self._next_step

    def has_previous_step(self):
        return False

    def setup_slaves(self):
        self._create_search()

    #
    # Kiwi callbacks
    #

#     def on_searchbar_activate(self, slave, objs):
#         """Use this callback with SearchBar search-activate signal"""
#         self.results.add_list(objs, clear=True)
#         has_selection = self.results.get_selected() is not None
#         self.wizard.refresh_next(has_selection)

    def _on_results__selection_changed(self, results, purchase_order_view):
        self.force_validation()
        self._update_view()

    def _on_results__row_activated(self, results, purchase_order_view):
        run_dialog(PurchaseDetailsDialog, self, self.conn,
                   model=purchase_order_view.purchase)

    def on_details_button__clicked(self, *args):
        selected = self.search.results.get_selected()
        if not selected:
            raise ValueError('You should have one order selected '
                             'at this point, got nothing')
        run_dialog(PurchaseDetailsDialog, self, self.conn,
                   model=selected.purchase)


class ReceivingOrderProductStep(SellableItemStep):
    model_type = ReceivingOrder
    item_table = ReceivingOrderItem
    summary_label_text = "<b>%s</b>" % _('Total Received:')

    #
    # SellableItemStep overrides
    #

    def setup_sellable_entry(self):
        purchase = self.model.purchase
        if purchase:
            sellables = [i.sellable for i in purchase.get_pending_items()]
        else:
            sellables = ASellable.get_unblocked_sellables(self.conn)
        self.sellable.prefill([(sellable.get_description(), sellable)
                                 for sellable in sellables])

    #
    # WizardStep hooks
    #

    def post_init(self):
        # Hide the search bar, since it does not make sense to add new
        # items to a receivable order.
        self.item_hbox.hide()
        self.slave.hide_add_button()
        self.slave.set_editor(SellableItemEditor)
        self._refresh_next()

    def next_step(self):
        return ReceivingInvoiceStep(self.conn, self.wizard, self.model, self)

    def get_columns(self):
        return [
            Column('sellable.description', title=_('Description'),
                   data_type=str, expand=True, searchable=True),
            Column('remaining_quantity', title=_('Quantity'), data_type=int,
                   width=90, format_func=format_quantity, expand=True),
            Column('quantity', title=_('Quantity to receive'), data_type=int,
                   width=110, format_func=format_quantity),
            Column('sellable.unit_description', title=_('Unit'), data_type=str,
                   width=50),
            Column('cost', title=_('Cost'), data_type=currency, width=90),
            Column('total', title=_('Total'), data_type=currency, width=100)
            ]


    def get_order_item(self, sellable, cost, total_quantity):
        purchase_item = PurchaseItem.selectBy(
            sellable=sellable,
            order=self.model.purchase,
            connection=self.conn)
        quantity = total_quantity - purchase_item.quantity_received
        return ReceivingOrderItem(connection=self.conn, sellable=sellable,
                                  receiving_order=self.model,
                                  purchase_item=purchase_item,
                                  cost=cost, quantity=quantity)

    def get_saved_items(self):
        if not self.model.purchase:
            return []
        return get_receiving_items_by_purchase_order(self.model.purchase,
                                                     self.model)

    #
    # callbacks
    #

    def on_product_button__clicked(self, *args):
        # We are going to call a SearchEditor subclass which means
        # database synchronization... Outch, time to commit !
        self.conn.commit()
        item_statuses = [ASellable.STATUS_AVAILABLE,
                         ASellable.STATUS_SOLD]
        items = run_dialog(ProductSearch, self, self.conn,
                           hide_footer=False, hide_toolbar=True,
                           hide_price_column=True,
                           selection_mode=gtk.SELECTION_MULTIPLE,
                           use_product_statuses=item_statuses)
        for item in items:
            self._update_list(item)


class ReceivingInvoiceStep(WizardEditorStep):
    gladefile = 'HolderTemplate'
    model_type = ReceivingOrder

    #
    # WizardStep hooks
    #

    def has_next_step(self):
        return False

    def post_init(self):
        self.invoice_slave = ReceivingInvoiceSlave(self.conn, self.model)
        self.attach_slave("place_holder", self.invoice_slave)
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()


#
# Main wizard
#

class ReceivingOrderWizard(BaseWizard):
    title = _("Receiving Order")
    size = (750, 350)

    def __init__(self, conn):
        self.model = None
        first_step = PurchaseSelectionStep(self, conn,
                                           _FakeReceivingOrder())
        BaseWizard.__init__(self, conn, first_step, self.model)
        self.next_button.set_sensitive(False)

    #
    # WizardStep hooks
    #

    def finish(self):
        assert self.model
        assert self.model.branch

        if not self.model.get_valid():
            self.model.set_valid()
        self.retval = self.model
        self.model.confirm()
        self.close()
