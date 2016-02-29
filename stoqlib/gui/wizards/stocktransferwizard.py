# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2009 Async Open Source <http://www.async.com.br>
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
""" Stock transfer wizard definition """

from decimal import Decimal

import gtk
from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.ui.objectlist import Column
from storm.expr import And

from stoqlib.api import api
from stoqlib.domain.fiscal import Invoice
from stoqlib.domain.person import Branch, Employee
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.transfer import TransferOrder, TransferOrderItem
from stoqlib.domain.views import ProductWithStockBranchView
from stoqlib.gui.base.columns import AccessorColumn
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.wizards import (BaseWizard, WizardEditorStep)
from stoqlib.gui.dialogs.batchselectiondialog import BatchDecreaseSelectionDialog
from stoqlib.gui.dialogs.missingitemsdialog import (get_missing_items,
                                                    MissingItemsDialog)
from stoqlib.gui.editors.transfereditor import TransferItemEditor
from stoqlib.gui.events import StockTransferWizardFinishEvent
from stoqlib.gui.utils.printing import print_report
from stoqlib.gui.wizards.abstractwizard import SellableItemStep
from stoqlib.lib.formatters import format_sellable_description
from stoqlib.lib.message import warning, yesno
from stoqlib.lib.pluginmanager import get_plugin_manager
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.transfer import TransferOrderReceipt

_ = stoqlib_gettext


#
# Wizard steps
#

class StockTransferInitialStep(WizardEditorStep):
    gladefile = 'StockTransferInitialStep'
    model_type = TransferOrder
    proxy_widgets = ['open_date',
                     'destination_branch',
                     'source_responsible',
                     'invoice_number',
                     'comments']

    def __init__(self, wizard, store, model):
        self.branch = api.get_current_branch(store)
        manager = get_plugin_manager()
        self._nfe_is_active = manager.is_active('nfe')
        WizardEditorStep.__init__(self, store, wizard, model)

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.wizard.model, self.proxy_widgets)
        # Force the user to select a branch, avoiding transfering to the wrong
        # branch by mistake
        self.destination_branch.update(None)

    def _setup_widgets(self):
        branches = Branch.get_active_remote_branches(self.store)
        self.destination_branch.prefill(api.for_person_combo(branches))
        self.source_branch.set_text(self.branch.get_description())

        employees = self.store.find(Employee)
        self.source_responsible.prefill(api.for_person_combo(employees))

        self.invoice_number.set_property('mandatory', self._nfe_is_active)

        # Set an initial invoice number to TransferOrder and Invoice
        if not self.model.invoice_number:
            new_invoice_number = Invoice.get_next_invoice_number(self.store)
            self.model.invoice_number = new_invoice_number

    def _validate_destination_branch(self):
        if not self._nfe_is_active:
            return True
        other_branch = self.destination_branch.read()

        if not self.branch.is_from_same_company(other_branch):
            warning(_(u"Branches are not from the same CNPJ"))
            return False

        return True

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def has_next_step(self):
        return True

    def next_step(self):
        return StockTransferItemStep(self.wizard, self, self.store,
                                     self.wizard.model)

    def validate_step(self):
        return self._validate_destination_branch()

    def on_invoice_number__validate(self, widget, value):
        if not 0 < value <= 999999999:
            return ValidationError(
                _("Invoice number must be between 1 and 999999999"))

        invoice = self.model.invoice
        branch = self.model.branch
        if invoice.check_unique_invoice_number_by_branch(value, branch):
            return ValidationError(_(u'Invoice number already used.'))


