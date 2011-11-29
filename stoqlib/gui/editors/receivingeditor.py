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
""" Receiving editors """


from kiwi.datatypes import ValidationError

from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.domain.receiving import ReceivingOrderItem
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ReceivingItemEditor(BaseEditor):
    gladefile = 'ReceivingItemEditor'
    model_name = _(u'Receiving Item')
    model_type = ReceivingOrderItem
    size = (500, 200)
    proxy_widgets = ('cost',
                     'description',
                     'quantity',
                     'remaining_quantity',
                     'total', )

    #
    # BaseEditor hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(
            self.model, ReceivingItemEditor.proxy_widgets)

    def _setup_widgets(self):
        receiving = self.model.receiving_order
        self.receiving_order.set_text(receiving.get_receiving_number_str())
        self.purchase_order.set_text(receiving.get_order_number())

        max_quantity = self.model.get_remaining_quantity()
        self.quantity.set_range(0, max_quantity)

    #
    # Callbacks
    #

    def on_quantity__validate(self, widget, value):
        if value < 0:
            return ValidationError(_(u'The receiving quantity must be '
                                      'zero or a positive number.'))
        max_quantity = self.model.get_remaining_quantity()
        if value > max_quantity:
            return ValidationError(
                _(u'You can not receive more than %d items.') % max_quantity)

    def after_quantity__value_changed(self, widget):
        self.proxy.update('total')
