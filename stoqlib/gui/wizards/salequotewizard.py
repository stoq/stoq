# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
""" Sale quote wizard"""

from decimal import Decimal

from dateutil.relativedelta import relativedelta
import gtk
from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.python import Settable
from kiwi.ui.objectlist import Column
from storm.expr import And, Eq, Or

from stoqlib.api import api
from stoqlib.database.expr import Field
from stoqlib.domain.event import Event
from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.person import ClientCategory, Client, SalesPerson
from stoqlib.domain.product import ProductStockItem
from stoqlib.domain.sale import Sale, SaleItem, SaleComment
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.views import SellableFullStockView
from stoqlib.enums import ChangeSalespersonPolicy
from stoqlib.exceptions import TaxError
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.decorators import public
from stoqlib.lib.formatters import (format_quantity, format_sellable_description,
                                    get_formatted_percentage)
from stoqlib.lib.message import yesno, warning
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.pluginmanager import get_plugin_manager
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.editors.discounteditor import DiscountEditor
from stoqlib.gui.editors.fiscaleditor import CfopEditor
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.events import SaleQuoteWizardFinishEvent, SaleQuoteFinishPrintEvent
from stoqlib.gui.editors.saleeditor import SaleQuoteItemEditor
from stoqlib.gui.slaves.paymentslave import (register_payment_slaves,
                                             MultipleMethodSlave)
from stoqlib.gui.utils.printing import print_report
from stoqlib.gui.widgets.calculator import CalculatorPopup
from stoqlib.gui.widgets.queryentry import ClientEntryGadget
from stoqlib.gui.wizards.abstractwizard import SellableItemStep
from stoqlib.reporting.sale import SaleOrderReport

_ = stoqlib_gettext


#
# Wizard Steps
#


