# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
"""Stock decrease items editor"""

import sys

import gtk

from kiwi.datatypes import ValidationError

from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.stockdecrease import StockDecreaseItem
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.editors.purchaseeditor import PurchaseItemEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class DecreaseItemEditor(PurchaseItemEditor):
    model_type = StockDecreaseItem
    model_name = _("Decrease Item")
    proxy_widgets = ['quantity']

    def __init__(self, conn, model, all_items):
        self.all_items = all_items
        BaseEditor.__init__(self, conn, model)

        for widget in [self.order_lbl, self.sold_lbl, self.cost_lbl,
                       self.expected_lbl, self.returned_lbl, self.total_lbl,
                       self.quantity_sold, self.cost, self.quantity_returned,
                       self.expected_receival_date, self.order]:
            widget.hide()

    def _setup_widgets(self):
        self.quantity.set_adjustment(gtk.Adjustment(lower=0, upper=sys.maxint,
                                                   step_incr=1))
        self.description.set_text(self.model.sellable.get_description())

    def on_quantity__validate(self, widget, value):
        if value <= 0:
            return ValidationError(_(u'Quantity must be greater than zero'))

        sellable = self.model.sellable
        storable = IStorable(sellable.product)
        branch = self.model.stock_decrease.branch
        balance = storable.get_full_balance(branch=branch)

        # Also consider the items already removed from stock.
        for i in self.all_items:
            if i.sellable == sellable and i != self.model:
                balance -= i.quantity

        if value > balance:
            return ValidationError(
                _(u'Quantity is greater than the quantity in stock.'))
