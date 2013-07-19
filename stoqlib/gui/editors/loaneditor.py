# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
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
""" Loan editors """

import gtk
from kiwi.datatypes import ValidationError

from stoqlib.api import api
from stoqlib.domain.loan import LoanItem
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.credentialsdialog import CredentialsDialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.widgets.calculator import CalculatorPopup
from stoqlib.lib.defaults import MAX_INT
from stoqlib.lib.translation import stoqlib_gettext as _


class LoanItemEditor(BaseEditor):
    gladefile = 'SaleQuoteItemEditor'
    model_type = LoanItem
    model_name = _("Loan Item")
    proxy_widgets = ['price',
                     'quantity',
                     'sale_quantity',
                     'return_quantity',
                     'total']

    #: The manager is someone that can allow a bigger discount for a sale item.
    manager = None

    def __init__(self, store, model, expanded_edition=False):
        """An editor for a loan item. If the expaned_edition is True, the
        editor will enable the sale_quantity and return_quantity fields to be
        edited and will lock the quantity and price fields.
        :param store: a store.
        :param model: a loan item.
        :param expanded_edition: whether or not we should enable sale_quantity
                                 and return_quantity fields to be edited.
        """
        self.proxy = None
        self._expanded_edition = expanded_edition
        self._branch = model.loan.branch

        default_store = api.get_default_store()
        orig_model = default_store.find(LoanItem, id=model.id).one()
        if orig_model:
            self._original_sale_qty = orig_model.sale_quantity
            self._original_return_qty = orig_model.return_quantity
        else:
            self._original_sale_qty = 0
            self._original_return_qty = 0

        BaseEditor.__init__(self, store, model)

    def _setup_widgets(self):
        self._calc = CalculatorPopup(self.price,
                                     CalculatorPopup.MODE_SUB)

        self.sale.set_text(unicode(self.model.loan.identifier))
        self.description.set_text(self.model.sellable.get_description())
        for widget in [self.quantity, self.price,
                       self.sale_quantity, self.return_quantity]:
            widget.set_adjustment(gtk.Adjustment(lower=0, upper=MAX_INT,
                                                 step_incr=1))
        self._configure_expanded_edition()
        self.tabs.set_show_tabs(False)
        self.cfop.hide()
        self.cfop_label.hide()

    def _configure_expanded_edition(self):
        if self._expanded_edition:
            self.quantity.set_sensitive(False)
            self.price.set_sensitive(False)

        for widget in [self.sale_quantity_lbl, self.sale_quantity,
                       self.return_quantity_lbl, self.return_quantity]:
            if self._expanded_edition:
                widget.show()
            else:
                widget.hide()

    def _has_stock(self, quantity):
        storable = self.model.sellable.product_storable
        if storable is not None:
            available = storable.get_balance_for_branch(self._branch)
        else:
            available = 0
        return available >= quantity

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    #
    # Kiwi callbacks
    #

    def after_price__changed(self, widget):
        if self.proxy:
            self.proxy.update('total')

    def after_quantity__changed(self, widget):
        if self.proxy:
            self.proxy.update('total')

    def on_price__validate(self, widget, value):
        if value <= 0:
            return ValidationError(_(u'The price must be greater than zero.'))

        sellable = self.model.sellable
        category = self.model.loan.client and self.model.loan.client.category
        self.manager = self.manager or api.get_current_user(self.store)
        valid_data = sellable.is_valid_price(value, category, self.manager)
        if not valid_data['is_valid']:
            return ValidationError(
                _(u'Max discount for this product is %.2f%%.' %
                  valid_data['max_discount']))

    def on_price__icon_press(self, entry, icon_pos, event):
        if icon_pos != gtk.ENTRY_ICON_PRIMARY:
            return

        # Ask for the credentials of a different user that can possibly allow a
        # bigger discount.
        self.manager = run_dialog(CredentialsDialog, self, self.store)
        if self.manager:
            self.price.validate(force=True)

    def on_quantity__validate(self, widget, value):
        if self._expanded_edition:
            return
        if value <= 0:
            return ValidationError(_(u'The quantity should be positive.'))
        if value and not self._has_stock(value):
            return ValidationError(_(u'Quantity not available in stock.'))

    def on_sale_quantity__validate(self, widget, value):
        if value < self._original_sale_qty:
            return ValidationError(_(u'Can not decrease this quantity.'))
        total = value + self.model.return_quantity
        if total > self.model.quantity:
            return ValidationError(_(u'Sale and return quantity is greater '
                                     'than the total quantity.'))

    def on_return_quantity__validate(self, widget, value):
        if value < self._original_return_qty:
            return ValidationError(_(u'Can not decrease this quantity.'))
        total = value + self.model.sale_quantity
        if total > self.model.quantity:
            return ValidationError(_(u'Sale and return quantity is greater '
                                     'than the total quantity.'))
