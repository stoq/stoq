# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2008 Async Open Source <http://www.async.com.br>
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
##              Johan Dahlin                <jdahlin@async.com.br>
##              George Kussumoto            <george@async.com.br>
##
##
""" Purchase wizard definition """

import datetime
from decimal import Decimal

from kiwi.datatypes import currency, ValidationError
from kiwi.ui.widgets.list import Column

from stoqlib.database.runtime import (get_current_branch, new_transaction,
                                      finish_transaction, get_current_user)
from stoqlib.domain.interfaces import IBranch, ITransporter, ISupplier
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.operation import register_payment_operations
from stoqlib.domain.person import Person
from stoqlib.domain.product import ProductSupplierInfo
from stoqlib.domain.purchase import PurchaseOrder, PurchaseItem
from stoqlib.domain.receiving import (ReceivingOrder, ReceivingOrderItem,
                                      get_receiving_items_by_purchase_order)
from stoqlib.domain.sellable import Sellable
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.validators import format_quantity
from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.editors.purchaseeditor import PurchaseItemEditor
from stoqlib.gui.printing import print_report
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.gui.wizards.receivingwizard import ReceivingInvoiceStep
from stoqlib.gui.wizards.abstractwizard import SellableItemStep
from stoqlib.gui.editors.personeditor import SupplierEditor, TransporterEditor
from stoqlib.gui.slaves.paymentslave import (CheckMethodSlave,
                                             BillMethodSlave, MoneyMethodSlave)
from stoqlib.reporting.purchase import PurchaseOrderReport

_ = stoqlib_gettext


#
# Wizard Steps
#


class StartPurchaseStep(WizardEditorStep):
    gladefile = 'StartPurchaseStep'
    model_type = PurchaseOrder
    proxy_widgets = ('open_date',
                     'order_number',
                     'supplier',
                     'branch',
                     'freight')
    def __init__(self, wizard, conn, model):
        WizardEditorStep.__init__(self, conn, wizard, model)

    def _fill_supplier_combo(self):
        # FIXME: Implement and use IDescribable on PersonAdaptToSupplier
        table = Person.getAdapterClass(ISupplier)
        suppliers = table.get_active_suppliers(self.conn)
        items = [(s.person.name, s) for s in suppliers]
        self.supplier.prefill(sorted(items))

    def _fill_branch_combo(self):
        # FIXME: Implement and use IDescribable on PersonAdaptToBranch
        table = Person.getAdapterClass(IBranch)
        branches = table.get_active_branches(self.conn)
        items = [(s.person.name, s) for s in branches]
        self.branch.prefill(sorted(items))

    def _setup_widgets(self):
        allow_outdated = sysparam(self.conn).ALLOW_OUTDATED_PURCHASES
        self.open_date.set_sensitive(allow_outdated)
        self._fill_supplier_combo()
        self._fill_branch_combo()
        self._update_widgets()

    def _update_widgets(self):
        has_freight = self.fob_radio.get_active()
        self.freight.set_sensitive(has_freight)
        self._update_freight()

    def _update_freight(self):
        if self.cif_radio.get_active():
            self.model.freight_type = self.model_type.FREIGHT_CIF
        else:
            self.model.freight_type = self.model_type.FREIGHT_FOB

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.open_date.grab_focus()
        self.table.set_focus_chain([self.open_date, self.order_number,
                                    self.branch, self.supplier,
                                    self.radio_hbox, self.freight])
        self.radio_hbox.set_focus_chain([self.cif_radio, self.fob_radio])
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def next_step(self):
        return PurchaseItemStep(self.wizard, self, self.conn, self.model)

    def has_previous_step(self):
        return False

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    StartPurchaseStep.proxy_widgets)

    #
    # Kiwi callbacks
    #

    def on_cif_radio__toggled(self, *args):
        self._update_widgets()

    def on_fob_radio__toggled(self, *args):
        self._update_widgets()

    def on_supplier_button__clicked(self, *args):
        trans = new_transaction()
        supplier = trans.get(self.model.supplier)

        # Since self.model.supplier always will exist here, we can't use
        # it to determine when add a new supplier or edit a selected
        # one. So, we check the supplier combo entry to determine that.
        if not self.supplier.get_text():
            supplier = None

        model = run_person_role_dialog(SupplierEditor, self, trans,
                                       supplier)
        retval = finish_transaction(trans, model)
        if retval:
            self._fill_supplier_combo()
            self.supplier.select(model)

    def on_open_date__validate(self, widget, date):
        if sysparam(self.conn).ALLOW_OUTDATED_PURCHASES:
            return
        if date < datetime.date.today():
            return ValidationError(
                _("Expected receival date must be set to today or "
                  "a future date"))

