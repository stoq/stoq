# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2009 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Receiving wizard definition """

import datetime
from decimal import Decimal

import gtk
from kiwi.currency import currency
from kiwi.ui.objectlist import Column
from storm.expr import And

from stoqlib.api import api
from stoqlib.domain.purchase import PurchaseOrder, PurchaseOrderView
from stoqlib.domain.receiving import ReceivingOrder
from stoqlib.gui.base.wizards import (WizardEditorStep, BaseWizard,
                                      BaseWizardStep)
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.slaves.receivingslave import ReceivingInvoiceSlave
from stoqlib.gui.dialogs.batchselectiondialog import BatchIncreaseSelectionDialog
from stoqlib.gui.dialogs.purchasedetails import PurchaseDetailsDialog
from stoqlib.gui.dialogs.labeldialog import SkipLabelsEditor
from stoqlib.gui.events import ReceivingOrderWizardFinishEvent
from stoqlib.gui.search.searchcolumns import IdentifierColumn, SearchColumn
from stoqlib.gui.search.searchslave import SearchSlave
from stoqlib.gui.utils.printing import print_labels
from stoqlib.lib.defaults import MAX_INT
from stoqlib.lib.formatters import format_quantity, get_formatted_cost
from stoqlib.lib.message import yesno, warning
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _TemporaryReceivingItem(object):
    def __init__(self, item):
        self.purchase_item = item
        self.description = item.sellable.description
        self.category_description = item.sellable.get_category_description()
        self.unit_description = item.sellable.get_unit_description()
        self.cost = item.cost
        self.remaining_quantity = item.get_pending_quantity()
        self.storable = item.sellable.product_storable
        self.is_batch = self.storable and self.storable.is_batch
        self.need_adjust_batch = self.is_batch
        self.batches = []
        if not self.is_batch:
            self.quantity = self.remaining_quantity

    @property
    def total(self):
        return currency(self.cost * self.quantity)

    def _get_quantity(self):
        if self.is_batch:
            return sum(item.quantity for item in self.batches)
        return self._quantity

    def _set_quantity(self, quantity):
        assert not self.is_batch
        self._quantity = quantity

    quantity = property(_get_quantity, _set_quantity)

#
# Wizard Steps
#