class StartSaleQuoteStep(WizardEditorStep):
    gladefile = 'SalesPersonQuoteWizardStep'
    model_type = Sale
    proxy_widgets = ['client', 'salesperson', 'expire_date',
                     'operation_nature', 'client_category']
    cfop_widgets = ('cfop', )

    def _setup_widgets(self):
        # Salesperson combo
        salespersons = SalesPerson.get_active_salespersons(self.store)
        self.salesperson.prefill(salespersons)

        change_salesperson = sysparam.get_int('ACCEPT_CHANGE_SALESPERSON')
        if change_salesperson == ChangeSalespersonPolicy.ALLOW:
            self.salesperson.grab_focus()
        elif change_salesperson == ChangeSalespersonPolicy.DISALLOW:
            self.salesperson.set_sensitive(False)
        elif change_salesperson == ChangeSalespersonPolicy.FORCE_CHOOSE:
            self.model.salesperson = None
            self.salesperson.grab_focus()
        else:
            raise AssertionError

        # CFOP combo
        if sysparam.get_bool('ASK_SALES_CFOP'):
            cfops = CfopData.get_for_sale(self.store)
            self.cfop.prefill(api.for_combo(cfops))
        else:
            self.cfop_lbl.hide()
            self.cfop.hide()
            self.create_cfop.hide()

        self._fill_clients_category_combo()
        self._setup_clients_widget()

        self._client_credit_set_visible(bool(self.client.read()))

    def _client_credit_set_visible(self, visible):
        if visible and self.model.client:
            self.client_credit.set_text(
                self.model.client.credit_account_balance.format(precision=2)
            )
        self.client_credit.set_visible(visible)
        self.client_credit_lbl.set_visible(visible)

    def _setup_clients_widget(self):
        self.client_gadget = ClientEntryGadget(
            entry=self.client,
            store=self.store,
            initial_value=self.model.client,
            parent=self.wizard)

    def _fill_clients_category_combo(self):
        categories = self.store.find(ClientCategory).order_by(ClientCategory.name)
        self.client_category.prefill(api.for_combo(categories, empty=''))

        if categories.is_empty():
            self.client_category.hide()
            self.client_category_lbl.hide()

    def post_init(self):
        self.toogle_client_details()
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def next_step(self):
        return SaleQuoteItemStep(self.wizard, self, self.store, self.model)

    def has_previous_step(self):
        return False

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    StartSaleQuoteStep.proxy_widgets)
        if sysparam.get_bool('ASK_SALES_CFOP'):
            self.add_proxy(self.model, StartSaleQuoteStep.cfop_widgets)

        expire_delta = sysparam.get_int('EXPIRATION_SALE_QUOTE_DATE')
        if expire_delta > 0 and not self.model.expire_date:
            # Only set the expire date if id doesn't already have one.
            self.expire_date.update(localtoday() +
                                    relativedelta(days=expire_delta))

    def toogle_client_details(self):
        client = self.model.client

        if client and client.status != Client.STATUS_SOLVENT:
            self.client_gadget.update_edit_button(
                gtk.STOCK_DIALOG_WARNING, _("The client is not solvent"))

    #
    #   Callbacks
    #

    def after_client__content_changed(self, widget):
        # During the setup of client_gadget, the client is changed. So this method is
        # called before the client_gadget be completely created.
        # Check if the client_gadget was created to continue setting other widgets.
        if not hasattr(self, 'client_gadget'):
            return

        client = self.model.client
        self.toogle_client_details()
        self._client_credit_set_visible(bool(client))
        if not client:
            return
        self.client_category.select(client.category)

    def on_expire_date__validate(self, widget, value):
        # open_date has a seconds precision, so that why we are rounding it to
        # date here.
        if value.date() < self.model.open_date.date():
            msg = _(u"The expire date must be after the sale open date")
            return ValidationError(msg)

    def on_notes_button__clicked(self, *args):
        self.store.savepoint('before_run_notes_editor')

        model = self.model.comments.first()
        if not model:
            model = SaleComment(store=self.store, sale=self.model,
                                author=api.get_current_user(self.store))
        rv = run_dialog(NoteEditor, self.wizard, self.store, model, 'comment',
                        title=_('Additional Information'))
        if not rv:
            self.store.rollback_to_savepoint('before_run_notes_editor')

    def on_create_cfop__clicked(self, widget):
        self.store.savepoint('before_run_editor_cfop')
        cfop = run_dialog(CfopEditor, self.wizard, self.store, None)
        if cfop:
            self.cfop.append_item(cfop.get_description(), cfop)
            self.cfop.select_item_by_data(cfop)
        else:
            self.store.rollback_to_savepoint('before_run_editor_cfop')


