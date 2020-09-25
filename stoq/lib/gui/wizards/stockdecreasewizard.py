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

from gi.repository import Gtk
from kiwi.currency import currency
from kiwi.ui.objectlist import Column
from storm.expr import And, Eq

from stoqlib.api import api
from stoqlib.domain.costcenter import CostCenter
from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.person import Branch, Employee, Person
from stoqlib.domain.product import Product
from stoqlib.domain.sale import Delivery
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.stockdecrease import StockDecrease, StockDecreaseItem
from stoqlib.domain.views import ProductWithStockBranchView
from stoqlib.exceptions import TaxError
from stoqlib.lib.defaults import MAX_INT
from stoqlib.lib.formatters import format_quantity, format_sellable_description
from stoqlib.lib.message import yesno, warning
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.pluginmanager import get_plugin_manager
from stoqlib.lib.translation import stoqlib_gettext
from stoq.lib.gui.base.dialogs import run_dialog
from stoq.lib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoq.lib.gui.dialogs.batchselectiondialog import BatchDecreaseSelectionDialog
from stoq.lib.gui.dialogs.missingitemsdialog import get_missing_items, MissingItemsDialog
from stoq.lib.gui.editors.deliveryeditor import CreateDeliveryModel, CreateDeliveryEditor
from stoq.lib.gui.editors.stockdecreaseeditor import StockDecreaseItemEditor
from stoq.lib.gui.events import (StockDecreaseWizardFinishEvent, InvoiceSetupEvent,
                                 WizardAddSellableEvent, StockOperationPersonValidationEvent)
from stoq.lib.gui.utils.printing import print_report
from stoq.lib.gui.wizards.abstractwizard import SellableItemStep
from stoq.lib.gui.wizards.salewizard import PaymentMethodStep
from stoqlib.reporting.stockdecrease import StockDecreaseReceipt

_ = stoqlib_gettext


#
# Wizard Steps
#


class StartStockDecreaseStep(WizardEditorStep):
    gladefile = 'StartStockDecreaseStep'
    model_type = StockDecrease
    stock_decrease_widgets = ['confirm_date',
                              'branch',
                              'reason',
                              'removed_by',
                              'cfop',
                              'cost_center',
                              'person']
    invoice_widgets = ['operation_nature']
    proxy_widgets = stock_decrease_widgets + invoice_widgets

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

    def _set_receiving_order_data(self):
        order = self.wizard.receiving_order
        self.branch.update(order.branch)
        cfop = sysparam.get_object(self.store, 'DEFAULT_PURCHASE_RETURN_CFOP')
        self.cfop.update(cfop)
        if order.receiving_invoice:
            self.person.update(order.receiving_invoice.supplier.person.id)
        for widget in (self.branch, self.person):
            if widget.is_valid():
                widget.set_sensitive(False)

    def _setup_widgets(self):
        self.confirm_date.set_sensitive(False)
        self._fill_employee_combo()
        self._fill_branch_combo()
        self._fill_cfop_combo()
        self._fill_cost_center_combo()
        self._fill_person_combo()

        manager = get_plugin_manager()
        nfe_is_active = manager.is_active('nfe')
        self.person.set_property('mandatory', nfe_is_active)

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
        self.stock_decrease_proxy = self.add_proxy(self.model,
                                                   self.stock_decrease_widgets)
        self.invoice_proxy = self.add_proxy(self.model.invoice,
                                            StartStockDecreaseStep.invoice_widgets)
        if self.wizard.receiving_order is not None:
            self._set_receiving_order_data()

    #
    # Callbacks
    #

    def on_branch__validate(self, widget, branch):
        return StockOperationPersonValidationEvent.emit(branch.person, type(branch))

    def on_person__validate(self, widget, person_id):
        person = self.store.get(Person, person_id)
        return StockOperationPersonValidationEvent.emit(person, type(person))