class PurchaseSelectionStep(BaseWizardStep):
    gladefile = 'PurchaseSelectionStep'

    def __init__(self, wizard, store):
        self._next_step = None
        BaseWizardStep.__init__(self, store, wizard)
        self.setup_slaves()

    def _refresh_next(self, validation_value):
        has_selection = self.search.results.get_selected() is not None
        self.wizard.refresh_next(has_selection)

    def _create_search(self):
        self.search = SearchSlave(self._get_columns(),
                                  restore_name=self.__class__.__name__,
                                  store=self.store,
                                  search_spec=PurchaseOrderView)
        self.search.enable_advanced_search()
        self.attach_slave('searchbar_holder', self.search)
        executer = self.search.get_query_executer()
        executer.add_query_callback(self.get_extra_query)
        self._create_filters()
        self.search.results.connect('selection-changed',
                                    self._on_results__selection_changed)
        self.search.results.connect('row-activated',
                                    self._on_results__row_activated)
        self.search.focus_search_entry()

    def _create_filters(self):
        self.search.set_text_field_columns(['supplier_name', 'identifier_str'])

    def get_extra_query(self, states):
        query = PurchaseOrderView.status == PurchaseOrder.ORDER_CONFIRMED

        # Dont let the user receive purchases from other branches when working
        # in synchronized mode
        if api.sysparam().get_bool('SYNCHRONIZED_MODE'):
            branch = api.get_current_branch(self.store)
            query = And(query,
                        PurchaseOrderView.branch_id == branch.id)
        return query

    def _get_columns(self):
        return [IdentifierColumn('identifier', sorted=True),
                SearchColumn('open_date', title=_('Date Started'),
                             data_type=datetime.date, width=100),
                SearchColumn('expected_receival_date', data_type=datetime.date,
                             title=_('Expected Receival'), visible=False),
                SearchColumn('supplier_name', title=_('Supplier'),
                             data_type=str, searchable=True, width=130,
                             expand=True),
                SearchColumn('ordered_quantity', title=_('Qty Ordered'),
                             data_type=Decimal, width=110,
                             format_func=format_quantity),
                SearchColumn('received_quantity', title=_('Qty Received'),
                             data_type=Decimal, width=145,
                             format_func=format_quantity),
                SearchColumn('total', title=_('Order Total'),
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
        self.search.save_columns()
        selected = self.search.results.get_selected()
        purchase = selected.purchase

        # We cannot create the model in the wizard since we haven't
        # selected a PurchaseOrder yet which ReceivingOrder depends on
        # Create the order here since this is the first place where we
        # actually have a purchase selected
        if not self.wizard.model:
            self.wizard.model = self.model = ReceivingOrder(
                responsible=api.get_current_user(self.store),
                supplier=purchase.supplier, invoice_number=None,
                branch=purchase.branch, purchase=purchase,
                store=self.store)

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
            self._next_step = ReceivingOrderItemStep(self.store, self.wizard,
                                                     self.model, self)
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
        run_dialog(PurchaseDetailsDialog, self.wizard, self.store,
                   model=purchase_order_view.purchase)

    def on_details_button__clicked(self, *args):
        selected = self.search.results.get_selected()
        if not selected:
            raise ValueError('You should have one order selected '
                             'at this point, got nothing')
        run_dialog(PurchaseDetailsDialog, self.wizard, self.store,
                   model=selected.purchase)


class ReceivingOrderItemStep(WizardEditorStep):
    gladefile = 'ReceivingOrderItemStep'
    model_type = ReceivingOrder

    #
    #  WizardEditorStep
    #

    def post_init(self):
        # If the user goes back from the previous step, make sure
        # things don't get messed
        if self.store.savepoint_exists('before_receivinginvoice_step'):
            self.store.rollback_to_savepoint('before_receivinginvoice_step')

        self.edit_btn.set_sensitive(bool(self.purchase_items.get_selected()))

        self.register_validate_function(self._validation_func)
        self.force_validation()

    def setup_proxies(self):
        self._setup_widgets()
        self._update_view()

    def next_step(self):
        self.store.savepoint('before_receivinginvoice_step')
        self._create_receiving_items()
        return ReceivingInvoiceStep(self.store, self.wizard, self.model, self)

    def validate_step(self):
        if any(i.need_adjust_batch for i in self.purchase_items):
            warning(_("Before proceeding you need to adjust quantities for "
                      "the batch products (highlighted in red)"))
            return False

        return True

    #
    #  Private
    #

    def _update_view(self):
        self.total_received.update(self._get_total_received())
        self.force_validation()

    def _setup_widgets(self):
        adjustment = gtk.Adjustment(lower=0, upper=MAX_INT, step_incr=1)
        self.purchase_items.set_columns([
            Column('description', title=_('Description'),
                   data_type=str, expand=True, searchable=True),
            Column('category_description', title=_('Category'),
                   data_type=str, width=120),
            Column('remaining_quantity', title=_('Qty'), data_type=int,
                   format_func=format_quantity, expand=True),
            Column('quantity', title=_('Qty to receive'), data_type=int,
                   editable=True, spin_adjustment=adjustment,
                   format_func=format_quantity),
            Column('unit_description', title=_('Unit'), data_type=str,
                   width=50),
            Column('cost', title=_('Cost'), data_type=currency,
                   format_func=get_formatted_cost, width=90),
            Column('total', title=_('Total'), data_type=currency, width=100)])
        self.purchase_items.extend(self._get_pending_items())

        self.purchase_items.set_cell_data_func(
            self._on_purchase_items__cell_data_func)

    def _get_pending_items(self):
        for item in self.model.purchase.get_pending_items():
            yield _TemporaryReceivingItem(item)

    def _get_total_received(self):
        return sum([item.total for item in self.purchase_items])

    def _create_receiving_items(self):
        for item in self.purchase_items:
            if item.is_batch:
                for batch_item in item.batches:
                    self.model.add_purchase_item(
                        item.purchase_item,
                        quantity=batch_item.quantity,
                        batch_number=batch_item.batch)
            elif item.quantity > 0:
                self.model.add_purchase_item(item.purchase_item,
                                             item.quantity)

    def _edit_item(self, item):
        if item.is_batch:
            retval = run_dialog(BatchIncreaseSelectionDialog, self.wizard,
                                store=self.store, model=item.storable,
                                quantity=item.remaining_quantity,
                                original_batches=item.batches)
            item.batches = retval or item.batches
            # Once we edited the batch item once, it's not obrigatory
            # to edit it again.
            item.need_adjust_batch = False
            self.purchase_items.update(item)
        else:
            self._edit_item_quantity_cell(item)

        self._update_view()

    def _edit_item_quantity_cell(self, item):
        for column in self.purchase_items.get_columns():
            if column.attribute != 'quantity':
                continue

            tc = column.treeview_column
            cr = tc.get_cell_renderers()[0]
            event = gtk.gdk.Event(gtk.gdk.BUTTON_PRESS)
            treeview = tc.get_tree_view()
            path, tv_column = treeview.get_cursor()
            cr.set_property('editable-set', True)
            cr.set_property('editable', True)
            # FIXME: Why is this now working? Maybe we should remove the
            # edit button and let the user just double-click, but we should
            # make it easier for the user to see that he can edit the cell
            ce = cr.start_editing(event, treeview, str(path[0]),
                                  treeview.get_background_area(path, tc),
                                  treeview.get_cell_area(path, tc),
                                  gtk.CELL_RENDERER_FOCUSED)
            ce.start_editing(event)
            break

    def _validation_func(self, value):
        has_receivings = self._get_total_received() > 0
        self.wizard.refresh_next(value and has_receivings)

    #
    #  Callbacks
    #

    def _on_purchase_items__cell_data_func(self, column, renderer, obj, text):
        if not isinstance(renderer, gtk.CellRendererText):
            return text

        if column.attribute == 'quantity':
            renderer.set_property('editable-set', not obj.is_batch)
            renderer.set_property('editable', not obj.is_batch)

        renderer.set_property('foreground', 'red')
        renderer.set_property('foreground-set', obj.need_adjust_batch)

        return text

    def on_purchase_items__cell_edited(self, purchase_items, obj, attr):
        self._update_view()

    def on_purchase_items__cell_editing_started(self, purchase_items, obj,
                                                attr, renderer, editable):
        if attr == 'quantity':
            adjustment = editable.get_adjustment()
            # Don't let the user return more than was bought
            adjustment.set_upper(obj.remaining_quantity)

    def on_purchase_items__selection_changed(self, purchase_items, item):
        self.edit_btn.set_sensitive(bool(item))

    def on_purchase_items__row_activated(self, purchase_items, item):
        self._edit_item(item)

    def on_edit_btn__clicked(self, button):
        item = self.purchase_items.get_selected()
        self._edit_item(item)


class ReceivingInvoiceStep(WizardEditorStep):
    gladefile = 'HolderTemplate'
    model_type = ReceivingOrder

    #
    # WizardStep hooks
    #

    def has_next_step(self):
        return False

    def post_init(self):
        self._is_valid = False
        self.invoice_slave = ReceivingInvoiceSlave(self.store, self.model)
        self.invoice_slave.connect('activate', self._on_invoice_slave__activate)
        self.attach_slave("place_holder", self.invoice_slave)
        # Slaves must be focused after being attached
        self.invoice_slave.invoice_number.grab_focus()
        self.register_validate_function(self._validate_func)
        self.force_validation()
        if not self.has_next_step():
            self.wizard.enable_finish()

    def validate_step(self):
        create_freight_payment = self.invoice_slave.create_freight_payment()
        self.model.update_payments(create_freight_payment)
        return self.model

    # Callbacks

    def _validate_func(self, is_valid):
        self._is_valid = is_valid
        self.wizard.refresh_next(is_valid)

    def _on_invoice_slave__activate(self, slave):
        if self._is_valid:
            self.wizard.finish()

#
# Main wizard
#


class ReceivingOrderWizard(BaseWizard):
    title = _("Receive Purchase Order")
    size = (750, 350)
    # help_section = 'purchase-new-receival'

    def __init__(self, store):
        self.model = None
        first_step = PurchaseSelectionStep(self, store)
        BaseWizard.__init__(self, store, first_step, self.model)
        self.next_button.set_sensitive(False)

    def _maybe_print_labels(self):
        param = api.sysparam().get_string('LABEL_TEMPLATE_PATH')
        if not param:
            return
        if not yesno(_(u'Do you want to print the labels for the received products?'),
                     gtk.RESPONSE_YES, _(u'Print labels'), _(u"Don't print")):
            return
        label_data = run_dialog(SkipLabelsEditor, self, self.store)
        if label_data:
            print_labels(label_data, self.store, self.model.purchase)

    #
    # WizardStep hooks
    #

    def finish(self):
        assert self.model
        assert self.model.branch

        # Remove the items that will not be received now.
        for item in self.model.get_items():
            if item.quantity > 0:
                continue
            self.store.remove(item)

        self._maybe_print_labels()

        ReceivingOrderWizardFinishEvent.emit(self.model)

        self.retval = self.model
        self.model.confirm()
        self.close()