class PurchaseItemStep(SellableItemStep):
    """ Wizard step for purchase order's items selection """
    model_type = PurchaseOrder
    item_table = PurchaseItem
    summary_label_text = "<b>%s</b>" % _('Total Ordered:')

    def _set_expected_receival_date(self, item):
        supplier = self.model.supplier
        sellable = item.sellable
        for supplier_info in ProductSupplierInfo.get_info_by_supplier(
            self.conn, supplier):
            if supplier_info.product.sellable is sellable:
                delta = datetime.timedelta(days=supplier_info.lead_time)
                expected_receival = self.model.open_date + delta
                item.expected_receival_date = expected_receival
                break

    #
    # Helper methods
    #

    def setup_sellable_entry(self):
        sellables = Sellable.get_unblocked_sellables(self.conn, storable=True)
        max_results = sysparam(self.conn).MAX_SEARCH_RESULTS
        self.sellable.prefill(
            [(sellable.get_description(full_description=True), sellable)
             for sellable in sellables[:max_results]])

    def setup_slaves(self):
        SellableItemStep.setup_slaves(self)
        self.hide_add_button()

        self.sellable.connect(
            'content-changed', self._on_sellable__content_changed)
        self.cost.set_editable(True)
        self.cost.connect('validate', self._on_cost__validate)

    #
    # SellableItemStep virtual methods
    #

    def get_order_item(self, sellable, cost, quantity):
        item = self.model.add_item(sellable, quantity)
        self._set_expected_receival_date(item)
        item.cost = self.cost.read()
        return item

    def get_saved_items(self):
        return list(self.model.get_items())

    def get_columns(self):
        return [
            Column('sellable.description', title=_('Description'),
                   data_type=str, expand=True, searchable=True),
            Column('sellable.category_description', title=_('Category'),
                   data_type=str, expand=True, searchable=True),
            Column('quantity', title=_('Quantity'), data_type=float, width=90,
                   format_func=format_quantity),
            Column('sellable.unit_description',title=_('Unit'), data_type=str,
                   width=70),
            Column('cost', title=_('Cost'), data_type=currency, width=90),
            Column('total', title=_('Total'), data_type=currency, width=100),
            ]

    #
    # WizardStep hooks
    #

    def post_init(self):
        SellableItemStep.post_init(self)
        self.slave.set_editor(PurchaseItemEditor)
        self._refresh_next()
        self.product_button.hide()

    def next_step(self):
        return PurchasePaymentStep(self.wizard, self, self.conn, self.model)

    #
    # Private API
    #

    def _validate_sellable_cost(self):
        sellable = self.sellable.get_selected_data()
        if sellable is None:
            return
        for item in self.slave.klist:
            if item.sellable == sellable:
                # set the value in the cost entry only, we don't want to keep
                # a custom sellable cost outside this purchase
                self.cost.set_text(str(item.cost))
                self.cost.set_editable(False)
                return

        self.cost.set_editable(True)

    #
    # Callbacks
    #

    def _on_sellable__content_changed(self, widget):
        self._validate_sellable_cost()

    def _on_cost__validate(self, widget, value):
        if value <= Decimal(0):
            return ValidationError(_(u"The cost must be greater than zero."))


class PurchasePaymentStep(WizardEditorStep):
    gladefile = 'PurchasePaymentStep'
    model_type = PaymentGroup
    payment_widgets = ('method_combo',)
    order_widgets = ('subtotal_lbl',
                     'total_lbl')

    def __init__(self, wizard, previous, conn, model):
        self.order = model
        self.slave = None
        self.discount_surcharge_slave = None
        WizardEditorStep.__init__(self, conn, wizard, model.group, previous)

    def _setup_widgets(self):
        items = [
            (_('Bill'), PaymentMethod.get_by_name(self.conn, 'bill')),
            (_('Check'), PaymentMethod.get_by_name(self.conn, 'check')),
            (_('Money'), PaymentMethod.get_by_name(self.conn, 'money')),
            ]
        self.method_combo.prefill(items)

    def _set_method_slave(self):
        """Sets the payment method slave"""
        method = self.method_combo.get_selected_data()
        if method is None:
            return
        slave_classes = {
            'bill': BillMethodSlave,
            'check': CheckMethodSlave,
            'money': MoneyMethodSlave,
            }
        slave_class = slave_classes.get(method.method_name)
        if slave_class:
            self.wizard.payment_group = self.model
            self.slave = slave_class(self.wizard, self,
                                     self.conn, self.order, method)
            self.attach_slave('method_slave_holder', self.slave)

    def _update_payment_method_slave(self):
        """Updates the payment method slave """
        holder_name = 'method_slave_holder'
        if self.get_slave(holder_name):
            self.slave.get_toplevel().hide()
            self.detach_slave(holder_name)
            self.slave = None

        # remove all payments created last time, if any
        self.model.clear_unused()
        if not self.slave:
            self._set_method_slave()

    def _update_totals(self, *args):
        for field_name in ['purchase_subtotal', 'purchase_total']:
            self.order_proxy.update(field_name)

    #
    # WizardStep hooks
    #

    def next_step(self):
        return FinishPurchaseStep(self.wizard, self, self.conn,
                                  self.order)

    def post_init(self):
        self.method_combo.grab_focus()
        self.main_box.set_focus_chain([self.payment_method_hbox,
                                       self.method_slave_holder])
        self.payment_method_hbox.set_focus_chain([self.method_combo])
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()
        can_finish = self.slave.payment_list.get_total_difference() == 0
        self.wizard.refresh_next(can_finish)

    def setup_proxies(self):
        self._setup_widgets()
        self.order_proxy = self.add_proxy(self.order,
                                          PurchasePaymentStep.order_widgets)
        self.proxy = self.add_proxy(self.model,
                                    PurchasePaymentStep.payment_widgets)
        # Set the first payment method as default
        self.method_combo.select_item_by_position(0)

    #
    # callbacks
    #

    def on_method_combo__content_changed(self, *args):
        self._update_payment_method_slave()


