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

from gi.repository import Gtk
from kiwi.currency import currency, format_price
from kiwi.ui.objectlist import Column
from storm.expr import Ne

from stoqlib.api import api
from stoqlib.domain.product import StorableBatch
from stoqlib.domain.returnedsale import ReturnedSale, ReturnedSaleItem
from stoqlib.domain.sale import Sale
from stoqlib.enums import ReturnPolicy
from stoqlib.lib.defaults import MAX_INT
from stoqlib.lib.formatters import format_quantity, format_sellable_description
from stoqlib.lib.message import yesno
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoq.lib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoq.lib.gui.dialogs.batchselectiondialog import BatchIncreaseSelectionDialog
from stoq.lib.gui.events import (SaleReturnWizardFinishEvent,
                                 SaleTradeWizardFinishEvent,
                                 InvoiceSetupEvent,
                                 WizardAddSellableEvent)
from stoq.lib.gui.search.salesearch import SaleSearch
from stoq.lib.gui.utils.printing import print_report
from stoq.lib.gui.wizards.abstractwizard import SellableItemStep
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
            model = sale.create_sale_return_adapter(api.get_current_branch(self.store),
                                                    api.get_current_user(self.store),
                                                    api.get_current_station(self.store))
            for item in model.returned_items:
                _adjust_returned_sale_item(item)
        else:
            assert self._allow_unknown_sales()
            model = ReturnedSale(
                store=self.store,
                responsible=api.get_current_user(self.store),
                branch=api.get_current_branch(self.store),
                station=api.get_current_station(self.store),
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
    check_item_taxes = True

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
        adjustment = Gtk.Adjustment(lower=0, upper=MAX_INT,
                                    step_increment=1)
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
        WizardAddSellableEvent.emit(self.wizard, item)
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

    def _on_klist__cell_edited(self, klist, obj, column):
        if column.attribute == 'quantity':
            obj.will_return = bool(obj.quantity)
        elif column.attribute == 'will_return':
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
        'reason',
        'sale_total',
        'returned_total',
        'message',
    ]

    #
    #  WizardEditorStep
    #

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()
        self._update_widgets()

    def has_next_step(self):
        return False

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    #
    #  Private
    #

    def _update_widgets(self):
        if (isinstance(self.wizard, SaleTradeWizard) or
                not self.wizard.model.sale.client):
            self.box1.hide()
            # Just a precaution
            self.message.hide()

        msg = _("A reversal payment to the client will be created. "
                "You can see it on the Payable Application.")
        self.message.set_text(msg)
        policy = sysparam.get_int('RETURN_POLICY_ON_SALES')
        if policy == ReturnPolicy.RETURN_MONEY:
            self.refund.set_active(True)
        elif policy == ReturnPolicy.RETURN_CREDIT:
            self.credit.set_active(True)
        for widget in self.credit.get_group():
            widget.set_sensitive(policy == ReturnPolicy.CLIENT_CHOICE)

        self.wizard.credit = self.credit.get_active()

        self.wizard.update_view()
        self.force_validation()

    #
    #  Callbacks
    #

    def on_refund__toggled(self, widget):
        if self.refund.get_active():
            msg = _("A reversal payment to the client will be created. "
                    "You can see it on the Payable Application.")
            self.message.set_text(msg)
            self.wizard.credit = False

    def on_credit__toggled(self, widget):
        if self.credit.get_active():
            msg = (_("The client will receive %s in credit for future purchases")
                   % format_price(self.returned_total.read()))
            self.message.set_text(msg)
            self.wizard.credit = True

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
        invoice_ok = InvoiceSetupEvent.emit()
        if invoice_ok is False:
            # If there is any problem with the invoice, the event will display an error
            # message and the dialog is kept open so the user can fix whatever is wrong.
            return

        login_user = api.get_current_user(self.store)
        self.model.return_(login_user, method_name=u'credit' if self.credit else u'money')
        SaleReturnWizardFinishEvent.emit(self.model)
        self.retval = self.model
        self.close()

        # Commit before printing to avoid losing data if something breaks
        self.store.confirm(self.retval)
        if self.credit:
            if yesno(_(u'Would you like to print the credit letter?'),
                     Gtk.ResponseType.YES, _(u"Print Letter"), _(u"Don't print")):
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
