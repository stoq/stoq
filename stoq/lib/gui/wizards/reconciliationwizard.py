# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

#
# Copyright (C) 2018 Async Open Source <http://www.async.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
# Author(s): Stoq Team <stoq-devel@async.com.br>
#
#
""" Receiving wizard definition """

import datetime

from gi.repository import Gtk
from kiwi.currency import currency
from kiwi.ui.objectlist import Column
from storm.expr import And, Eq

from stoqlib.api import api
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.receiving import ReceivingInvoice
from stoqlib.domain.views import PurchaseReceivingView
from stoq.lib.gui.base.wizards import BaseWizard, BaseWizardStep, WizardEditorStep
from stoq.lib.gui.base.dialogs import run_dialog
from stoq.lib.gui.dialogs.receivingdialog import ReceivingOrderDetailsDialog
from stoq.lib.gui.search.searchcolumns import IdentifierColumn, SearchColumn
from stoq.lib.gui.search.searchslave import SearchSlave
from stoq.lib.gui.slaves.receivingslave import ReceivingInvoiceSlave
from stoq.lib.gui.wizards.abstractwizard import BasePaymentStep
from stoqlib.lib.formatters import format_quantity, get_formatted_cost
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ReceivingSelectionStep(BaseWizardStep):
    gladefile = 'PurchaseSelectionStep'

    def __init__(self, wizard, store):
        self._next_step = None
        BaseWizardStep.__init__(self, store, wizard)
        self.setup_slaves()

    def _create_search(self):
        self.search = SearchSlave(self._get_columns(),
                                  restore_name=self.__class__.__name__,
                                  store=self.store,
                                  search_spec=PurchaseReceivingView)
        self.search.enable_advanced_search()
        self.attach_slave('searchbar_holder', self.search)
        executer = self.search.get_query_executer()
        executer.add_query_callback(self.get_extra_query)
        self._create_filters()
        self.search.result_view.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        self.search.result_view.connect('selection-changed',
                                        self._on_results__selection_changed)
        self.search.result_view.connect('row-activated',
                                        self._on_results__row_activated)
        self.search.focus_search_entry()

    def _create_filters(self):
        self.search.set_text_field_columns(['supplier_name', 'purchase_identifier'])

    def get_extra_query(self, states):
        query = And(Eq(PurchaseReceivingView.purchase_group, None),
                    Eq(PurchaseReceivingView.receiving_invoice, None))

        # Dont let the user receive purchases from other branches when working
        # in synchronized mode
        if (api.sysparam.get_bool('SYNCHRONIZED_MODE') and not
                api.can_see_all_branches()):
            branch = api.get_current_branch(self.store)
            query = And(query, PurchaseReceivingView.branch_id == branch.id)
        return query

    def _get_columns(self):
        return [IdentifierColumn('identifier', _('Receiving #'), width=140),
                IdentifierColumn('purchase_identifier', _('Purchase #'), width=110),
                SearchColumn('packing_number', title=_('Packing Number'),
                             data_type=str, visible=False),
                SearchColumn('receival_date', _('Receival date'), expand=True,
                             data_type=datetime.date, sorted=True, width=110),
                SearchColumn('supplier_name', _('Supplier'), data_type=str,
                             expand=True),
                SearchColumn('responsible_name', _('Responsible'),
                             data_type=str, visible=False, expand=True),
                SearchColumn('purchase_responsible_name', _('Purchaser'),
                             data_type=str, visible=False, expand=True),
                SearchColumn('invoice_number', _('Invoice #'), data_type=int,
                             width=80),
                Column('subtotal', title=_('Products total'),
                       data_type=currency, width=150)]

    def _update_view(self):
        selected_rows = self.search.result_view.get_selected_rows()
        can_continue = len(set((v.supplier_id, v.branch_id) for v in selected_rows)) == 1
        self.wizard.refresh_next(can_continue)
        self.details_button.set_sensitive(len(selected_rows) == 1)

    #
    # WizardStep hooks
    #

    def post_init(self):
        self._update_view()
        self.force_validation()

    def next_step(self):
        self.search.save_columns()
        selected_rows = self.search.result_view.get_selected_rows()

        return ProductsCostCheckStep(self.wizard, self, self.store, selected_rows)

    def has_previous_step(self):
        return False

    def setup_slaves(self):
        self._create_search()

    #
    # Kiwi callbacks
    #

    def _on_results__selection_changed(self, results, purchase_order_view):
        self.force_validation()
        self._update_view()

    def _on_results__row_activated(self, results, receiving_order_view):
        run_dialog(ReceivingOrderDetailsDialog, self.wizard, self.store,
                   model=receiving_order_view.order)

    def on_details_button__clicked(self, *args):
        selected = self.search.results.get_selected_rows()[0]
        if not selected:
            raise ValueError('You should have one order selected '
                             'at this point, got nothing')
        run_dialog(ReceivingOrderDetailsDialog, self.wizard, self.store,
                   model=selected.order)