class FinishPurchaseStep(WizardEditorStep):
    gladefile = 'FinishPurchaseStep'
    model_type = PurchaseOrder
    proxy_widgets = ('salesperson_name',
                     'receival_date',
                     'transporter',
                     'notes')

    def __init__(self, wizard, previous, conn, model):
        WizardEditorStep.__init__(self, conn, wizard, model, previous)

    def _setup_transporter_entry(self):
        # FIXME: Implement and use IDescribable on PersonAdaptToTransporter
        table = Person.getAdapterClass(ITransporter)
        transporters = table.get_active_transporters(self.conn)
        items = [(t.person.name, t) for t in transporters]
        self.transporter.prefill(items)

    def _set_receival_date_suggestion(self):
        receival_date = self.model.get_items().max('expected_receival_date')
        if receival_date:
            self.model.expected_receival_date = receival_date

    def _setup_focus(self):
        self.salesperson_name.grab_focus()
        self.notes.set_accepts_tab(False)

    def _create_receiving_order(self):
        receiving_model = ReceivingOrder(
            responsible=get_current_user(self.conn),
            purchase=self.model,
            supplier=self.model.supplier,
            branch=self.model.branch,
            transporter=self.model.transporter,
            invoice_number=None,
            connection=self.conn)

        # Creates ReceivingOrderItem's
        get_receiving_items_by_purchase_order(self.model, receiving_model)

        self.wizard.receiving_model = receiving_model

    #
    # WizardStep hooks
    #

    def has_next_step(self):
        return self.receive_now.get_active()

    def next_step(self):
        # In case the check box for receiving the products now is not active,
        # This is the last step.
        if not self.receive_now.get_active():
            return

        self._create_receiving_order()
        return ReceivingInvoiceStep(self.conn, self.wizard,
                                    self.wizard.receiving_model, self)

    def post_init(self):
        # A receiving model was created. We should remove it (and its items),
        # since after this step we can either receive the products now or
        # later, on the stock application.
        receiving_model = self.wizard.receiving_model
        if receiving_model:
            for item in receiving_model.get_items():
                ReceivingOrderItem.delete(item.id, self.conn)

            ReceivingOrder.delete(receiving_model.id, connection=self.conn)
            self.wizard.receiving_model = None


        self.salesperson_name.grab_focus()
        self._set_receival_date_suggestion()
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def setup_proxies(self):
        self._setup_transporter_entry()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    #
    # Kiwi callbacks
    #

    def on_receival_date__validate(self, widget, date):
        if date < datetime.date.today():
            return ValidationError(_("Expected receival date must be set to a future date"))

    def on_transporter_button__clicked(self, button):
        trans = new_transaction()
        transporter = trans.get(self.model.transporter)
        model =  run_person_role_dialog(TransporterEditor, self, trans,
                                        transporter)
        rv = finish_transaction(trans, model)
        trans.close()
        if rv:
            self._setup_transporter_entry()
            self.transporter.select(model)

    def on_receive_now__toggled(self, widget):
        if self.receive_now.get_active():
            self.wizard.disable_finish()
        else:
            self.wizard.enable_finish()

    def on_print_button__clicked(self, button):
        print_report(PurchaseOrderReport, self.model)


#
# Main wizard
#


class PurchaseWizard(BaseWizard):
    size = (775, 400)

    def __init__(self, conn, model=None, edit_mode=False):
        title = self._get_title(model)
        model = model or self._create_model(conn)
        # If we receive the order right after the purchase.
        self.receiving_model = None
        if model.status != PurchaseOrder.ORDER_PENDING:
            raise ValueError('Invalid order status. It should '
                             'be ORDER_PENDING')
        register_payment_operations()
        first_step = StartPurchaseStep(self, conn, model)
        BaseWizard.__init__(self, conn, first_step, model, title=title,
                            edit_mode=edit_mode)

    def _get_title(self, model=None):
        if not model:
            return _('New Order')
        return _('Edit Order')

    def _create_model(self, conn):
        supplier = sysparam(conn).SUGGESTED_SUPPLIER
        branch = get_current_branch(conn)
        group = PaymentGroup(connection=conn)
        status = PurchaseOrder.ORDER_PENDING
        return PurchaseOrder(supplier=supplier,
                             branch=branch,
                             status=status,
                             group=group,
                             connection=conn)

    #
    # WizardStep hooks
    #

    def finish(self):
        if not self.model.get_valid():
            self.model.set_valid()
        self.retval = self.model

        if self.receiving_model:
            if not self.receiving_model.get_valid():
                self.receiving_model.set_valid()
            self.model.confirm()
            # Confirming the receiving will close the purchase
            self.receiving_model.confirm()

        self.close()
