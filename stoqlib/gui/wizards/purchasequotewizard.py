# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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
## Author(s):       George Kussumoto        <george@async.com.br>
##
""" Purchase quote wizard definition """

import datetime

from kiwi.datatypes import currency, ValidationError
from kiwi.python import Settable
from kiwi.ui.widgets.list import Column

from stoqlib.database.runtime import get_current_branch
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.message import info
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.validators import format_quantity
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.lists import SimpleListDialog
from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.printing import print_report
from stoqlib.gui.wizards.purchasewizard import PurchaseItemStep
from stoqlib.domain.person import Person
from stoqlib.domain.purchase import (PurchaseOrder, PurchaseItem, QuoteGroup,
                                     Quotation)
from stoqlib.domain.interfaces import IBranch, IProduct
from stoqlib.reporting.purchase import PurchaseQuoteReport

_ = stoqlib_gettext


#
# Wizard Steps
#


class StartQuoteStep(WizardEditorStep):
    gladefile = 'StartQuoteStep'
    model_type = PurchaseOrder
    proxy_widgets = ['open_date', 'quote_deadline', 'branch_combo',]

    def __init__(self, wizard, previous, conn, model):
        WizardEditorStep.__init__(self, conn, wizard, model, previous)

    def _setup_widgets(self):
        quote_group = "%05d" % self.wizard.quote_group.id
        self.quote_group.set_text(quote_group)

        table = Person.getAdapterClass(IBranch)
        branches = table.get_active_branches(self.conn)
        items = [(s.person.name, s) for s in branches]
        self.branch_combo.prefill(sorted(items))

    #
    # WizardStep
    #

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def next_step(self):
        return QuoteItemsStep(self.wizard, self, self.conn, self.model)

    #
    # BaseEditorSlave
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model, StartQuoteStep.proxy_widgets)

    #
    # Kiwi Callbacks
    #

    def on_quote_deadline__validate(self, widget, date):
        if date <= datetime.date.today():
            return ValidationError(
                _("The quote deadline date must be set to a future date"))


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
                        data_type=str, sorted=True, expand=True),
                Column('products_per_supplier', title=_('Supplied/Total'),
                        data_type=str)]

    def _update_widgets(self):
        selected = self.quoting_list.get_selected()
        self.print_button.set_sensitive(selected is not None)
        self.view_products_button.set_sensitive(selected is not None)

    def _populate_quoting_list(self):
        # populate the quoting list by finding the suppliers based on the
        # products list
        quotes = {}
        total_items = 0
        # O(n*n)
        for item in self.model.get_items():
            total_items += 1
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
            total_supplier_items = len(items)
            per_supplier = _(u"%s/%s") % (total_supplier_items, total_items)
            self.quoting_list.append(Settable(supplier=supplier,
                                     items=items,
                                     products_per_supplier=per_supplier,
                                     selected=True))

    def _print_quote(self):
        selected = self.quoting_list.get_selected()
        self.model.supplier = selected.supplier
        print_report(PurchaseQuoteReport, self.model)

    def _generate_quote(self, selected):
        # we use our model as a template to create new quotes
        quote = self.model.clone()
        include_all = self.include_all_products.get_active()
        for item in self.model.get_items():
            if item.sellable in selected.items or include_all:
                quote_item = item.clone()
                quote_item.order = quote

        quote.supplier = selected.supplier
        if not quote.get_valid():
            quote.set_valid()

        self.wizard.quote_group.add_item(quote)

        self.conn.commit()

    def _get_product_columns(self):
        return [Column('description', title=_(u'Product'), data_type=str,
                       expand=True)]

    def _show_products(self):
        selected = self.quoting_list.get_selected()
        columns = self._get_product_columns()
        title = _(u'Products supplied by %s' % selected.supplier.person.name)
        run_dialog(SimpleListDialog, self, columns, selected.items,
                   title=title)

    def _show_missing_products(self):
        missing_products = set([i.sellable for i in self.model.get_items()])
        for quote in self.quoting_list:
            if quote.selected:
                missing_products = missing_products.difference(quote.items)
            if len(missing_products) == 0:
                break

        columns = self._get_product_columns()
        run_dialog(SimpleListDialog, self, columns, missing_products,
                   title=_(u'Missing Products'))

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

    def on_missing_products_button__clicked(self, widget):
        self._show_missing_products()

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


class QuotePurchaseWizard(BaseWizard):
    size = (775, 400)

    def __init__(self, conn, model=None):
        title = self._get_title(model)
        self.edit = model is not None
        self.quote_group = self._get_or_create_quote_group(model, conn)
        model = model or self._create_model(conn)
        if model.status != PurchaseOrder.ORDER_QUOTING:
            raise ValueError('Invalid order status. It should '
                             'be ORDER_QUOTING')

        first_step = StartQuoteStep(self, None, conn, model)
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

    def _get_or_create_quote_group(self, order, conn):
        if order is not None:
            quotation = Quotation.selectOneBy(purchase=order, connection=conn)
            return quotation.group
        else:
            return QuoteGroup(connection=conn)

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
