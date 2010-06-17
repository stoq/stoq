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
## Author(s):   George Kussumoto        <george@async.com.br>
##
""" Purchase editors """


import datetime
import sys

import gtk

from kiwi.datatypes import ValidationError

from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.domain.purchase import PurchaseOrder, PurchaseItem
from stoqlib.lib.defaults import DECIMAL_PRECISION
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class PurchaseItemEditor(BaseEditor):
    gladefile = 'PurchaseItemEditor'
    model_type = PurchaseItem
    model_name = _("Purchase Item")
    proxy_widgets = ['cost',
                     'expected_receival_date',
                     'quantity',
                     'quantity_sold',
                     'quantity_returned',
                     'total',]

    def __init__(self, conn, model):
        self._original_sold_qty = model.quantity_sold
        self._original_returned_qty = model.quantity_returned
        BaseEditor.__init__(self, conn, model)
        order = self.model.order
        if order.status == PurchaseOrder.ORDER_CONFIRMED:
            self._set_not_editable()
        if order.status == PurchaseOrder.ORDER_CONSIGNED:
            self._set_not_editable()
        else:
            self._disable_consignment_fields()


    def _setup_widgets(self):
        self.order.set_text("%04d" %  self.model.order.id)
        for widget in [self.quantity, self.cost, self.quantity_sold,
                       self.quantity_returned]:
            widget.set_adjustment(gtk.Adjustment(lower=0, upper=sys.maxint,
                                                 step_incr=1))
        self.description.set_text(self.model.sellable.get_description())
        if sysparam(self.conn).USE_FOUR_PRECISION_DIGITS:
            self.cost.set_digits(4)
        else:
            self.cost.set_digits(DECIMAL_PRECISION)

    def _set_not_editable(self):
        self.cost.set_sensitive(False)
        self.quantity.set_sensitive(False)

    def _disable_consignment_fields(self):
        self.sold_lbl.hide()
        self.returned_lbl.hide()
        self.quantity_sold.hide()
        self.quantity_returned.hide()

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model, PurchaseItemEditor.proxy_widgets)

    #
    # Kiwi callbacks
    #

    def on_expected_receival_date__validate(self, widget, value):
        if value < datetime.date.today():
            return ValidationError(_(u'The expected receival date should be '
                                     'a future date or today.'))

    def on_cost__validate(self, widget, value):
        if value <= 0:
            return ValidationError(_(u'The cost should be greater than zero.'))

    def on_quantity__validate(self, widget, value):
        if value <= 0:
            return ValidationError(_(u'The quantity should be greater than '
                                     'zero.'))

    def on_quantity_sold__validate(self, widget, value):
        if value < self._original_sold_qty:
            return ValidationError(_(u'Can not decrease this quantity.'))
        total = value + self.model.quantity_returned
        if value and total > self.model.quantity_received:
            return ValidationError(_(u'Invalid sold quantity.'))

    def on_quantity_returned__validate(self, widget, value):
        if value < self._original_returned_qty:
            return ValidationError(_(u'Can not decrease this quantity.'))
        total = value + self.model.quantity_sold
        if value and total > self.model.quantity_received:
            return ValidationError(_(u'Invalid returned quantity'))
