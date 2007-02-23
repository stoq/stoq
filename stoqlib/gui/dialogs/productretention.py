# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Lincoln Molica                  <lincoln@async.com.br>
##
##

from decimal import Decimal

from kiwi.python import Settable
from kiwi.datatypes import currency

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.interfaces import ISellable, IStorable
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.message import warning

_ = stoqlib_gettext

class ProductRetentionDialog(BaseEditor):
    """This dialogs is responsible to make retention of products"""
    title = _(u"Product Retention")
    hide_footer = False
    size = (500, 300)
    model_type = Settable
    gladefile = "ProductRetentionDialog"
    proxy_widgets = ('quantity',
                     'reason',
                     'available',
                     'product_description',
                     'supplier')

    def __init__(self, conn, product):
        # FIXME: BaseEditor should provide support for this
        if IStorable(product, None) is None:
            raise TypeError("Product must provide a IStorable facet")
        if ISellable(product, None) is None:
            raise TypeError("Product must provide a ISellable facet")
        self.branch = get_current_branch(conn)
        self.product = product
        model = self._get_model(conn, product)
        BaseEditor.__init__(self, conn, model)
        self.setup_widgets()

    def _get_model(self, conn, product):
        return Settable(reason='',
                        available=currency(0),
                        product_description='',
                        supplier=self.product.get_main_supplier_name(),
                        quantity=Decimal())

    def setup_widgets(self):
        self.quantity.set_range(1,
                                self.storable.get_full_balance(self.branch))

    def setup_proxies(self):
        self.storable = IStorable(self.product)
        sellable = ISellable(self.product)
        self.model.product_description = sellable.get_description()
        self.model.available = self.storable.get_full_balance(self.branch)
        self.add_proxy(self.model, self.proxy_widgets)

    def validate_confirm(self):
        if not self.model.reason:
            warning(_(u'You can not retain a product without a reason!'))
            return False
        return True

    def on_confirm(self):
        return self.product.block(quantity=self.model.quantity,
                                  conn=self.conn, branch=self.branch,
                                  reason=self.model.reason,
                                  product=self.product)
