# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
from kiwi.python import Settable
from kiwi.ui.widgets.list import Column
from stoqdrivers.enum import PaymentMethodType

from stoqlib.database.runtime import (get_current_branch, new_transaction,
                                      finish_transaction)
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import INTERVALTYPE_MONTH
from stoqlib.lib.message import info
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.validators import format_quantity
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.lists import SimpleListDialog
from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.printing import print_report
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.gui.wizards.abstractwizard import SellableItemStep
from stoqlib.gui.editors.personeditor import SupplierEditor, TransporterEditor
from stoqlib.gui.editors.producteditor import ProductEditor
from stoqlib.gui.slaves.paymentslave import (CheckMethodSlave,
                                             BillMethodSlave, MoneyMethodSlave)
from stoqlib.domain.sellable import ASellable
from stoqlib.domain.payment.methods import APaymentMethod
from stoqlib.domain.person import Person
from stoqlib.domain.purchase import PurchaseOrder, PurchaseItem
from stoqlib.domain.interfaces import (IBranch, ITransporter, ISupplier,
                                       IPaymentGroup, IOutPayment, IProduct)
from stoqlib.reporting.purchase import PurchaseOrderReport, PurchaseQuoteReport

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
        if date < datetime.date.today():
            return ValidationError(
                _("Expected receival date must be set to today or "
                  "a future date"))

