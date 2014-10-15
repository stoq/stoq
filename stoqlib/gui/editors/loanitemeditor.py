# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010-2013 Async Open Source <http://www.async.com.br>
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
from stoqlib.lib.defaults import QUANTITY_PRECISION, MAX_INT
from stoqlib.lib.translation import stoqlib_gettext as _


class LoanItemEditor(BaseEditor):
    gladefile = 'LoanItemEditor'
    model_type = LoanItem
    model_name = _("Loan Item")
    proxy_widgets = ['price',
                     'quantity',
                     'total']

    def __init__(self, store, model):
        """An editor for a loan item.

        :param store: a store.
        :param model: a loan item.
        """
        self.manager = None
        self.proxy = None
        BaseEditor.__init__(self, store, model)

    def _setup_widgets(self):
        self._calc = CalculatorPopup(self.price,
                                     CalculatorPopup.MODE_SUB)

        self.sale.set_text(unicode(self.model.loan.identifier))
        self.description.set_text(self.model.sellable.get_description())
        self.original_price.update(self.model.price)
        for widget in [self.quantity, self.price]:
            widget.set_adjustment(gtk.Adjustment(lower=0, upper=MAX_INT,
                                                 step_incr=1))
        unit = self.model.sellable.unit
        self.quantity.set_digits(
            QUANTITY_PRECISION if unit and unit.allow_fraction else 0)

        self.tabs.set_show_tabs(False)

    def _has_stock(self, quantity):
        batch = self.model.batch
        sellable = self.model.sellable
        storable = sellable.product_storable
        if storable is None:
            return None

        total_quatity = sum(
            i.quantity for i in self.model.loan.loaned_items if
            i != self.model and (i.sellable, i.batch) == (sellable, batch))

        # FIXME: It would be better to just use storable.get_balance_for_branch
        # and pass batch=batch there. That would avoid this if
        if batch is not None:
            balance = batch.get_balance_for_branch(self.model.loan.branch)
        else:
            balance = storable.get_balance_for_branch(self.model.loan.branch)

        return quantity <= balance - total_quatity

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
                (_(u'Max discount for this product is %.2f%%.') %
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
        if value <= 0:
            return ValidationError(_(u'The quantity should be positive.'))
        if value and not self._has_stock(value):
            return ValidationError(_(u'Quantity not available in stock.'))
