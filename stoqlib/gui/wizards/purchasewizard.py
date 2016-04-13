# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source <http://www.async.com.br>
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
""" Purchase wizard definition """

import datetime
from decimal import Decimal

import gtk
from kiwi.component import get_utility
from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.ui.objectlist import Column

from stoqlib.api import api
from stoqlib.domain.inventory import Inventory
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.person import Branch, Supplier, Transporter
from stoqlib.domain.product import ProductSupplierInfo
from stoqlib.domain.purchase import PurchaseOrder, PurchaseItem
from stoqlib.domain.receiving import ReceivingOrder
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.views import ProductFullStockItemSupplierView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.editors.purchaseeditor import PurchaseItemEditor
from stoqlib.gui.editors.personeditor import SupplierEditor, TransporterEditor
from stoqlib.gui.interfaces import IDomainSlaveMapper
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.gui.wizards.receivingwizard import ReceivingInvoiceStep
from stoqlib.gui.wizards.abstractwizard import SellableItemStep
from stoqlib.gui.search.sellablesearch import PurchaseSellableSearch
from stoqlib.gui.slaves.paymentmethodslave import SelectPaymentMethodSlave
from stoqlib.gui.slaves.paymentslave import register_payment_slaves
from stoqlib.gui.utils.printing import print_report
from stoqlib.lib.defaults import MAX_INT
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.message import info
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.permissions import PermissionManager
from stoqlib.lib.formatters import format_quantity, get_formatted_cost
from stoqlib.reporting.purchase import PurchaseOrderReport

_ = stoqlib_gettext


#
# Wizard Steps
#


class StartPurchaseStep(WizardEditorStep):
    gladefile = 'StartPurchaseStep'
    model_type = PurchaseOrder
    proxy_widgets = ['open_date',
                     'identifier',
                     'supplier',
                     'branch',
                     'expected_freight',
                     ]

    def __init__(self, wizard, store, model):
        WizardEditorStep.__init__(self, store, wizard, model)
        pm = PermissionManager.get_permission_manager()
        if not pm.can_create('Supplier'):
            self.add_supplier.hide()
        if not pm.can_edit('Supplier'):
            self.edit_supplier.hide()

    def _fill_supplier_combo(self):
        suppliers = Supplier.get_active_suppliers(self.store)
        self.edit_supplier.set_sensitive(any(suppliers))
        self.supplier.prefill(api.for_person_combo(suppliers))

    def _fill_branch_combo(self):
        branches = Branch.get_active_branches(self.store)
        self.branch.prefill(api.for_person_combo(branches))
        self.branch.set_sensitive(api.can_see_all_branches())

    def _setup_widgets(self):
        allow_outdated = sysparam.get_bool('ALLOW_OUTDATED_OPERATIONS')
        self.open_date.set_property('mandatory', True)
        self.open_date.set_sensitive(allow_outdated)
        self._fill_supplier_combo()
        self._fill_branch_combo()
        if self.model.freight_type == self.model_type.FREIGHT_FOB:
            self.fob_radio.set_active(True)
        else:
            self.cif_radio.set_active(True)

        self._update_widgets()

    def _update_widgets(self):
        has_freight = self.fob_radio.get_active()
        self.expected_freight.set_sensitive(has_freight)

        if self.cif_radio.get_active():
            self.model.freight_type = self.model_type.FREIGHT_CIF
        else:
            self.model.freight_type = self.model_type.FREIGHT_FOB

    def _run_supplier_dialog(self, supplier):
        store = api.new_store()
        if supplier is not None:
            supplier = store.fetch(self.model.supplier)
        model = run_person_role_dialog(SupplierEditor, self.wizard, store,
                                       supplier)
        retval = store.confirm(model)
        if retval:
            model = self.store.fetch(model)
            self._fill_supplier_combo()
            self.supplier.select(model)
        store.close()

    def _add_supplier(self):
        self._run_supplier_dialog(supplier=None)

    def _edit_supplier(self):
        supplier = self.supplier.get_selected()
        self._run_supplier_dialog(supplier)

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.open_date.grab_focus()

        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def next_step(self):
        self.wizard.all_products = self.all_products.get_active()
        if self.wizard.is_for_another_branch() and self.model.identifier > 0:
            info(_('The identifier for this purchase will be defined when it '
                   'is synchronized to the detination branch'))
            self.model.identifier = self.wizard.temporary_identifier
        return PurchaseItemStep(self.wizard, self, self.store, self.model)

    def has_previous_step(self):
        return False

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    StartPurchaseStep.proxy_widgets)

    #
    # Kiwi callbacks
    #

    def on_fob_radio__toggled(self, *args):
        self._update_widgets()

    def on_add_supplier__clicked(self, button):
        self._add_supplier()

    def on_supplier__content_changed(self, supplier):
        self.edit_supplier.set_sensitive(bool(self.supplier.get_selected()))

    def on_edit_supplier__clicked(self, button):
        self._edit_supplier()

    def on_open_date__validate(self, widget, date):
        if sysparam.get_bool('ALLOW_OUTDATED_OPERATIONS'):
            return
        if date < localtoday().date():
            return ValidationError(
                _("Open date must be set to today or "
                  "a future date"))

    def on_expected_freight__validate(self, widget, value):
        if value < 0:
            return ValidationError(_(u'The expected freight value must be a '
                                     'positive number.'))