class SaleQuoteItemStep(SellableItemStep):
    """ Wizard step for purchase order's items selection """
    change_remove_btn_sensitive = True
    model_type = Sale
    item_table = SaleItem
    summary_label_text = "<b>%s</b>" % api.escape(_('Total Ordered:'))
    sellable = None
    sellable_view = SellableFullStockView
    item_editor = SaleQuoteItemEditor
    validate_price = True
    value_column = 'price'
    calculator_mode = CalculatorPopup.MODE_SUB

    #
    # SellableItemStep
    #

    def get_sellable_view_query(self):
        branch = api.get_current_branch(self.store)
        branch_query = Or(Field('_stock_summary', 'branch_id') == branch.id,
                          Eq(Field('_stock_summary', 'branch_id'), None))
        query = And(branch_query,
                    Sellable.get_available_sellables_query(self.store))
        return self.sellable_view, query

    def setup_slaves(self):
        SellableItemStep.setup_slaves(self)
        self.hide_add_button()
        self.cost_label.set_label(_('Price:'))
        self.cost.set_editable(True)

        self.discount_btn = self.slave.add_extra_button(label=_("Apply discount"))
        self.discount_btn.set_sensitive(bool(len(self.slave.klist)))
        self.slave.klist.connect('has-rows', self._on_klist__has_rows)
        self.slave.klist.connect('selection-changed',
                                 self._on_klist__selection_changed)

    def update_total(self):
        SellableItemStep.update_total(self)
        quantities = {}
        missing = {}
        lead_time = 0
        for i in self.slave.klist:
            sellable = i.sellable
            if sellable.service or not sellable.product.manage_stock:
                continue

            quantities.setdefault(sellable, 0)
            quantities[sellable] += i.quantity
            # This was already removed from stock, so we need to ignore it.
            if hasattr(i, 'quantity_decreased'):
                quantities[sellable] -= i.quantity_decreased

            if quantities[sellable] > i._stock_quantity:
                _lead_time = sellable.product.get_max_lead_time(
                    quantities[sellable], self.model.branch)
                max_lead_time = max(lead_time, _lead_time)
                missing[sellable] = Settable(
                    description=sellable.get_description(),
                    stock=i._stock_quantity,
                    ordered=quantities[sellable],
                    lead_time=_lead_time,
                )
        self.missing = missing

        if missing:
            msg = _('Not enough stock. '
                    'Estimated time to obtain missing items: %d days.') % max_lead_time
            self.slave.set_message(
                '<b>%s</b>' % (api.escape(msg)), self._show_missing_details)
        else:
            self.slave.clear_message()

    def add_sellable(self, sellable, parent=None):
        price = sellable.get_price_for_category(self.model.client_category)
        new_price = self.cost.read()

        # Percentage of discount
        discount = 100 - new_price * 100 / price

        if discount > 0 and self.manager:
            Event.log_sale_item_discount(
                store=self.store,
                sale_number=self.model.identifier,
                user_name=self.manager.username,
                discount_value=discount,
                product=sellable.description,
                original_price=price,
                new_price=new_price)

        SellableItemStep.add_sellable(self, sellable, parent=parent)
        self.update_total()

    def get_order_item(self, sellable, price, quantity, batch=None, parent=None):
        """
        :param sellable: the |sellable|
        :param price: the price the sellable is being sold
        :param quantity: the quantity for that is being sold
        :param batch: the |storable_batch| if exists
        :param parent: |sale_item|'s parent_item if exists
        """
        if parent:
            component = self.get_component(parent, sellable)
            quantity = parent.quantity * component.quantity
            price = component.price
        else:
            if sellable.product and sellable.product.is_package:
                # XXX Sending package products with price 0 (zero)
                price = Decimal(0)

        item = self.model.add_sellable(sellable, quantity=quantity,
                                       price=price,
                                       batch=batch, parent=parent)
        # Save temporarily the stock quantity and lead_time so we can show a
        # warning if there is not enough quantity for the sale.
        if not parent:
            item._stock_quantity = self.proxy.model.stock_quantity
            # When the product does not have stock control. Use the
            # sellable cost information
            item.average_cost = sellable.cost
        else:
            storable = sellable.product_storable
            stock_item = self.store.find(ProductStockItem,
                                         storable=storable,
                                         batch=batch,
                                         branch=self.model.branch).one()
            # FIXME: Currently uses the cost of the supplier or cost sellable.
            # Implement batch control for the cost of the lot not the product.
            if stock_item is not None:
                item.average_cost = stock_item.stock_cost

            stock = storable.get_balance_for_branch(self.model.branch)
            item._stock_quantity = stock

        item.update_tax_values()

        return item

    def get_saved_items(self):
        items = self.model.get_items()
        for i in items:
            product = i.sellable.product
            if not product:
                yield i
                continue
            storable = product.storable
            if not storable:
                yield i
                continue
            stock = storable.get_balance_for_branch(self.model.branch)
            i._stock_quantity = stock
            yield i

    def get_columns(self):
        columns = [
            Column('sellable.code', title=_('Code'),
                   data_type=str, visible=False),
            Column('sellable.barcode', title=_('Barcode'),
                   data_type=str, visible=False),
            Column('sellable.description', title=_('Description'),
                   data_type=str, expand=True, searchable=True,
                   format_func=self._format_description, format_func_data=True),
            Column('manufacturer', title=_('Manufacturer'),
                   data_type=str, visible=False),
            Column('model', title=_('Model'),
                   data_type=str, visible=False),
            Column('sellable.category_description', title=_('Category'),
                   data_type=str, expand=True, searchable=True),
            Column('quantity', title=_('Quantity'), data_type=Decimal,
                   format_func=format_quantity),
            Column('sellable.unit_description', title=_('Unit'),
                   data_type=str)]

        if sysparam.get_bool('SHOW_COST_COLUMN_IN_SALES'):
            columns.append(Column('sellable.cost', title=_('Cost'), data_type=currency,
                                  width=80))

        manager = get_plugin_manager()
        show_invoice_columns = manager.is_active('nfe') and not manager.is_active('ecf')
        columns.extend([
            Column('nfe_cfop_code', title=_('CFOP'), data_type=str,
                   visible=show_invoice_columns),
            Column('icms_info.v_bc', title=_('ICMS BC'), data_type=currency,
                   visible=show_invoice_columns),
            Column('icms_info.v_icms', title=_('ICMS'), data_type=currency,
                   visible=show_invoice_columns),
            Column('ipi_info.v_ipi', title=_('IPI'), data_type=currency,
                   visible=show_invoice_columns),
            Column('base_price', title=_('Original Price'), data_type=currency),
            Column('price', title=_('Sale Price'), data_type=currency),
            Column('sale_discount', title=_('Discount'), data_type=Decimal,
                   format_func=get_formatted_percentage),
            Column('total', title=_('Total'), data_type=currency)])

        return columns

    def sellable_selected(self, sellable, batch=None):
        # We may receive a batch if the user typed a batch number instead of a
        # product code, but we pass batch=None here since the user must select
        # the batch when confirming a sale.
        SellableItemStep.sellable_selected(self, sellable, batch=None)
        if sellable:
            price = sellable.get_price_for_category(
                self.model.client_category)
            self.cost.update(price)

    def can_add_sellable(self, sellable):
        try:
            sellable.check_taxes_validity()
        except TaxError as strerr:
            # If the sellable icms taxes are not valid, we cannot sell it.
            warning(str(strerr))
            return False

        return True

    def get_extra_discount(self, sellable):
        if not api.sysparam.get_bool('REUTILIZE_DISCOUNT'):
            return None
        return self.model.get_available_discount_for_items(user=self.manager)

    #
    # WizardStep hooks
    #

    def has_next_step(self):
        return False

    #
    # Private API
    #

    def _format_description(self, item, data):
        return format_sellable_description(item.sellable, item.batch)

    def _show_missing_details(self, button):
        from stoqlib.gui.base.lists import SimpleListDialog
        columns = [Column('description', title=_(u'Product'),
                          data_type=str, expand=True),
                   Column('ordered', title=_(u'Ordered'),
                          data_type=int),
                   Column('stock', title=_(u'Stock'),
                          data_type=int),
                   Column('lead_time', title=_(u'Lead Time'),
                          data_type=int),
                   ]

        class MyList(SimpleListDialog):
            size = (500, 200)

        run_dialog(MyList, self.get_toplevel().get_toplevel(), columns,
                   list(self.missing.values()), title=_("Missing products"))

    #
    # Callbacks
    #

    def on_slave__on_edit_item(self, slave, item):
        product = item.sellable.product
        if not product or not product.storable:
            return
        # The item was edited, and there is the chance that the quantity
        # reserved changed. Update the object so that we can display the correcy
        # missing message
        stock = product.storable.get_balance_for_branch(self.model.branch)
        item._stock_quantity = stock

    def _on_klist__has_rows(self, klist, has_rows):
        self.discount_btn.set_sensitive(has_rows)

    def _on_klist__selection_changed(self, klist, selected):
        if self.change_remove_btn_sensitive:
            can_remove = all(item.parent_item is None for item in selected)
            self.slave.delete_button.set_sensitive(can_remove)

    def on_discount_btn__clicked(self, button):
        rv = run_dialog(DiscountEditor, self.parent, self.store, self.model,
                        user=self.manager or api.get_current_user(self.store))
        if not rv:
            return

        for item in self.slave.klist:
            self.slave.klist.update(item)

        self.update_total()


