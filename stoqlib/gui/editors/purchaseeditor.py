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
from sys import maxint as MAXINT

import gtk

from kiwi.datatypes import ValidationError

from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.domain.purchase import PurchaseOrder, PurchaseItem
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class PurchaseItemEditor(BaseEditor):
    gladefile = 'PurchaseItemEditor'
    model_type = PurchaseItem
    model_name = _("Purchase Item")
    proxy_widgets = ['cost',
                     'expected_receival_date',
                     'quantity',
                     'total',]

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)
        order = self.model.order
        if order.status == PurchaseOrder.ORDER_CONFIRMED:
            self._set_not_editable()

    def _setup_widgets(self):
        self.order.set_text("%04d" %  self.model.order.id)
        self.quantity.set_adjustment(gtk.Adjustment(lower=1, upper=MAXINT))
        self.description.set_text(self.model.sellable.get_description())

    def _set_not_editable(self):
        self.cost.set_sensitive(False)
        self.quantity.set_sensitive(False)

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