class PurchaseItemStep(SellableItemStep):
    """ Wizard step for purchase order's items selection """
    model_type = PurchaseOrder
    item_table = PurchaseItem
    summary_label_text = "<b>%s</b>" % api.escape(_('Total Ordered:'))
    sellable_editable = True
    item_editor = PurchaseItemEditor
    sellable_search = PurchaseSellableSearch

    def _set_expected_receival_date(self, item):
        supplier = self.model.supplier
        product = item.sellable.product
        supplier_info = self.store.find(ProductSupplierInfo, product=product,
                                        supplier=supplier).one()
        if supplier_info is not None:
            delta = datetime.timedelta(days=supplier_info.lead_time)
            expected_receival = self.model.open_date + delta
            item.expected_receival_date = expected_receival

    #
    # Helper methods
    #

    def get_sellable_view_query(self):
        supplier = self.model.supplier
        if self.wizard.all_products:
            supplier = None

        # If we our query includes the supplier, we must use another viewable,
        # that actually joins with that table
        if supplier:
            viewable = ProductFullStockItemSupplierView
        else:
            viewable = self.sellable_view

        query = Sellable.get_unblocked_sellables_query(self.store, supplier=supplier,
                                                       consigned=self.model.consigned)
        return viewable, query

    def setup_slaves(self):
        SellableItemStep.setup_slaves(self)
        self.hide_add_button()
        self.cost.set_editable(True)
        self.quantity.connect('validate', self._on_quantity__validate)
        self.slave.klist.connect('selection-changed',
                                 self._on_klist_selection_changed)

    #
    # SellableItemStep virtual methods
    #

    def validate(self, value):
        SellableItemStep.validate(self, value)
        can_purchase = self.model.purchase_total > 0
        self.wizard.refresh_next(value and can_purchase)

    def get_order_item(self, sellable, cost, quantity, batch=None, parent=None):
        assert batch is None
        # Associate the product with the supplier if they are not yet. This
        # happens when the user checked the option to show all products on the
        # first step
        supplier_info = self._get_supplier_info()
        if not supplier_info:
            supplier_info = ProductSupplierInfo(product=sellable.product,
                                                supplier=self.model.supplier,
                                                store=self.store)
        if parent:
            component = self.get_component(parent, sellable)
            quantity = quantity * component.quantity
        else:
            if sellable.product.is_package:
                cost = Decimal('0')
            supplier_info.base_cost = cost

        item = self.model.add_item(sellable, quantity, parent=parent)
        self._set_expected_receival_date(item)
        item.cost = cost
        return item

    def get_saved_items(self):
        return list(self.model.get_items())

    def sellable_selected(self, sellable, batch=None):
        super(PurchaseItemStep, self).sellable_selected(sellable, batch=batch)
        supplier_info = self._get_supplier_info()
        if not supplier_info:
            return

        minimum = supplier_info.minimum_purchase
        self.quantity.set_adjustment(gtk.Adjustment(lower=minimum,
                                                    upper=MAX_INT,
                                                    step_incr=1))
        self.quantity.set_value(minimum)
        self.cost.set_value(supplier_info.base_cost)

    def get_sellable_search_extra_kwargs(self):
        return dict(supplier=self.model.supplier)

    def get_columns(self):
        return [
            Column('sellable.code', title=_('Code'), width=100, data_type=str),
            Column('sellable.description', title=_('Description'),
                   data_type=str, width=250, searchable=True, expand=True),
            Column('sellable.category_description', title=_('Category'),
                   data_type=str, searchable=True, visible=False),
            Column('quantity', title=_('Quantity'), data_type=float, width=90,
                   format_func=format_quantity),
            Column('expected_receival_date', title=_('Expected Receival'),
                   data_type=datetime.date, visible=False),
            Column('sellable.unit_description', title=_('Unit'), data_type=str,
                   width=70),
            Column('cost', title=_('Cost'), data_type=currency,
                   format_func=get_formatted_cost, width=90),
            Column('total', title=_('Total'), data_type=currency, width=100),
        ]

    #
    # WizardStep hooks
    #

    def next_step(self):
        if self.model.consigned:
            return FinishPurchaseStep(self.store, self.wizard, self.model, self)
        return PurchasePaymentStep(self.wizard, self, self.store, self.model)

    #
    # Private API
    #

    def _get_supplier_info(self):
        sellable = self.proxy.model.sellable
        if not sellable:
            # FIXME: We should not be accessing a private method here
            sellable, batch = self._get_sellable_and_batch()
        if not sellable:
            return
        product = sellable.product
        supplier = self.model.supplier
        return self.store.find(ProductSupplierInfo, product=product,
                               supplier=supplier).one()

    #
    # Callbacks
    #

    def _on_quantity__validate(self, widget, value):
        if not self.proxy.model.sellable:
            return

        supplier_info = self._get_supplier_info()
        if supplier_info and value < supplier_info.minimum_purchase:
            return ValidationError(_(u'Quantity below the minimum required '
                                     'by the supplier'))
        return super(PurchaseItemStep,
                     self).on_quantity__validate(widget, value)

    def _on_klist_selection_changed(self, klist, data):
        can_delete = all(item.quantity_received == 0 and item.parent_item is None
                         for item in data)
        self.slave.delete_button.set_sensitive(can_delete)


