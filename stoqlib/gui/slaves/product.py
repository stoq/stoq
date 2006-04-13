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
## Author(s):   Henrique Romano      <henrique@async.com.br>
##
""" Slaves for products """

from stoqlib.gui.base.editors import BaseEditorSlave
from stoqlib.domain.product import (ProductSupplierInfo, Product,
                                    ProductAdaptToSellable)
from stoqdrivers.constants import TAX_NONE

class TributarySituationSlave(BaseEditorSlave):
    gladefile = "TributarySituationSlave"
    proxy_widgets = ("tax_type",
                     "tax_value")
    model_type = ProductAdaptToSellable

    def _update_tax_box(self):
        self.tax_box.set_sensitive(self.model.tax_type != TAX_NONE)

    def _setup_combos(self):
        self.tax_type.prefill([(v, k) for (k, v) in
                               ProductAdaptToSellable.tax_type_names.items()])

    def _setup_widgets(self):
        self._setup_combos()

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model, TributarySituationSlave.proxy_widgets)

    #
    # Kiwi callbacks
    #

    def on_tax_type__changed(self, combo):
        self._update_tax_box()
