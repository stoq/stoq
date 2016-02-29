# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2009 Async Open Source <http://www.async.com.br>
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
""" Stock Decrease wizard definition """

from decimal import Decimal

import gtk
from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.ui.objectlist import Column
from storm.expr import And, Eq

from stoqlib.api import api
from stoqlib.domain.costcenter import CostCenter
from stoqlib.domain.fiscal import CfopData, Invoice
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.person import Branch, Employee, Person
from stoqlib.domain.product import Product
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.stockdecrease import StockDecrease, StockDecreaseItem
from stoqlib.domain.views import ProductWithStockBranchView
from stoqlib.lib.formatters import format_quantity, format_sellable_description
from stoqlib.lib.message import yesno
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.pluginmanager import get_plugin_manager
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.dialogs.batchselectiondialog import BatchDecreaseSelectionDialog
from stoqlib.gui.dialogs.missingitemsdialog import (get_missing_items,
                                                    MissingItemsDialog)
from stoqlib.gui.editors.stockdecreaseeditor import StockDecreaseItemEditor
from stoqlib.gui.events import StockDecreaseWizardFinishEvent
from stoqlib.gui.utils.printing import print_report
from stoqlib.gui.wizards.abstractwizard import SellableItemStep
from stoqlib.gui.wizards.salewizard import PaymentMethodStep
from stoqlib.reporting.stockdecrease import StockDecreaseReceipt

_ = stoqlib_gettext


#
# Wizard Steps
#


class StartStockDecreaseStep(WizardEditorStep):
    gladefile = 'StartStockDecreaseStep'
    model_type = StockDecrease
    proxy_widgets = ('confirm_date',
                     'branch',
                     'reason',
                     'removed_by',
                     'cfop',
                     'cost_center',
                     'person',
                     'invoice_number')

    def _fill_employee_combo(self):
        employess = self.store.find(Employee)
        self.removed_by.prefill(api.for_person_combo(employess))

    def _fill_branch_combo(self):
        branches = Branch.get_active_branches(self.store)
        self.branch.prefill(api.for_person_combo(branches))
        sync_mode = api.sysparam.get_bool('SYNCHRONIZED_MODE')
        self.branch.set_sensitive(not sync_mode)

    def _fill_cfop_combo(self):
        cfops = CfopData.get_for_sale(self.store)
        self.cfop.prefill(api.for_combo(cfops))

    def _fill_cost_center_combo(self):
        cost_centers = CostCenter.get_active(self.store)

        # we keep this value because each call to is_empty() is a new sql query
        # to the database
        cost_centers_exists = not cost_centers.is_empty()

        if cost_centers_exists:
            self.cost_center.prefill(api.for_combo(cost_centers, attr='name',
                                                   empty=_('No cost center.')))
        self.cost_center.set_visible(cost_centers_exists)
        self.cost_center_lbl.set_visible(cost_centers_exists)

    def _fill_person_combo(self):
        items = Person.get_items(self.store,
                                 Person.branch != api.get_current_branch(self.store))
        self.person.prefill(items)

    def _setup_widgets(self):
        self.confirm_date.set_sensitive(False)
        self._fill_employee_combo()
        self._fill_branch_combo()
        self._fill_cfop_combo()
        self._fill_cost_center_combo()
        self._fill_person_combo()

        manager = get_plugin_manager()
        nfe_is_active = manager.is_active('nfe')
        self.invoice_number.set_property('mandatory', nfe_is_active)
        self.person.set_property('mandatory', nfe_is_active)

        if not self.model.invoice_number:
            new_invoice_number = Invoice.get_next_invoice_number(self.store)
            self.model.invoice_number = new_invoice_number

        if not sysparam.get_bool('CREATE_PAYMENTS_ON_STOCK_DECREASE'):
            self.create_payments.hide()

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.confirm_date.grab_focus()
        self.table1.set_focus_chain([self.confirm_date, self.branch,
                                     self.removed_by, self.reason, self.cfop,
                                     self.person])
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def next_step(self):
        self.wizard.create_payments = self.create_payments.read()
        return DecreaseItemStep(self.wizard, self, self.store, self.model)

    def has_previous_step(self):
        return False

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    self.proxy_widgets)

    #
    # Callbacks
    #
    def on_invoice_number__validate(self, widget, value):
        if not 0 < value <= 999999999:
            return ValidationError(
                _(u"Invoice number must be between 1 and 999999999"))

        invoice = self.model.invoice
        branch = self.model.branch
        if invoice.check_unique_invoice_number_by_branch(value, branch):
            return ValidationError(_(u"Invoice number already used."))