class ProductsCostCheckStep(BaseWizardStep):
    gladefile = 'ReceivingOrderItemStep'

    def __init__(self, wizard, previous_step, store, receivings):
        self.receivings = receivings
        self.receiving_items = self._get_received_items(with_children=True)
        BaseWizardStep.__init__(self, store, wizard, previous_step)

    #
    #  WizardEditorStep
    #

    def post_init(self):
        self.edit_btn.set_visible(False)

        self._setup_widgets()
        self._update_view()

    def next_step(self):
        self._create_receiving_invoice()
        return InvoiceDetailsStep(self.store, self.wizard, self.model, self)

    #
    #  Private
    #

    def _update_view(self):
        self.total_received.update(self._get_total_received())
        self.force_validation()

    def _setup_widgets(self):
        self.purchase_items.set_columns([
            # TRANSLATORS: Packing Number = Número do Romaneio
            Column('receiving_packing_number', title=_('Packing Number'), data_type=str),
            Column('code', title=_('Code'),
                   data_type=str, searchable=True, visible=False),
            Column('barcode', title=_('Barcode'),
                   data_type=str, searchable=True, visible=False),
            Column('description', title=_('Description'),
                   data_type=str, expand=True, searchable=True, sorted=True),
            Column('quantity', title=_('Qty to receive'), data_type=int,
                   format_func=format_quantity),
            Column('purchase_cost', title=_('Purchase Cost'), data_type=currency,
                   format_func=get_formatted_cost, width=120),
            Column('cost', title=_('Cost'), data_type=currency, editable=True,
                   format_func=get_formatted_cost, width=120),
            Column('received_total', title=_('Total'), data_type=currency, width=100)])
        # We must clear the ObjectTree before
        self.purchase_items.clear()
        for item in self._get_received_items():
            self.purchase_items.append(None, item)
            for child in item.children_items:
                self.purchase_items.append(item, child)

        self.purchase_items.set_cell_data_func(
            self._on_purchase_items__cell_data_func)

        self.purchase_items.connect('cell-edited', self._on_purchase_items__cell_edited)

    def _get_received_items(self, with_children=False):
        items = []
        for receiving_view in self.receivings:
            for item in receiving_view.order.get_items(with_children=with_children):
                items.append(item)
        return items

    def _get_total_received(self):
        return sum([item.get_received_total() for item in self.receiving_items])

    def _create_receiving_invoice(self):
        # We only let the user get this far if the receivings selected are for the
        # same branch and supplier
        supplier = self.receivings[0].purchase.supplier
        branch = self.receivings[0].branch

        # If the receiving is for another branch, we need a temporary identifier
        temporary_identifier = None
        if (api.sysparam.get_bool('SYNCHRONIZED_MODE') and
                api.get_current_branch(self.store) != branch):
            temporary_identifier = ReceivingInvoice.get_temporary_identifier(self.store)

        group = PaymentGroup(store=self.store, recipient=supplier.person)
        self.wizard.model = self.model = ReceivingInvoice(
            identifier=temporary_identifier, supplier=supplier, group=group,
            branch=branch, store=self.store, station=api.get_current_station(self.store),
            responsible=api.get_current_user(self.store))

        for row in self.receivings:
            self.model.add_receiving(row.order)

    #
    #  Callbacks
    #

    def _on_purchase_items__cell_data_func(self, column, renderer, obj, text):
        editable = not obj.sellable.product.is_package
        renderer.set_property('sensitive', editable)
        if column.attribute == 'cost':
            renderer.set_property('editable-set', editable)
            renderer.set_property('editable', editable)
        return text

    def _on_purchase_items__cell_edited(self, klist, obj, column):
        if column.attribute == 'cost':
            self.purchase_items.update(obj)
            self._update_view()


class InvoiceDetailsStep(WizardEditorStep):
    gladefile = 'HolderTemplate'
    model_type = ReceivingInvoice

    #
    # WizardStep hooks
    #

    def next_step(self):
        if self.model.freight_total and self.invoice_slave.create_freight_payment():
            group = self.model.group if not self.model.transporter else None
            self.model.create_freight_payment(group=group)
        self.store.savepoint('before_invoicepayment_step')
        return InvoicePaymentStep(self.wizard, self, self.store, self.model)

    def post_init(self):
        # If the user is comming back from the next, make sure things don't get
        # messed
        if self.store.savepoint_exists('before_invoicepayment_step'):
            self.store.rollback_to_savepoint('before_invoicepayment_step')

        self._is_valid = False
        self.invoice_slave = ReceivingInvoiceSlave(self.store, self.model)
        self.invoice_slave.connect('activate', self._on_invoice_slave__activate)
        self.attach_slave("place_holder", self.invoice_slave)
        # Slaves must be focused after being attached
        self.invoice_slave.invoice_number.grab_focus()
        self.register_validate_function(self._validate_func)
        self.force_validation()

    # Callbacks

    def _validate_func(self, is_valid):
        self._is_valid = is_valid
        self.wizard.refresh_next(is_valid)

    def _on_invoice_slave__activate(self, slave):
        if self._is_valid:
            self.wizard.finish()


class InvoicePaymentStep(BasePaymentStep):

    #
    # BasePaymentStep hooks
    #

    def has_next_step(self):
        return False


class PurchaseReconciliationWizard(BaseWizard):
    title = _("Purchase Reconciliation")
    size = (850, 430)
    need_cancel_confirmation = True

    def __init__(self, store):
        self.model = None
        self.sync_mode = api.sysparam.get_bool('SYNCHRONIZED_MODE')
        self.current_branch = api.get_current_branch(store)
        first_step = ReceivingSelectionStep(self, store)
        BaseWizard.__init__(self, store, first_step, self.model)
        self.next_button.set_sensitive(False)

    def is_for_another_branch(self):
        # If sync mode is on and the purchase order is for another branch, we
        # must restrict a few options like creating payments and receiving all
        # items now.
        if not self.sync_mode:
            return False
        if self.model.branch == self.current_branch:
            return False

        return True

    #
    # WizardStep hooks
    #

    def finish(self):
        assert self.model
        assert self.model.branch

        self.model.confirm(api.get_current_user(self.store))
        self.retval = self.model
        self.store.confirm(self.retval)
        self.close()
