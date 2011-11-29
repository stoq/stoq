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

import sys

import gtk

from kiwi.datatypes import ValidationError

from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.loan import LoanItem
from stoqlib.gui.editors.baseeditor import BaseEditor
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

    def __init__(self, conn, model, expanded_edition=False):
        """An editor for a loan item. If the expaned_edition is True, the
        editor will enable the sale_quantity and return_quantity fields to be
        edited and will lock the quantity and price fields.
        @param conn: a database connection.
        @param model: a loan item.
        @param expanded_edition: whether or not we should enable sale_quantity
                                 and return_quantity fields to be edited.
        """
        self._expanded_edition = expanded_edition
        self._branch = model.loan.branch
        self._original_sale_qty = model.sale_quantity
        self._original_return_qty = model.return_quantity
        BaseEditor.__init__(self, conn, model)

    def _setup_widgets(self):
        self.sale.set_text("%04d" % self.model.loan.id)
        self.description.set_text(self.model.sellable.get_description())
        for widget in [self.sale_quantity, self.return_quantity]:
            widget.set_adjustment(gtk.Adjustment(lower=0, upper=sys.maxint,
                                                 step_incr=1))
        self.quantity.set_adjustment(gtk.Adjustment(lower=1, step_incr=1,
                                                    upper=sys.maxint))
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
        storable = IStorable(self.model.sellable.product, None)
        if storable is not None:
            available = storable.get_full_balance(self._branch)
        else:
            available = 0
        return available >= quantity

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model, LoanItemEditor.proxy_widgets)

    #
    # Kiwi callbacks
    #

    def on_price__validate(self, widget, value):
        if value <= 0:
            return ValidationError(_(u'The price must be greater than zero.'))

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