class DecreaseItemStep(SellableItemStep):
    """ Wizard step for purchase order's items selection """
    model_type = StockDecrease
    item_table = StockDecreaseItem
    sellable_view = ProductWithStockBranchView
    summary_label_text = "<b>%s</b>" % api.escape(_('Total quantity:'))
    summary_label_column = 'quantity'
    sellable_editable = False
    validate_stock = True
    batch_selection_dialog = BatchDecreaseSelectionDialog
    item_editor = StockDecreaseItemEditor
    check_item_taxes = True

    #
    # SellableItemStep
    #

    def post_init(self):
        self.hide_add_button()
        manager = get_plugin_manager()
        nfe_is_active = manager.is_any_active(['nfce', 'nfe'])
        if not self.wizard.create_payments and not nfe_is_active:
            self.cost_label.hide()
            self.cost.hide()
            self.cost.update(0)

        self.slave.klist.connect('cell-editing-started',
                                 self._on_klist__cell_editing_started)

        if self.wizard.receiving_order is not None:
            self.hide_item_addition_toolbar()

        super(DecreaseItemStep, self).post_init()

    def setup_slaves(self):
        SellableItemStep.setup_slaves(self)
        self._delivery = None
        self._delivery_item = None

        self.delivery_button = self.slave.add_extra_button(label=_("Add Delivery"))
        self.delivery_button.set_sensitive(bool(len(self.slave.klist)))

        self.slave.klist.connect('has_rows', self._on_klist__has_rows)
        self.delivery_button.connect('clicked',
                                     self._on_delivery_button__clicked)

    def get_sellable_view_query(self):
        # The stock quantity of consigned products can not be
        # decreased manually. See bug 5212.
        query = And(Eq(Product.consignment, False),
                    self.sellable_view.branch_id == self.model.branch_id,
                    Sellable.get_available_sellables_query(self.store))
        return self.sellable_view, query

    def get_order_item(self, sellable, cost, quantity, batch=None, parent=None):
        item = self.model.add_sellable(sellable, cost, quantity, batch=batch)
        # FIXME this attibute is used by DeliveyEditor
        item.deliver = False
        WizardAddSellableEvent.emit(self.wizard, item)
        return item

    def get_saved_items(self):
        return self.model.get_items()

    def get_columns(self):
        ext_args = {}
        is_receiving_return = bool(self.wizard.receiving_order)
        # The quantity column will only be editable if this decrease refers to
        # a receiving return
        if is_receiving_return:
            ext_args.update({
                'spin_adjustment': Gtk.Adjustment(lower=0, upper=MAX_INT,
                                                  step_increment=1),
                'editable': True})
        columns = [
            Column('sellable.code', title=_('Code'), data_type=str),
            Column('sellable.description', title=_('Description'),
                   data_type=str, expand=True, searchable=True,
                   format_func=self._format_description, format_func_data=True),
            Column('sellable.category_description', title=_('Category'),
                   data_type=str, expand=True, searchable=True),
            Column('quantity', title=_('Quantity'), data_type=Decimal,
                   format_func=format_quantity, **ext_args),
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
    # WizardStep hooks
    #

    def validate_step(self):
        if self._delivery is not None:
            delivery = Delivery(
                store=self.store,
                transporter_id=self._delivery.transporter_id,
                invoice=self.model.invoice,
                address=self._delivery.address,
                freight_type=self._delivery.freight_type,
                volumes_kind=self._delivery.volumes_kind,
                volumes_quantity=self._delivery.volumes_quantity,
                volumes_gross_weight=self._delivery.volumes_gross_weight,
                volumes_net_weight=self._delivery.volumes_net_weight,
                vehicle_license_plate=self._delivery.vehicle_license_plate,
                vehicle_state=self._delivery.vehicle_state,
                vehicle_registration=self._delivery.vehicle_registration,
            )
        else:
            delivery = None

        for item in self.slave.klist:
            item.delivery = delivery if getattr(item, 'deliver', False) else None

        return super(DecreaseItemStep, self).validate_step()

    #
    # Private
    #

    def _format_description(self, item, data):
        return format_sellable_description(item.sellable, item.batch)

    def _create_or_update_delivery(self):
        delivery_service = sysparam.get_object(self.store, 'DELIVERY_SERVICE')
        delivery_sellable = delivery_service.sellable

        items = [item for item in self.slave.klist
                 if item.sellable.product is not None]

        if self._delivery is not None:
            model = self._delivery

        else:
            model = CreateDeliveryModel(
                price=delivery_sellable.price, recipient=self.model.person)

        rv = run_dialog(
            CreateDeliveryEditor, self.get_toplevel().get_toplevel(),
            self.store, model=model, items=items, person_type=Person)

        if not rv:
            return

        self._delivery = rv
        if self._delivery_item:
            self.slave.klist.update(self._delivery_item)
        else:
            self._delivery_item = self.get_order_item(
                delivery_sellable, self._delivery.price, 1)
            self.slave.klist.append(None, self._delivery_item)

    #
    # Callbacks
    #

    def on_slave__before_edit_item(self, slave, item):
        # Do not try to edit a delivery
        if item != self._delivery_item:
            return

        self._create_or_update_delivery()
        return self._delivery_item

    def on_slave__before_delete_items(self, klist, items):
        for item in items:
            if item == self._delivery_item:
                self._delivery_item = None
                self._delivery = None

    def _on_klist__cell_editing_started(self, klist, obj, attr,
                                        renderer, editable):
        if attr == 'quantity':
            adjustment = editable.get_adjustment()
            remaining_quantity = self.get_remaining_quantity(obj.sellable,
                                                             obj.batch)
            adjustment.set_upper(obj.quantity + remaining_quantity)

    def _on_klist__has_rows(self, klist, has_rows):
        if self.delivery_button is not None:
            self.delivery_button.set_sensitive(has_rows)

    def _on_delivery_button__clicked(self, button):
        self._create_or_update_delivery()


class StockDecreaseWizard(BaseWizard):
    size = (775, 400)
    title = _('Manual Stock Decrease')
    need_cancel_confirmation = True

    def __init__(self, store, receiving_order=None):
        self.receiving_order = receiving_order
        if self.receiving_order is not None:
            self.title = _('Receiving Order Return')

        model = self._create_model(store)
        first_step = StartStockDecreaseStep(store, self, model)
        BaseWizard.__init__(self, store, first_step, model)
        self.create_payments = False

    def _create_model(self, store):
        if self.receiving_order:
            return StockDecrease.create_for_receiving_order(self.receiving_order,
                                                            api.get_current_branch(store),
                                                            api.get_current_station(store),
                                                            api.get_current_user(store))

        branch = api.get_current_branch(store)
        user = api.get_current_user(store)
        employee = user.person.employee
        cfop_id = sysparam.get_object_id('DEFAULT_STOCK_DECREASE_CFOP')
        stock_decrease = StockDecrease(store=store,
                                       responsible=user,
                                       removed_by=employee,
                                       branch=branch,
                                       station=api.get_current_station(store),
                                       status=StockDecrease.STATUS_INITIAL,
                                       cfop_id=cfop_id)
        stock_decrease.invoice.operation_nature = self.title
        return stock_decrease

    def _receipt_dialog(self):
        msg = _('Would you like to print a receipt?')
        if yesno(msg, Gtk.ResponseType.YES,
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

        # If this wizard is for a purchase return, the items are automatically
        # added so the tax check escaped. So we do it now.
        if self.receiving_order is not None:
            missing_tax_info = []
            for item in self.model.get_items():
                sellable = item.sellable
                try:
                    sellable.check_taxes_validity(self.model.branch)
                except TaxError:
                    missing_tax_info.append(sellable.description)
            if missing_tax_info:
                warning(_("There are some items with missing tax information"),
                        ', '.join(missing_tax_info))
                return False

        invoice_ok = InvoiceSetupEvent.emit()
        if invoice_ok is False:
            # If there is any problem with the invoice, the event will display an error
            # message and the dialog is kept open so the user can fix whatever is wrong.
            return

        self.retval = self.model
        self.store.confirm(self.model)
        self.model.confirm(api.get_current_user(self.store))
        self.close()

        StockDecreaseWizardFinishEvent.emit(self.model)
        # Commit before printing to avoid losing data if something breaks
        self.store.confirm(self.retval)
        self._receipt_dialog()