class PurchasePaymentStep(WizardEditorStep):
    gladefile = 'PurchasePaymentStep'
    model_type = PaymentGroup

    def __init__(self, wizard, previous, store, model,
                 outstanding_value=currency(0)):
        self.order = model
        self.slave = None
        self.discount_surcharge_slave = None
        self.outstanding_value = outstanding_value

        if not model.payments.count():
            # Default values
            self._installments_number = None
            self._first_duedate = None
            self._method = 'bill'
        else:
            # FIXME: SqlObject returns count as long, but we need it as int.
            self._installments_number = int(model.payments.count())
            self._method = model.payments[0].method.method_name

            # due_date is datetime.datetime. Converting it to datetime.date
            due_date = model.payments[0].due_date.date()
            self._first_duedate = (due_date >= localtoday().date() and
                                   due_date or None)

        WizardEditorStep.__init__(self, store, wizard, model.group, previous)

    def _setup_widgets(self):
        register_payment_slaves()

        self._ms = SelectPaymentMethodSlave(store=self.store,
                                            payment_type=Payment.TYPE_OUT,
                                            default_method=self._method,
                                            no_payments=True)
        self._ms.connect_after('method-changed',
                               self._after_method_select__method_changed)

        self.attach_slave('method_select_holder', self._ms)
        self._update_payment_method_slave()

    def _set_method_slave(self):
        """Sets the payment method slave"""
        method = self._ms.get_selected_method()
        if not method:
            return
        domain_mapper = get_utility(IDomainSlaveMapper)
        slave_class = domain_mapper.get_slave_class(method)
        if slave_class:
            self.wizard.payment_group = self.model
            self.slave = slave_class(self.wizard, self,
                                     self.store, self.order, method,
                                     outstanding_value=self.outstanding_value,
                                     first_duedate=self._first_duedate,
                                     installments_number=self._installments_number,
                                     temporary_identifiers=self.wizard.is_for_another_branch())
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

    #
    # WizardStep hooks
    #

    def validate_step(self):
        if self.slave:
            return self.slave.finish()
        return True

    def next_step(self):
        return FinishPurchaseStep(self.store, self.wizard, self.order, self)

    def post_init(self):
        self.model.clear_unused()
        self.main_box.set_focus_chain([self.method_select_holder,
                                       self.method_slave_holder])
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def setup_proxies(self):
        self._setup_widgets()

    #
    # callbacks
    #

    def _after_method_select__method_changed(self, slave, method):
        self._update_payment_method_slave()


