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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Sale return wizards definition """

import decimal

import gtk
from kiwi.currency import currency
from kiwi.datatypes import ValidationError, converter
from kiwi.ui.objectlist import Column
from storm.expr import Ne

from stoqlib.api import api
from stoqlib.database.runtime import get_current_user, get_current_branch
from stoqlib.domain.fiscal import Invoice
from stoqlib.domain.product import StorableBatch
from stoqlib.domain.returnedsale import ReturnedSale, ReturnedSaleItem
from stoqlib.domain.sale import Sale
from stoqlib.enums import ReturnPolicy
from stoqlib.lib.defaults import MAX_INT
from stoqlib.lib.formatters import format_quantity, format_sellable_description
from stoqlib.lib.message import info, yesno
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.pluginmanager import get_plugin_manager
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.dialogs.batchselectiondialog import BatchIncreaseSelectionDialog
from stoqlib.gui.events import (SaleReturnWizardFinishEvent,
                                SaleTradeWizardFinishEvent)
from stoqlib.gui.search.salesearch import SaleSearch
from stoqlib.gui.slaves.paymentslave import (register_payment_slaves,
                                             MultipleMethodSlave)
from stoqlib.gui.utils.printing import print_report
from stoqlib.gui.wizards.abstractwizard import SellableItemStep
from stoqlib.reporting.clientcredit import ClientCreditReport


_ = stoqlib_gettext


def _adjust_returned_sale_item(item):
    # Some temporary attrs for wizards/steps bellow
    item.will_return = bool(item.quantity)
    if item.sale_item:
        item.max_quantity = item.quantity
    else:
        item.max_quantity = MAX_INT


#
#  Steps
#


class SaleReturnSelectionStep(WizardEditorStep):
    gladefile = 'SaleReturnSelectionStep'
    model_type = object

    #
    #  WizardEditorStep
    #

    def create_model(self, store):
        # FIXME: We don't really need a model, but we need to use a
        # WizardEditorStep subclass so we can attach slaves
        return object()

    def post_init(self):
        if not self._allow_unknown_sales():
            self.unknown_sale_check.hide()
        self.register_validate_function(self._validation_func)
        self.slave.results.connect('selection-changed',
                                   self._on_results__selection_changed)
        self.force_validation()

    def setup_slaves(self):
        self.slave = SaleSearch(self.store)
        self.slave.search.set_query(self._sale_executer_query)
        self.attach_slave('place_holder', self.slave)
        self.slave.search.refresh()

    def next_step(self):
        self._update_wizard_model()
        return SaleReturnItemsStep(self.wizard, self,
                                   self.store, self.wizard.model)

    def has_next_step(self):
        return True

    #
    #  Private
    #

    def _allow_unknown_sales(self):
        return sysparam.get_bool('ALLOW_TRADE_NOT_REGISTERED_SALES')

    def _validation_func(self, value):
        has_selected = self.slave.results.get_selected()
        if self._allow_unknown_sales() and self.unknown_sale_check.get_active():
            can_advance = True
        else:
            can_advance = has_selected

        self.wizard.refresh_next(value and can_advance)

    def _update_wizard_model(self):
        wizard_model = self.wizard.model
        if wizard_model:
            # We are replacing the model. Remove old one
            wizard_model.remove()

        sale_view = self.slave.results.get_selected()
        # FIXME: Selecting a sale and then clicking on unknown_sale_check
        # will not really deselect it, not until the results are sensitive
        # again. This should be as simple as 'if sale_view'.
        if sale_view and not self.unknown_sale_check.get_active():
            sale = self.store.fetch(sale_view.sale)
            model = sale.create_sale_return_adapter()
            for item in model.returned_items:
                _adjust_returned_sale_item(item)
        else:
            assert self._allow_unknown_sales()
            model = ReturnedSale(
                store=self.store,
                responsible=get_current_user(self.store),
                branch=get_current_branch(self.store),
            )

        self.wizard.model = model

    def _sale_executer_query(self, store):
        # Only show sales that can be returned
        query = Sale.status == Sale.STATUS_CONFIRMED
        return store.find(self.slave.search_spec, query)

    #
    #  Callbacks
    #

    def _on_results__selection_changed(self, results, obj):
        self.force_validation()

    def on_unknown_sale_check__toggled(self, check):
        active = check.get_active()
        self.wizard.unkown_sale = active
        self.slave.results.set_sensitive(not active)
        if not active:
            self.slave.results.unselect_all()
        self.force_validation()


class SaleReturnItemsStep(SellableItemStep):
    model_type = ReturnedSale
    item_table = ReturnedSaleItem
    cost_editable = False
    summary_label_text = '<b>%s</b>' % api.escape(_("Total to return:"))
    # This will only be used when wizard.unkown_sale is True
    batch_selection_dialog = BatchIncreaseSelectionDialog
    stock_labels_visible = False

    #
    #  SellableItemStep
    #

    def post_init(self):
        super(SaleReturnItemsStep, self).post_init()

        self.cost_label.set_text(_("Price:"))
        self.hide_add_button()
        self.hide_edit_button()
        self.hide_del_button()
        # If we have a sale reference, we cannot add more items
        if self.model.sale:
            self.hide_item_addition_toolbar()

        self.slave.klist.connect('cell-edited', self._on_klist__cell_edited)
        self.slave.klist.connect('cell-editing-started',
                                 self._on_klist__cell_editing_started)
        self.force_validation()

    def next_step(self):
        return SaleReturnInvoiceStep(self.store, self.wizard,
                                     model=self.model, previous=self)

    def get_columns(self, editable=True):
        adjustment = gtk.Adjustment(lower=0, upper=MAX_INT,
                                    step_incr=1)
        columns = [
            Column('will_return', title=_('Return'),
                   data_type=bool, editable=editable),
            Column('sellable.code', title=_('Code'),
                   data_type=str, visible=False, sorted=True),
            Column('sellable.barcode', title=_('Barcode'),
                   data_type=str, visible=False),
            Column('sellable.description', title=_('Description'),
                   data_type=str, expand=True,
                   format_func=self._format_description,
                   format_func_data=True),
            Column('price', title=_('Sale price'),
                   data_type=currency),
        ]

        # max_quantity has no meaning on returns without a sale reference
        if self.model.sale:
            columns.append(Column('max_quantity', title=_('Sold quantity'),
                                  data_type=decimal.Decimal,
                                  format_func=format_quantity))
        kwargs = {}
        if editable:
            kwargs['spin_adjustment'] = adjustment
        columns.extend([
            Column('quantity', title=_('Quantity'),
                   data_type=decimal.Decimal, format_func=format_quantity,
                   editable=editable, **kwargs),
            Column('total', title=_('Total'),
                   data_type=currency),
        ])

        return columns

    def get_saved_items(self):
        return self.model.returned_items.find(Ne(ReturnedSaleItem.quantity, 0))

    def get_order_item(self, sellable, price, quantity, batch=None, parent=None):
        if parent:
            if parent.sellable.product.is_package:
                component = self.get_component(parent, sellable)
                quantity = parent.quantity * component.quantity
                price = component.price
            else:
                # Do not add the components if its not a package product
                return

        if batch is not None:
            batch = StorableBatch.get_or_create(
                self.store,
                storable=sellable.product_storable,
                batch_number=batch)

        item = ReturnedSaleItem(
            store=self.store,
            quantity=quantity,
            price=price,
            sellable=sellable,
            batch=batch,
            returned_sale=self.model,
            parent_item=parent
        )
        _adjust_returned_sale_item(item)
        return item

    def sellable_selected(self, sellable, batch=None):
        SellableItemStep.sellable_selected(self, sellable, batch=batch)
        if sellable:
            self.cost.update(sellable.price)

    def validate_step(self):
        items = list(self.model.returned_items)
        if not len(items):
            # Will happen on a trade without a sale reference
            return False

        returned_items = [item for item in items if item.will_return]
        if not len(returned_items):
            return False
        if not all([0 < item.quantity <= item.max_quantity for
                    item in returned_items]):
            # Just a precaution..should not happen!
            return False

        return True

    def validate(self, value):
        super(SaleReturnItemsStep, self).validate(value)
        self.wizard.refresh_next(value and self.validate_step())

    #
    #  Private
    #

    def _format_description(self, item, data):
        return format_sellable_description(item.sellable, item.batch)

    #
    #  Callbacks
    #

    def _on_klist__cell_edited(self, klist, obj, attr):
        if attr == 'quantity':
            obj.will_return = bool(obj.quantity)
        elif attr == 'will_return':
            obj.quantity = obj.max_quantity * int(obj.will_return)

        parent = obj.parent_item
        if parent:
            quantity = parent.max_quantity
            for sibling in parent.children_items:
                component = self.get_component(parent, sibling.sellable)
                # The quantity for the parent is the minimum quantity possible
                # between all siblings
                quantity = min(quantity,
                               int(sibling.quantity / component.quantity))
            parent.quantity = decimal.Decimal(quantity)
            parent.will_return = bool(parent.quantity)

        for child in obj.children_items:
            component = self.get_component(obj, child.sellable)
            child.quantity = min(obj.quantity * component.quantity,
                                 child.max_quantity)
            child.will_return = bool(child.quantity)

        self.summary.update_total()
        self.force_validation()
        self.slave.klist.queue_draw()

    def _on_klist__cell_editing_started(self, klist, obj, attr,
                                        renderer, editable):
        if attr == 'quantity':
            adjustment = editable.get_adjustment()
            # Don't let the user return more than was bought
            adjustment.set_upper(obj.max_quantity)


class SaleReturnInvoiceStep(WizardEditorStep):
    gladefile = 'SaleReturnInvoiceStep'
    model_type = ReturnedSale
    proxy_widgets = [
        'responsible',
        'invoice_number',
        'reason',
        'sale_total',
        'paid_total',
        'returned_total',
        'total_amount_abs',
    ]

    #
    #  WizardEditorStep
    #

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

        if isinstance(self.wizard, SaleTradeWizard):
            for widget in [self.total_amount_lbl, self.total_amount_abs,
                           self.total_separator]:
                widget.hide()

        self._update_widgets()

    def next_step(self):
        return SaleReturnPaymentStep(self.store, self.wizard,
                                     model=self.model, previous=self)

    def has_next_step(self):
        if isinstance(self.wizard, SaleTradeWizard):
            return False
        return self.model.total_amount > 0

    def setup_proxies(self):
        manager = get_plugin_manager()
        nfe_is_active = manager.is_active('nfe')
        self.invoice_number.set_property('mandatory', nfe_is_active)

        # Set an initial invoice number.
        if not self.model.invoice_number:
            new_invoice_number = Invoice.get_next_invoice_number(self.store)
            self.model.invoice_number = new_invoice_number

        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    #
    #  Private
    #

    def _update_widgets(self):
        self.proxy.update('total_amount_abs')

        if self.model.total_amount < 0:
            self.total_amount_lbl.set_text(_("Overpaid:"))
        elif self.model.total_amount > 0:
            self.total_amount_lbl.set_text(_("Missing:"))
        else:
            self.total_amount_lbl.set_text(_("Difference:"))

        if (isinstance(self.wizard, SaleTradeWizard) or
                not self.wizard.model.sale.client):
            self.credit_checkbutton.hide()

        policy = sysparam.get_int('RETURN_POLICY_ON_SALES')
        self.credit_checkbutton.set_sensitive(policy == ReturnPolicy.CLIENT_CHOICE)
        self.credit_checkbutton.set_active(policy == ReturnPolicy.RETURN_CREDIT)

        self.wizard.credit = self.credit_checkbutton.read()

        self.wizard.update_view()
        self.force_validation()

    #
    #  Callbacks
    #

    def on_invoice_number__validate(self, widget, value):
        if not 0 < value <= 999999999:
            return ValidationError(_("Invoice number must be between "
                                     "1 and 999999999"))
        invoice = self.model.invoice
        branch = self.model.branch
        if invoice.check_unique_invoice_number_by_branch(value, branch):
            return ValidationError(_("Invoice number already exists."))

    def on_credit_checkbutton__toggled(self, widget):
        self.wizard.credit = self.credit_checkbutton.read()


class SaleReturnPaymentStep(WizardEditorStep):
    gladefile = 'HolderTemplate'
    model_type = ReturnedSale

    #
    #  WizardEditorStep
    #

    def post_init(self):
        self.register_validate_function(self._validation_func)
        self.force_validation()

        before_debt = currency(self.model.sale_total - self.model.paid_total)
        now_debt = currency(before_debt - self.model.returned_total)
        short = _("The client's debt has changed. "
                  "Use this step to adjust the payments.")
        longdesc = _("The debt before was %s and now is %s. Cancel some unpaid "
                     "installments and create new ones.")
        info(short,
             longdesc % (converter.as_string(currency, before_debt),
                         converter.as_string(currency, now_debt)))

    def setup_slaves(self):
        register_payment_slaves()
        outstanding_value = (self.model.total_amount_abs +
                             self.model.paid_total)
        self.slave = MultipleMethodSlave(self.wizard, self, self.store,
                                         self.model, None,
                                         outstanding_value=outstanding_value,
                                         finish_on_total=False,
                                         allow_remove_paid=False)
        self.slave.enable_remove()
        self.attach_slave('place_holder', self.slave)

    def validate_step(self):
        return True

    def has_next_step(self):
        return False

    #
    #  Callbacks
    #

    def _validation_func(self, value):
        can_finish = value and self.slave.can_confirm()
        self.wizard.refresh_next(can_finish)


#
#  Wizards
#


class _BaseSaleReturnWizard(BaseWizard):
    size = (800, 450)

    def __init__(self, store, model=None):
        self.unkown_sale = False
        if model:
            # Adjust items befre creating the step, so that plugins may have a
            # chance to change the value
            for item in model.returned_items:
                _adjust_returned_sale_item(item)
            first_step = SaleReturnItemsStep(self, None, store, model)
        else:
            first_step = SaleReturnSelectionStep(store, self, None)

        BaseWizard.__init__(self, store, first_step, model)


class SaleReturnWizard(_BaseSaleReturnWizard):
    """Wizard for returning a sale"""

    title = _('Return Sale Order')
    help_section = 'sale-return'

    #
    #  BaseWizard
    #

    def finish(self):
        for payment in self.model.group.payments:
            if payment.is_preview():
                # Set payments created on SaleReturnPaymentStep as pending
                payment.set_pending()

        total_amount = self.model.total_amount
        # If the user chose to create credit for the client instead of returning
        # money, there is no need to display this messages.
        if not self.credit:
            if total_amount == 0:
                info(_("The client does not have a debt to this sale anymore. "
                       "Any existing unpaid installment will be cancelled."))
            elif total_amount < 0:
                info(_("A reversal payment to the client will be created. "
                       "You can see it on the Payable Application."))

        login_user = api.get_current_user(self.store)
        self.model.return_(method_name=u'credit' if self.credit else u'money',
                           login_user=login_user)
        SaleReturnWizardFinishEvent.emit(self.model)
        self.retval = self.model
        self.close()

        # Commit before printing to avoid losing data if something breaks
        self.store.confirm(self.retval)
        if self.credit:
            if yesno(_(u'Would you like to print the credit letter?'),
                     gtk.RESPONSE_YES, _(u"Print Letter"), _(u"Don't print")):
                print_report(ClientCreditReport, self.model.client)


class SaleTradeWizard(_BaseSaleReturnWizard):
    """Wizard for trading a sale"""

    title = _('Trade Sale Order')
    help_section = 'sale-trade'

    #
    #  BaseWizard
    #

    def finish(self):
        # Dont call model.trade() here, since it will be called on
        # POS after the new sale is created..
        SaleTradeWizardFinishEvent.emit(self.model)
        self.retval = self.model
        self.close()
