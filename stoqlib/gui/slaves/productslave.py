# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
##              Lincoln Molica       <lincoln@async.com.br>
##              Johan Dahlin         <jdahlin@async.com.br>
##
""" Slaves for products """

from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.slaves.sellableslave import SellableDetailsSlave
from stoqlib.domain.product import Product
from stoqlib.domain.sellable import Sellable


class ProductInformationSlave(BaseEditorSlave):
    gladefile = 'ProductInformationSlave'
    model_type = Product
    proxy_widgets = ['location', 'part_number', 'manufacturer',]

    def __init__(self, conn, model):
        BaseEditorSlave.__init__(self, conn, model)

    def setup_proxies(self):
        self.proxy = self.add_proxy(
            self.model, ProductInformationSlave.proxy_widgets)


class ProductDetailsSlave(SellableDetailsSlave):

    def setup_slaves(self):
        self.setup_image_slave(self.model.product)
        info_slave = ProductInformationSlave(self.conn, self.model.product)
        self.attach_slave('details_holder', info_slave)