class DecreaseItemStep(SellableItemStep):
    """ Wizard step for purchase order's items selection """
    model_type = StockDecrease
    item_table = StockDecreaseItem
    sellable_view = ProductWithStockBranchView
    summary_label_text = "<b>%s</b>" % api.escape(_('Total Ordered:'))
    summary_label_column = None
    sellable_editable = False
    validate_stock = True
    batch_selection_dialog = BatchDecreaseSelectionDialog
    item_editor = StockDecreaseItemEditor

    #
    # SellableItemStep
    #

    def post_init(self):
        self.hide_add_button()
        manager = get_plugin_manager()
        nfe_is_active = manager.is_active('nfe')
        if not self.wizard.create_payments and not nfe_is_active:
            self.cost_label.hide()
            self.cost.hide()
            self.cost.update(0)

        self.slave.klist.connect('cell-editing-started',
                                 self._on_klist__cell_editing_started)

        super(DecreaseItemStep, self).post_init()

    def get_sellable_view_query(self):
        # The stock quantity of consigned products can not be
        # decreased manually. See bug 5212.
        query = And(Eq(Product.consignment, False),
                    self.sellable_view.branch_id == self.model.branch_id,
                    Sellable.get_available_sellables_query(self.store))
        return self.sellable_view, query

    def get_order_item(self, sellable, cost, quantity, batch=None, parent=None):
        return self.model.add_sellable(sellable, cost, quantity, batch=batch)

    def get_saved_items(self):
        return self.model.get_items()

    def get_columns(self):
        columns = [
            Column('sellable.code', title=_('Code'), data_type=str),
            Column('sellable.description', title=_('Description'),
                   data_type=str, expand=True, searchable=True,
                   format_func=self._format_description, format_func_data=True),
            Column('sellable.category_description', title=_('Category'),
                   data_type=str, expand=True, searchable=True),
            Column('quantity', title=_('Quantity'), data_type=Decimal,
                   format_func=format_quantity),
            Column('sellable.unit_description', title=_('Unit'), data_type=str,
                   width=70),
        ]

        if self.wizard.create_payments:
            columns.extend([
                Column('cost', title=_('Cost'), data_type=currency),
                Column('total', title=_('Total'), data_type=currency),
            ])

        return columns

    def has_next_step(self):
        return self.wizard.create_payments

    def next_step(self):
        if not self.wizard.create_payments:
            return

        group = PaymentGroup(store=self.store)
        self.model.group = group
        return PaymentMethodStep(self.wizard, self, self.store, self.model,
                                 PaymentMethod.get_by_name(self.store, u'multiple'),
                                 finish_on_total=False)

    def validate(self, value):
        for item in self.model.get_items():
            if item.quantity == 0:
                value = False
                break

        super(DecreaseItemStep, self).validate(value)

    #
    # Private
    #

    def _format_description(self, item, data):
        return format_sellable_description(item.sellable, item.batch)

    #
    # Callbacks
    #

    def _on_klist__cell_editing_started(self, klist, obj, attr,
                                        renderer, editable):
        if attr == 'quantity':
            adjustment = editable.get_adjustment()
            remaining_quantity = self.get_remaining_quantity(obj.sellable,
                                                             obj.batch)
            adjustment.set_upper(obj.quantity + remaining_quantity)


class StockDecreaseWizard(BaseWizard):
    size = (775, 400)
    title = _('Manual Stock Decrease')
    need_cancel_confirmation = True

    def __init__(self, store):
        model = self._create_model(store)

        first_step = StartStockDecreaseStep(store, self, model)
        BaseWizard.__init__(self, store, first_step, model)
        self.create_payments = False

    def _create_model(self, store):
        branch = api.get_current_branch(store)
        user = api.get_current_user(store)
        employee = user.person.employee
        cfop_id = sysparam.get_object_id('DEFAULT_STOCK_DECREASE_CFOP')
        return StockDecrease(responsible=user,
                             removed_by=employee,
                             branch=branch,
                             status=StockDecrease.STATUS_INITIAL,
                             cfop_id=cfop_id,
                             store=store)

    def _receipt_dialog(self):
        msg = _('Would you like to print a receipt?')
        if yesno(msg, gtk.RESPONSE_YES,
                 _("Print receipt"), _("Don't print")):
            print_report(StockDecreaseReceipt, self.model)

    #
    # WizardStep hooks
    #

    def finish(self):
        missing = get_missing_items(self.model, self.store)
        if missing:
            run_dialog(MissingItemsDialog, self, self.model, missing)
            return False

        self.retval = self.model
        self.model.confirm()
        self.close()

        StockDecreaseWizardFinishEvent.emit(self.model)
        # Commit before printing to avoid losing data if something breaks
        self.store.confirm(self.retval)
        self._receipt_dialog()