class FinishPurchaseStep(WizardEditorStep):
    gladefile = 'FinishPurchaseStep'
    model_type = PurchaseOrder
    proxy_widgets = ('salesperson_name',
                     'expected_receival_date',
                     'transporter',
                     'notes')

    def _setup_transporter_entry(self):
        self.add_transporter.set_tooltip_text(_("Add a new transporter"))
        self.edit_transporter.set_tooltip_text(_("Edit the selected transporter"))

        items = Transporter.get_active_transporters(self.store)
        self.transporter.prefill(api.for_person_combo(items))
        self.transporter.set_sensitive(not items.is_empty())
        self.edit_transporter.set_sensitive(not items.is_empty())

    def _set_receival_date_suggestion(self):
        receival_date = self.model.get_items().max(PurchaseItem.expected_receival_date)
        if receival_date:
            self.expected_receival_date.update(receival_date)

    def _setup_focus(self):
        self.salesperson_name.grab_focus()
        self.notes.set_accepts_tab(False)

    def _create_receiving_order(self):
        # since we will create a new receiving order, we should confirm the
        # purchase first. Note that the purchase may already be confirmed
        if self.model.status in [PurchaseOrder.ORDER_PENDING,
                                 PurchaseOrder.ORDER_CONSIGNED]:
            self.model.confirm()

        temporary_identifier = None
        if self.wizard.is_for_another_branch():
            temporary_identifier = ReceivingOrder.get_temporary_identifier(self.store)

        receiving_model = ReceivingOrder(
            identifier=temporary_identifier,
            responsible=api.get_current_user(self.store),
            supplier=self.model.supplier,
            branch=self.model.branch,
            transporter=self.model.transporter,
            invoice_number=None,
            store=self.store)
        receiving_model.add_purchase(self.model)

        # Creates ReceivingOrderItem's
        for item in self.model.get_pending_items():
            receiving_model.add_purchase_item(item)

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
        return ReceivingInvoiceStep(self.store, self.wizard,
                                    self.wizard.receiving_model)

    def post_init(self):
        # A receiving model was created. We should remove it (and its items),
        # since after this step we can either receive the products now or
        # later, on the stock application.
        receiving_model = self.wizard.receiving_model
        if receiving_model:
            for item in receiving_model.get_items():
                self.store.remove(item)
            self.store.remove(receiving_model)
            self.wizard.receiving_model = None

        self.salesperson_name.grab_focus()
        self._set_receival_date_suggestion()

        # If the purchase is for another branch, we should not allow receiving
        if self.model.has_batch_item():
            self.receive_now.hide()

        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def setup_proxies(self):
        # Avoid changing widget states in __init__, so that plugins have a
        # chance to override the default settings
        has_open_inventory = Inventory.has_open(self.store,
                                                api.get_current_branch(self.store))
        self.receive_now.set_sensitive(not bool(has_open_inventory))

        self._setup_focus()
        self._setup_transporter_entry()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    def _run_transporter_editor(self, transporter=None):
        store = api.new_store()
        transporter = store.fetch(transporter)
        model = run_person_role_dialog(TransporterEditor, self.wizard, store,
                                       transporter)
        rv = store.confirm(model)
        store.close()
        if rv:
            self._setup_transporter_entry()
            model = self.store.fetch(model)
            self.transporter.select(model)

    def on_expected_receival_date__validate(self, widget, date):
        if sysparam.get_bool('ALLOW_OUTDATED_OPERATIONS'):
            return

        if date < localtoday().date():
            return ValidationError(_("Expected receival date must be set to a future date"))

    def on_add_transporter__clicked(self, button):
        self._run_transporter_editor()

    def on_edit_transporter__clicked(self, button):
        self._run_transporter_editor(self.transporter.get_selected())

    def on_transporter__content_changed(self, category):
        self.edit_transporter.set_sensitive(bool(self.transporter.get_selected()))

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
    help_section = 'purchase-new'
    need_cancel_confirmation = True

    def __init__(self, store, model=None, edit_mode=False):
        title = self._get_title(model)
        self.sync_mode = api.sysparam.get_bool('SYNCHRONIZED_MODE')
        self.current_branch = api.get_current_branch(store)
        if self.sync_mode and not model:
            self.temporary_identifier = PurchaseOrder.get_temporary_identifier(store)

        model = model or self._create_model(store)
        # Should we show all products or only the ones associated with the
        # selected supplier?
        self.all_products = False

        # If we receive the order right after the purchase.
        self.receiving_model = None
        purchase_edit = [PurchaseOrder.ORDER_CONFIRMED,
                         PurchaseOrder.ORDER_PENDING]

        if not model.status in purchase_edit:
            raise ValueError('Invalid order status. It should '
                             'be ORDER_PENDING or ORDER_CONFIRMED')
        first_step = StartPurchaseStep(self, store, model)
        BaseWizard.__init__(self, store, first_step, model, title=title,
                            edit_mode=edit_mode)

    def _get_title(self, model=None):
        if not model:
            return _('New Order')
        return _('Edit Order')

    def _create_model(self, store):
        supplier_id = sysparam.get_object_id('SUGGESTED_SUPPLIER')
        branch = api.get_current_branch(store)
        group = PaymentGroup(store=store)
        status = PurchaseOrder.ORDER_PENDING
        return PurchaseOrder(supplier_id=supplier_id,
                             responsible=api.get_current_user(store),
                             branch=branch,
                             status=status,
                             group=group,
                             store=store)

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
        self.retval = self.model

        if self.receiving_model:
            # Confirming the receiving will close the purchase
            self.receiving_model.confirm()

        self.close()

        if sysparam.get_bool('UPDATE_PRODUCTS_COST_ON_PURCHASE'):
            self.model.update_products_cost()


def test():  # pragma nocover
    creator = api.prepare_test()
    retval = run_dialog(PurchaseWizard, None, creator.store)
    creator.store.confirm(retval)


if __name__ == '__main__':  # pragma nocover
    test()
