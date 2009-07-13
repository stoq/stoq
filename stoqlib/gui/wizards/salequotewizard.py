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
## Author(s):   Ronaldo Maia                <romaia@async.com.br>
##
##
""" Sale quote wizard"""

from decimal import Decimal
import datetime

from kiwi.datatypes import currency, ValidationError
from kiwi.ui.widgets.list import Column
from kiwi.python import Settable

from stoqlib.database.runtime import (get_current_branch, get_current_user,
                                      new_transaction, finish_transaction)
from stoqlib.domain.interfaces import ISalesPerson
from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.operation import register_payment_operations
from stoqlib.domain.person import Person, ClientView
from stoqlib.domain.sale import Sale, SaleItem
from stoqlib.domain.sellable import Sellable
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.validators import format_quantity
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.editors.fiscaleditor import CfopEditor
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.editors.personeditor import ClientEditor
from stoqlib.gui.editors.saleeditor import SaleQuoteItemEditor
from stoqlib.gui.wizards.abstractwizard import SellableItemStep
from stoqlib.gui.wizards.personwizard import run_person_role_dialog

_ = stoqlib_gettext


#
# Wizard Steps
#


class StartSaleQuoteStep(WizardEditorStep):
    gladefile = 'SalesPersonStep'
    model_type = Sale
    proxy_widgets = ('client', 'salesperson', 'expire_date')
    cfop_widgets = ('cfop',)

    def _setup_widgets(self):
        # Hide total and subtotal
        self.table1.hide()
        self.hbox4.hide()

        # Salesperson combo
        salespersons = Person.iselect(ISalesPerson, connection=self.conn)
        items = [(s.person.name, s) for s in salespersons]
        self.salesperson.prefill(items)
        if not sysparam(self.conn).ACCEPT_CHANGE_SALESPERSON:
            self.salesperson.set_sensitive(False)
        else:
            self.salesperson.grab_focus()

        # Clients combo
        clients = ClientView.get_active_clients(self.conn)
        max_results = sysparam(self.conn).MAX_SEARCH_RESULTS
        clients = clients[:max_results]
        items = [(c.name, c.client) for c in clients]
        self.client.prefill(sorted(items))

        # CFOP combo
        if sysparam(self.conn).ASK_SALES_CFOP:
            cfops = [(cfop.get_description(), cfop)
                        for cfop in CfopData.select(connection=self.conn)]
            self.cfop.prefill(cfops)
        else:
            self.cfop_lbl.hide()
            self.cfop.hide
            self.create_cfop.hide()

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def next_step(self):
        return SaleQuoteItemStep(self.wizard, self, self.conn, self.model)

    def has_previous_step(self):
        return False

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    StartSaleQuoteStep.proxy_widgets)
        if sysparam(self.conn).ASK_SALES_CFOP:
            self.add_proxy(self.model, StartSaleQuoteStep.cfop_widgets)

    #
    #   Callbacks
    #

    def on_create_client__clicked(self, button):
        trans = new_transaction()
        client = run_person_role_dialog(ClientEditor, self, trans, None)
        if not finish_transaction(trans, client):
            return
        if len(self.client) == 0:
            self._fill_clients_combo()
        else:
            self.client.append_item(client.person.name, client)
        self.client.select(client)

    def on_expire_date__validate(self, widget, value):
        if value < datetime.date.today():
            msg = _(u"The expire date must be set to today or a future date.")
            return ValidationError(msg)

    def on_notes_button__clicked(self, *args):
        run_dialog(NoteEditor, self.wizard, self.conn, self.model, 'notes',
                   title=_("Additional Information"))

    def on_create_cfop__clicked(self, widget):
        cfop = run_dialog(CfopEditor, self, self.conn, None)
        if cfop:
            self.cfop.append_item(cfop.get_description(), cfop)
            self.cfop.select_item_by_data(cfop)


class SaleQuoteItemStep(SellableItemStep):
    """ Wizard step for purchase order's items selection """
    model_type = Sale
    item_table = SaleItem
    summary_label_text = "<b>%s</b>" % _('Total Ordered:')
    sellable = None

    #
    # Helper methods
    #

    def setup_sellable_entry(self):
        sellables = Sellable.get_unblocked_sellables(self.conn, storable=True)
        max_results = sysparam(self.conn).MAX_SEARCH_RESULTS
        self.sellable.prefill(
            [(sellable.get_description(full_description=True), sellable)
             for sellable in sellables[:max_results]])

        self.cost_label.set_label('Price:')
        self.cost.set_property('model-attribute', 'price')

    def setup_slaves(self):
        SellableItemStep.setup_slaves(self)
        self.hide_add_button()
        self.cost.set_editable(True)

    #
    # SellableItemStep virtual methods
    #

    def get_order_item(self, sellable, price, quantity):
        return self.model.add_sellable(sellable, quantity, self.cost.read())

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
            Column('price', title=_('Price'), data_type=currency, width=90),
            Column('base_price', title=_('Base Price'), data_type=currency, width=90),
            Column('total', title=_('Total'), data_type=currency, width=100),
            ]

    def sellable_selected(self, sellable):
        if sellable:
            price = sellable.price
            quantity = Decimal(1)
        else:
            price = None
            quantity = None

        model = Settable(quantity=quantity,
                         price=price,
                         sellable=sellable)

        self.proxy.set_model(model)

        has_sellable = bool(sellable)
        self.add_sellable_button.set_sensitive(has_sellable)
        self.quantity.set_sensitive(has_sellable)
        self.cost.set_sensitive(has_sellable)

    #
    # WizardStep hooks
    #

    def post_init(self):
        SellableItemStep.post_init(self)
        self.slave.set_editor(SaleQuoteItemEditor)
        self._refresh_next()
        self.product_button.hide()

    def has_next_step(self):
        return False

    #
    # Callbacks
    #

    def on_cost__validate(self, widget, value):
        if value <= Decimal(0):
            return ValidationError(_(u"The price must be greater than zero."))

        sellable = self.sellable.get_selected_data()
        info = sellable.base_sellable_info
        if value < info.price - (info.price * info.max_discount/100):
            return ValidationError(
                        _(u"Max discount for this product is %.2f%%") %
                            info.max_discount)


#
# Main wizard
#


class SaleQuoteWizard(BaseWizard):
    size = (775, 400)

    def __init__(self, conn, model=None):
        title = self._get_title(model)
        model = model or self._create_model(conn)

        if model.status != Sale.STATUS_QUOTE:
            raise ValueError('Invalid sale status. It should '
                             'be STATUS_QUOTE')

        register_payment_operations()
        first_step = StartSaleQuoteStep(conn, self, model)
        BaseWizard.__init__(self, conn, first_step, model, title=title,
                            edit_mode=False)

    def _get_title(self, model=None):
        if not model:
            return _('New Sale Quote')
        return _('Edit Sale Quote')

    def _create_model(self, conn):
        user = get_current_user(conn)
        salesperson = ISalesPerson(user.person)

        return Sale(coupon_id=None,
                    status=Sale.STATUS_QUOTE,
                    salesperson=salesperson,
                    branch=get_current_branch(conn),
                    group=PaymentGroup(connection=conn),
                    cfop=sysparam(conn).DEFAULT_SALES_CFOP,
                    connection=conn)

    #
    # WizardStep hooks
    #

    def finish(self):
        if not self.model.get_valid():
            self.model.set_valid()
        self.retval = self.model

        self.close()
