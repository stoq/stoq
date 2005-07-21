# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Henrique Romano <henrique@async.com.br>
##
"""
gui/components/product_item_editor.py:

    Product item editor implementation.
"""


from stoqlib.gui.editors import BaseEditor

from stoq.domain.interfaces import ISellable
from stoq.domain.product import ProductAdaptToSellableItem
from stoq.lib.parameters import get_system_parameter


class ProductItemEditor(BaseEditor):
    title = _('Editing Product')
    size = (550, 100)

    model_type = ProductAdaptToSellableItem
    gladefile = 'ProductItemEditor'
    proxy_widgets = ('quantity', 'price')
    widgets = ('product_name', 'price_label') + proxy_widgets

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)

    def hide_price_fields(self):
        for widget in (self.price, self.price_label):
            widget.hide()

    #
    # BaseEditor hooks
    #

    def setup_proxies(self):
        # We need to setup the widgets format before the proxy fill them
        # with the values.
        self.setup_widgets()

        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    def setup_widgets(self):
        adapted = self.model.get_adapted()
        sellable = ISellable(adapted)
        self.product_name.set_text(sellable.description)

        sparam = get_system_parameter(self.conn)
        if not sparam.EDIT_SELLABLE_PRICE:
            self.hide_price_fields()
            return
        self.price.set_data_format('%.02f')

    def on_confirm(self):
        # XXX: this editor must use not-persistent objects. In this method
        # we will "link" the not persistent copy with the persistent one.
        # Waiting fix for bug #2043
        return self.model



