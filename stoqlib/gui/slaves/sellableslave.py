# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Gilma Gomes de Souza        <anaiort@gmail.com>
##
""" Slaves for sellables """

from kiwi.datatypes import ValidationError

from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.domain.sellable import OnSaleInfo
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

class OnSaleInfoSlave(BaseEditorSlave):
    """A slave for price and dates information when a certain product,
    service or gift certificate is on sale.
    """
    gladefile = 'OnSaleInfoSlave'
    model_type = OnSaleInfo
    proxy_widgets = ('on_sale_price',
                     'on_sale_start_date',
                     'on_sale_end_date')

    #
    # BaseEditorSlave hooks
    #

    def create_model(self, conn):
        return OnSaleInfo(connection=conn)

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    #
    # Kiwi callbacks
    #

    def on_on_sale_price__validate(self, entry, value):
        if value < 0:
           return ValidationError(_("Sale price can not be 0"))

class TributarySituationSlave(BaseEditorSlave):
    """
    This is base slave for tributary taxes applied to product, service
        and it's category if any.
    """
    gladefile = "TributarySituationSlave"
    proxy_widgets = ("tax_constant", "tax_value")
    model_type = None


    def __init__(self, conn, model=None):
        self.proxy = None
        BaseEditorSlave.__init__(self, conn, model)

    def setup_combos(self):
        """
        The child class must fill the combo
        """

    def _update_tax_value(self):
        constant = self.tax_constant.get_selected_data()
        if constant:
            self.model.tax_value = constant.tax_value
            if self.proxy:
                self.proxy.update('tax_value')

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self.setup_combos()
        self.proxy = self.add_proxy(self.model,
                            TributarySituationSlave.proxy_widgets)
        self._update_tax_value()

    def on_tax_constant__changed(self, combo):
        self._update_tax_value()