class StockTransferItemStep(SellableItemStep):
    model_type = TransferOrder
    item_table = TransferOrderItem
    sellable_view = ProductWithStockBranchView
    batch_selection_dialog = BatchDecreaseSelectionDialog
    validate_stock = True
    cost_editable = False
    item_editor = TransferItemEditor

    def __init__(self, wizard, previous, store, model):
        manager = get_plugin_manager()
        nfe_is_active = manager.is_active('nfe')
        if nfe_is_active:
            self.cost_editable = True
        SellableItemStep.__init__(self, wizard, previous, store, model)

    #
    # SellableItemStep hooks
    #

    def get_sellable_view_query(self):
        sellable_query = And(
            Sellable.get_unblocked_sellables_query(self.store, storable=False),
            self.sellable_view.branch_id == self.model.source_branch_id)
        return self.sellable_view, sellable_query

    def get_saved_items(self):
        return list(self.model.get_items())

    def get_order_item(self, sellable, cost, quantity, batch=None, parent=None):
        return self.model.add_sellable(sellable, batch, quantity, cost)

    def get_columns(self):
        return [
            Column('sellable.code', title=_(u'Code'), data_type=str,
                   searchable=True,),
            Column('sellable.description', title=_(u'Description'),
                   data_type=str, expand=True, searchable=True,
                   format_func=self._format_description, format_func_data=True),
            AccessorColumn('stock', title=_(u'Stock'), data_type=Decimal,
                           accessor=self._get_stock_quantity, width=80),
            Column('quantity', title=_(u'Transfer'), data_type=Decimal,
                   width=100),
            AccessorColumn('total', title=_(u'Total'), data_type=Decimal,
                           accessor=self._get_total_quantity, width=80),
            Column('stock_cost', title=_(u'Cost'), data_type=currency),
        ]

    def _format_description(self, item, data):
        return format_sellable_description(item.sellable, item.batch)

    def _get_stock_quantity(self, item):
        if not item.sellable.product.manage_stock:
            return
        storable = item.sellable.product_storable
        stock_item = storable.get_stock_item(self.model.branch, item.batch)
        return stock_item.quantity or 0

    def _get_total_quantity(self, item):
        if not item.sellable.product.manage_stock:
            return
        qty = self._get_stock_quantity(item)
        qty -= item.quantity
        if qty > 0:
            return qty
        return 0

    def _setup_summary(self):
        self.summary = None

    def sellable_selected(self, sellable, batch=None):
        SellableItemStep.sellable_selected(self, sellable, batch=batch)

        if sellable is None or not sellable.product.manage_stock:
            return

        storable = sellable.product_storable
        # FIXME: We should not have to override this method. This should
        # be done automatically on SellableItemStep
        self.stock_quantity.set_label(
            "%s" % storable.get_balance_for_branch(branch=self.model.branch))

    def setup_slaves(self):
        SellableItemStep.setup_slaves(self)

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.hide_add_button()

        SellableItemStep.post_init(self)

    def has_next_step(self):
        return False


#
# Main wizard
#


class StockTransferWizard(BaseWizard):
    title = _(u'Stock Transfer')
    size = (750, 350)

    def __init__(self, store):
        self.model = self._create_model(store)
        first_step = StockTransferInitialStep(self, store, self.model)
        BaseWizard.__init__(self, store, first_step, self.model)

    def _create_model(self, store):
        user = api.get_current_user(store)
        source_responsible = store.find(Employee, person=user.person).one()
        return TransferOrder(
            source_branch=api.get_current_branch(store),
            source_responsible=source_responsible,
            destination_branch=Branch.get_active_remote_branches(store)[0],
            store=store)

    def _receipt_dialog(self, order):
        msg = _('Would you like to print a receipt for this transfer?')
        if yesno(msg, gtk.RESPONSE_YES, _("Print receipt"), _("Don't print")):
            print_report(TransferOrderReceipt, order)

    def finish(self):
        missing = get_missing_items(self.model, self.store)
        if missing:
            run_dialog(MissingItemsDialog, self, self.model, missing)
            return False

        self.model.send()

        self.retval = self.model
        self.close()

        StockTransferWizardFinishEvent.emit(self.model)
        # Commit before printing to avoid losing data if something breaks
        self.store.confirm(self.retval)
        self._receipt_dialog(self.model)