class SaleQuotePaymentStep(WizardEditorStep):
    """A step for creating payments for a |sale|

    All this step does is to attach
    :class:`stoqlib.gui.slaves.paymentslave.MultipleMethodSlave`, so
    see it for more information
    """

    gladefile = 'HolderTemplate'
    model_type = Sale

    #
    #  WizardEditorStep
    #

    def post_init(self):
        self.register_validate_function(self._validation_func)
        self.force_validation()

    def setup_slaves(self):
        register_payment_slaves()
        self.slave = MultipleMethodSlave(
            wizard=self.wizard,
            parent=self,
            store=self.store,
            order=self.model,
            payment_method=None,
            finish_on_total=False,
            allow_remove_paid=False,
            require_total_value=False)
        self.slave.enable_remove()
        self.attach_slave('place_holder', self.slave)

    def has_next_step(self):
        return False

    #
    #  Callbacks
    #

    def _validation_func(self, value):
        can_finish = value and self.slave.can_confirm()
        self.wizard.refresh_next(can_finish)


#
# Main wizard
#


class SaleQuoteWizard(BaseWizard):
    size = (775, 400)
    help_section = 'sale-quote'
    need_cancel_confirmation = True

    def __init__(self, store, model=None):
        title = self.get_title(model)
        model = model or self._create_model(store)

        if not model.can_edit():
            raise ValueError('Invalid sale status. It should '
                             'be STATUS_QUOTE or STATUS_ORDERED')

        first_step = self.get_first_step(store, model)
        BaseWizard.__init__(self, store, first_step, model, title=title,
                            edit_mode=False)

    @public(since='1.8.0')
    def get_first_step(self, store, model):
        """Returns the first step of this wizard.

        Subclasses can override this if they want to change the first step,
        without overriding __init__.
        """
        return StartSaleQuoteStep(store, self, model)

    def get_title(self, model=None):
        if not model:
            return _('New Sale Quote')
        return _('Edit Sale Quote')

    def _create_model(self, store):
        user = api.get_current_user(store)
        salesperson = user.person.sales_person

        return Sale(coupon_id=None,
                    status=Sale.STATUS_QUOTE,
                    salesperson=salesperson,
                    branch=api.get_current_branch(store),
                    group=PaymentGroup(store=store),
                    cfop_id=sysparam.get_object_id('DEFAULT_SALES_CFOP'),
                    operation_nature=sysparam.get_string('DEFAULT_OPERATION_NATURE'),
                    store=store)

    @public(since='1.8.0')
    def print_quote_details(self, quote, payments_created=False):
        already_printed = SaleQuoteFinishPrintEvent.emit(self.model)
        if already_printed is not None:
            return
        msg_list = []
        if not quote.group.payments.is_empty():
            msg_list.append(
                _('The created payments can be found in the Accounts '
                  'Receivable application and you can set them as paid '
                  'there at any time.'))
        msg_list.append(_('Would you like to print the quote details now?'))

        # We can only print the details if the quote was confirmed.
        if yesno('\n\n'.join(msg_list), gtk.RESPONSE_YES,
                 _("Print quote details"), _("Don't print")):
            print_report(SaleOrderReport, self.model)

    #
    # WizardStep hooks
    #

    def finish(self):
        # Confirm the payments created on SaleQuotePaymentStep
        # They were created as preview on the step
        if self.model.client:
            self.model.group.payer = self.model.client.person
        self.model.group.confirm()

        self.retval = self.model

        # Commit before printing to avoid losing data if something breaks
        self.store.confirm(self.model)
        SaleQuoteWizardFinishEvent.emit(self.model)
        self.close()
        self.print_quote_details(self.model)
