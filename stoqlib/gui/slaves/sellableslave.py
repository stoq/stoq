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
