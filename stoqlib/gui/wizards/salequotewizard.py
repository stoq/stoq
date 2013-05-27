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
import operator

import gtk
from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.ui.widgets.list import Column
from kiwi.python import Settable
from storm.expr import And, Eq, Or

from stoqlib.api import api
from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.person import (ClientCategory, SalesPerson, Client,
                                   ClientView)
from stoqlib.domain.product import ProductStockItem
from stoqlib.domain.sale import Sale, SaleItem
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.views import SellableFullStockView
from stoqlib.exceptions import TaxError
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.decorators import public
from stoqlib.lib.message import yesno, warning
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.formatters import format_quantity
from stoqlib.lib.translation import locale_sorted
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
from stoqlib.gui.editors.fiscaleditor import CfopEditor
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.editors.personeditor import ClientEditor
from stoqlib.gui.editors.saleeditor import SaleQuoteItemEditor
from stoqlib.gui.printing import print_report
from stoqlib.gui.slaves.paymentslave import (register_payment_slaves,
                                             MultipleMethodSlave)
from stoqlib.gui.wizards.abstractwizard import SellableItemStep
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.reporting.sale import SaleOrderReport

_ = stoqlib_gettext


#
# Wizard Steps
#


class StartSaleQuoteStep(WizardEditorStep):
    gladefile = 'SalesPersonStep'
    model_type = Sale
    proxy_widgets = ('client', 'salesperson', 'expire_date',
                     'operation_nature', 'client_category')
    cfop_widgets = ('cfop', )

    def _setup_widgets(self):
        # Hide total and subtotal
        self.table1.hide()
        self.hbox4.hide()
        # Hide invoice number details
        self.invoice_number_label.hide()
        self.invoice_number.hide()

        # Hide cost center combobox
        self.cost_center_lbl.hide()
        self.cost_center.hide()

        # Salesperson combo
        salespersons = self.store.find(SalesPerson)
        self.salesperson.prefill(api.for_person_combo(salespersons))
        if not sysparam(self.store).ACCEPT_CHANGE_SALESPERSON:
            self.salesperson.set_sensitive(False)
        else:
            self.salesperson.grab_focus()

        # CFOP combo
        if sysparam(self.store).ASK_SALES_CFOP:
            cfops = self.store.find(CfopData)
            self.cfop.prefill(api.for_combo(cfops))
        else:
            self.cfop_lbl.hide()
            self.cfop.hide()
            self.create_cfop.hide()

        self.transporter_lbl.hide()
        self.transporter.hide()
        self.create_transporter.hide()

        self._fill_clients_combo()
        self._fill_clients_category_combo()

    def _fill_clients_combo(self):
        # FIXME: This should not be using a normal ProxyComboEntry,
        #        we need a specialized widget that does the searching
        #        on demand.

        # This is to keep the clients in cache
        clients_cache = list(Client.get_active_clients(self.store))
        clients_cache  # pyflakes

        # We are using ClientView here to show the fancy name as well
        clients = ClientView.get_active_clients(self.store)
        items = [(c.get_description(), c.client) for c in clients]
        items = locale_sorted(items, key=operator.itemgetter(0))
        self.client.prefill(items)

        # TODO: Implement a has_items() in kiwi
        self.client.set_sensitive(len(self.client.get_model()))

    def _fill_clients_category_combo(self):
        categories = self.store.find(ClientCategory).order_by(ClientCategory.name)
        self.client_category.prefill(api.for_combo(categories, empty=''))

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
        if sysparam(self.store).ASK_SALES_CFOP:
            self.add_proxy(self.model, StartSaleQuoteStep.cfop_widgets)

    def toogle_client_details(self):
        client = self.client.read()
        self.client_details.set_sensitive(bool(client))

    #
    #   Callbacks
    #

    def on_create_client__clicked(self, button):
        store = api.new_store()
        client = run_person_role_dialog(ClientEditor, self.wizard, store, None)
        retval = store.confirm(client)
        client = self.store.fetch(client)
        store.close()
        if not retval:
            return
        self._fill_clients_combo()
        self.client.select(client)

    def on_client__changed(self, widget):
        self.toogle_client_details()
        client = self.client.get_selected()
        if not client:
            return
        self.client_category.select(client.category)

    def on_client_details__clicked(self, button):
        client = self.model.client
        run_dialog(ClientDetailsDialog, self.wizard, self.store, client)

    def on_expire_date__validate(self, widget, value):
        if value < localtoday().date():
            msg = _(u"The expire date must be set to today or a future date.")
            return ValidationError(msg)

    def on_notes_button__clicked(self, *args):
        run_dialog(NoteEditor, self.wizard, self.store, self.model, 'notes',
                   title=_("Additional Information"))

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
    model_type = Sale
    item_table = SaleItem
    summary_label_text = "<b>%s</b>" % api.escape(_('Total Ordered:'))
    sellable = None
    sellable_view = SellableFullStockView
    item_editor = SaleQuoteItemEditor

    def get_sellable_view_query(self):
        branch = api.get_current_branch(self.store)
        branch_query = Or(ProductStockItem.branch_id == branch.id,
                          Eq(ProductStockItem.branch_id, None))
        query = And(branch_query,
                    Sellable.get_available_sellables_query(self.store))
        return self.sellable_view, query

    def setup_slaves(self):
        SellableItemStep.setup_slaves(self)
        self.hide_add_button()
        self.cost_label.set_label('Price:')
        self.cost.set_editable(True)

    #
    # SellableItemStep virtual methods
    #

    def _update_total(self):
        SellableItemStep._update_total(self)
        quantities = {}
        missing = {}
        lead_time = 0
        for i in self.slave.klist:
            sellable = i.sellable
            if sellable.service:
                continue

            quantities.setdefault(sellable, 0)
            quantities[sellable] += i.quantity
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

    def get_order_item(self, sellable, price, quantity):
        retval = self._validate_sellable_price(price)
        if retval is None:
            item = self.model.add_sellable(sellable, quantity, price)
            # Save temporarily the stock quantity and lead_time so we can show a
            # warning if there is not enough quantity for the sale.
            item._stock_quantity = self.proxy.model.stock_quantity
            return item

    def get_saved_items(self):
        items = self.model.get_items()
        for i in items:
            product = i.sellable.product
            if not product:
                continue
            storable = product.storable
            if not storable:
                continue
            stock = storable.get_balance_for_branch(self.model.branch)
            i._stock_quantity = stock

        return list(items)

    def get_columns(self):
        columns = [
            Column('sellable.code', title=_('Code'),
                   data_type=str, visible=False),
            Column('sellable.barcode', title=_('Barcode'),
                   data_type=str, visible=False),
            Column('sellable.description', title=_('Description'),
                   data_type=str, expand=True, searchable=True),
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

        if sysparam(self.store).SHOW_COST_COLUMN_IN_SALES:
            columns.append(Column('sellable.cost', title=_('Cost'), data_type=currency,
                                  width=80))

        columns.extend([
            Column('price', title=_('Price'), data_type=currency),
            Column('nfe_cfop_code', title=_('CFOP'), data_type=str),
            Column('icms_info.v_bc', title=_('ICMS BC'), data_type=currency),
            Column('icms_info.v_icms', title=_('ICMS'), data_type=currency),
            Column('ipi_info.v_ipi', title=_('IPI'), data_type=currency),
            Column('total', title=_('Total'), data_type=currency),
        ])

        return columns

    def sellable_selected(self, sellable):
        SellableItemStep.sellable_selected(self, sellable)
        if sellable:
            price = sellable.get_price_for_category(
                self.model.client_category)
            self.cost.set_text("%s" % price)
            self.proxy.update('cost')

    #
    #  SellableWizardStep Hooks
    #

    def can_add_sellable(self, sellable):
        try:
            sellable.check_taxes_validity()
        except TaxError as strerr:
            # If the sellable icms taxes are not valid, we cannot sell it.
            warning(strerr)
            return False

        return True

    #
    # WizardStep hooks
    #

    def next_step(self):
        return SaleQuotePaymentStep(self.store, self.wizard,
                                    model=self.model, previous=self)

    def has_next_step(self):
        return True

    #
    # Private API
    #

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

    def _validate_sellable_price(self, price):
        s = self.proxy.model.sellable
        category = self.model.client_category
        default_price = s.get_price_for_category(category)

        if price > default_price:
            if not sysparam(self.store).ALLOW_HIGHER_SALE_PRICE:
                return ValidationError(
                    _(u'The sell price cannot be greater than %s.') %
                    default_price)

        if not s.is_valid_price(price, category):
            info = None
            if category:
                info = s.get_category_price_info(category)
            if not info:
                info = s
            return ValidationError(
                _(u'Max discount for this product is %.2f%%') %
                info.max_discount)

    #
    # Callbacks
    #

    def on_cost__validate(self, widget, value):
        if not self.proxy.model.sellable:
            return

        if value <= Decimal(0):
            return ValidationError(_(u"The price must be greater than zero."))
        return self._validate_sellable_price(value)


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

    def __init__(self, store, model=None):
        title = self._get_title(model)
        model = model or self._create_model(store)

        if model.status != Sale.STATUS_QUOTE:
            raise ValueError('Invalid sale status. It should '
                             'be STATUS_QUOTE')

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

    def _get_title(self, model=None):
        if not model:
            return _('New Sale Quote')
        return _('Edit Sale Quote')

    def _create_model(self, store):
        user = api.get_current_user(store)
        salesperson = user.person.salesperson

        return Sale(coupon_id=None,
                    status=Sale.STATUS_QUOTE,
                    salesperson=salesperson,
                    branch=api.get_current_branch(store),
                    group=PaymentGroup(store=store),
                    cfop=sysparam(store).DEFAULT_SALES_CFOP,
                    operation_nature=sysparam(store).DEFAULT_OPERATION_NATURE,
                    store=store)

    def _print_quote_details(self, quote, payments_created=False):
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
        self.model.group.confirm()

        self.retval = self.model
        self.close()
        self._print_quote_details(self.model)