class PurchaseItemStep(SellableItemStep):
    """ Wizard step for purchase order's items selection """
    model_type = PurchaseOrder
    item_table = PurchaseItem
    summary_label_text = "<b>%s</b>" % _('Total Ordered:')

    #
    # Helper methods
    #

    def setup_sellable_entry(self):
        sellables = ASellable.get_unblocked_sellables(self.conn, storable=True)
        max_results = sysparam(self.conn).MAX_SEARCH_RESULTS
        self.sellable.prefill([(sellable.get_description(), sellable)
                              for sellable in sellables[:max_results]])

    def setup_slaves(self):
        SellableItemStep.setup_slaves(self)
        self.hide_add_and_edit_buttons()

        self.sellable.connect(
            'content-changed', self._on_sellable__content_changed)
        self.cost.set_editable(True)
        self.cost.connect('validate', self._on_cost__validate)

    #
    # SellableItemStep virtual methods
    #

    def get_order_item(self, sellable, cost, quantity):
        item = self.model.add_item(sellable, quantity)
        item.cost = self.cost.read()
        return item

    def get_saved_items(self):
        return list(self.model.get_items())

    def get_columns(self):
        return [
            Column('sellable.description', title=_('Description'),
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
        self.slave.set_editor(ProductEditor)
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
    model_iface = IPaymentGroup
    payment_widgets = ('method_combo',)
    order_widgets = ('subtotal_lbl',
                     'total_lbl')

    def __init__(self, wizard, previous, conn, model):
        self.order = model
        pg = IPaymentGroup(model, None)
        if pg:
            model = pg
        else:
            method = PaymentMethodType.BILL
            interval_type = INTERVALTYPE_MONTH
            model = model.addFacet(IPaymentGroup, default_method=int(method),
                                   intervals=1,
                                   interval_type=interval_type,
                                   connection=conn)
        self.slave = None
        self.discount_surcharge_slave = None
        WizardEditorStep.__init__(self, conn, wizard, model, previous)

    def _setup_widgets(self):
        items = [(_('Bill'), PaymentMethodType.BILL),
                 (_('Check'), PaymentMethodType.CHECK),
                 (_('Money'), PaymentMethodType.MONEY)]
        self.method_combo.prefill(items)

    def _get_slave_class(self, method_type):
        """Returns the slave class corresponding to a payment method type
        """
        if method_type == PaymentMethodType.BILL:
            return BillMethodSlave
        if method_type == PaymentMethodType.CHECK:
            return CheckMethodSlave
        if method_type == PaymentMethodType.MONEY:
            return MoneyMethodSlave

    def _get_slave_args(self, method_type):
        """Returns a tuple with a the slave arguments corresponding to
            a a payment method type
        """
        # payment_group is used in slave class
        self.wizard.payment_group = self.model
        payment_method = APaymentMethod.get_by_enum(self.conn, method_type)
        return (self.wizard, self, self.conn, self.order, payment_method)

    def _set_method_slave(self):
        """Sets the payment method slave"""
        method = self.method_combo.get_selected_data()
        if method is not None:
            self.model.set_method(int(method))

            slave_class = self._get_slave_class(method)
            if slave_class:
                slave_args = self._get_slave_args(method)
                self.slave = slave_class(*slave_args)
                self.attach_slave('method_slave_holder', self.slave)

    def _update_payment_method_slave(self):
        """Updates the payment method slave """
        holder_name = 'method_slave_holder'
        if self.get_slave(holder_name):
            self.slave.get_toplevel().hide()
            self.detach_slave(holder_name)
            self.slave = None
        # remove all payments created last time, if any
        self.model.clear_preview_payments(IOutPayment)
        if not self.slave:
            self._set_method_slave()

    def _update_totals(self, *args):
        for field_name in ('purchase_subtotal', 'purchase_total'):
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

    def _setup_focus(self):
        self.salesperson_name.grab_focus()
        self.notes.set_accepts_tab(False)

    #
    # WizardStep hooks
    #

    def has_next_step(self):
        return False

    def post_init(self):
        self.salesperson_name.grab_focus()
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

    def on_print_button__clicked(self, button):
        print_report(PurchaseOrderReport, self.model)


class QuoteItemsStep(PurchaseItemStep):

    def setup_slaves(self):
        PurchaseItemStep.setup_slaves(self)
        self.cost_label.hide()
        self.cost.hide()

    def get_order_item(self, sellable, cost, quantity):
        item = self.model.add_item(sellable, quantity)
        # since we are quoting products, it should not have
        # predefined cost. It should be filled later, when the
        # supplier reply our quoting request.
        item.cost = currency(0)
        return item

    def get_columns(self):
        return [
            Column('sellable.description', title=_('Description'),
                   data_type=str, expand=True, searchable=True),
            Column('quantity', title=_('Quantity'), data_type=float, width=90,
                   format_func=format_quantity),
            Column('sellable.unit_description',title=_('Unit'), data_type=str,
                   width=70),
            ]

    def _setup_summary(self):
        # disables summary label for the quoting list
        self.summary = False

    #
    # WizardStep
    #

    def post_init(self):
        PurchaseItemStep.post_init(self)
        if not self.has_next_step():
            self.wizard.enable_finish()

    def has_next_step(self):
        # if we are editing a quote, this is the first and last step
        return not self.wizard.edit

    def next_step(self):
        return QuoteSupplierStep(self.wizard, self, self.conn, self.model)


class QuoteSupplierStep(WizardEditorStep):
    gladefile = 'QuoteSupplierStep'
    model_type = PurchaseOrder

    def __init__(self, wizard, previous, conn, model):
        WizardEditorStep.__init__(self, conn, wizard, model, previous)
        self._setup_widgets()

    def _setup_widgets(self):
        self.quoting_list.set_columns(self._get_columns())
        self._populate_quoting_list()

        if not len(self.quoting_list) > 0:
            info(_(u'No supplier have been found for any of the selected '
                    'items.\nThis quote will be cancelled.'))
            self.wizard.finish()

    def _get_columns(self):
        return [Column('selected', title=" ", data_type=bool, editable=True),
                Column('supplier.person.name', title=_('Supplier'),
                        data_type=str, sorted=True, expand=True)]

    def _update_widgets(self):
        selected = self.quoting_list.get_selected()
        self.print_button.set_sensitive(selected is not None)
        self.view_products_button.set_sensitive(selected is not None)

    def _populate_quoting_list(self):
        # populate the quoting list by finding the suppliers based on the
        # products list
        quotes = {}
        # O(n*n)
        for item in self.model.get_items():
            sellable = item.sellable
            product = IProduct(sellable)
            for supplier_info in product.suppliers:
                supplier = supplier_info.supplier
                if supplier is None:
                    continue

                if supplier not in quotes.keys():
                    quotes[supplier] = [sellable]
                else:
                    quotes[supplier].append(sellable)

        for supplier, items in quotes.items():
            self.quoting_list.append(Settable(supplier=supplier,
                                              items=items,
                                              selected=True))

    def _print_quote(self):
        selected = self.quoting_list.get_selected()
        self.model.supplier = selected.supplier
        print_report(PurchaseQuoteReport, self.model)

    def _generate_quote(self, selected):
        # we use our model as a template to create new quotes
        quote = self.model.clone()
        for item in self.model.get_items():
            if item.sellable in selected.items:
                quote_item = item.clone()
                quote_item.order = quote

        quote.supplier = selected.supplier
        if not quote.get_valid():
            quote.set_valid()
        self.conn.commit()

    def _show_products(self):
        selected = self.quoting_list.get_selected()
        columns = [Column('description', title=_(u'Product'), data_type=str,
                          expand=True)]
        title = _(u'Products supplied by %s' % selected.supplier.person.name)
        run_dialog(SimpleListDialog, self, columns, selected.items,
                   title=title)

    def _update_wizard(self):
        # we need at least one supplier to finish this wizard
        can_finish = any([i.selected for i in self.quoting_list])
        self.wizard.refresh_next(can_finish)

    #
    # WizardStep hooks
    #

    def validate_step(self):
        # I am using validate_step as a callback for the finish button
        for item in self.quoting_list:
            if item.selected:
                self._generate_quote(item)

        return True

    def has_next_step(self):
        return False

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    #
    # Kiwi Callbacks
    #

    def on_print_button__clicked(self, widget):
        self._print_quote()

    def on_view_products_button__clicked(self, widget):
        self._show_products()

    def on_quoting_list__selection_changed(self, widget, item):
        self._update_widgets()

    def on_quoting_list__cell_edited(self, widget, item, cell):
        self._update_wizard()

    def on_quoting_list__row_activated(self, widget, item):
        self._show_products()


#
# Main wizard
#


class PurchaseWizard(BaseWizard):
    size = (775, 400)

    def __init__(self, conn, model=None, edit_mode=False):
        title = self._get_title(model)
        model = model or self._create_model(conn)
        if model.status != PurchaseOrder.ORDER_PENDING:
            raise ValueError('Invalid order status. It should '
                             'be ORDER_PENDING')
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
        status = PurchaseOrder.ORDER_PENDING
        return PurchaseOrder(supplier=supplier, branch=branch, status=status,
                             connection=conn)

    #
    # WizardStep hooks
    #

    def finish(self):
        if not self.model.get_valid():
            self.model.set_valid()
        self.retval = self.model
        self.close()


class QuotePurchaseWizard(BaseWizard):
    size = (775, 400)

    def __init__(self, conn, model=None):
        title = self._get_title(model)
        self.edit = model is not None
        model = model or self._create_model(conn)
        if model.status != PurchaseOrder.ORDER_QUOTING:
            raise ValueError('Invalid order status. It should '
                             'be ORDER_QUOTING')

        first_step = QuoteItemsStep(self, None, conn, model)
        BaseWizard.__init__(self, conn, first_step, model, title=title)

    def _get_title(self, model=None):
        if not model:
            return _('New Quote')
        return _('Edit Quote')

    def _create_model(self, conn):
        supplier = sysparam(conn).SUGGESTED_SUPPLIER
        branch = get_current_branch(conn)
        status = PurchaseOrder.ORDER_QUOTING
        return PurchaseOrder(supplier=supplier, branch=branch, status=status,
                             expected_receival_date=None, connection=conn)

    def _delete_model(self):
        if self.edit:
            return

        for item in self.model.get_items():
            PurchaseItem.delete(item.id, connection=self.conn)

        PurchaseOrder.delete(self.model.id, connection=self.conn)

    #
    # WizardStep hooks
    #

    def finish(self):
        self._delete_model()
        self.retval = True
        self.close()
