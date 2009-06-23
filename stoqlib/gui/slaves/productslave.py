# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2009 Async Open Source <http://www.async.com.br>
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
##              George Y. Kussumoto  <george@async.com.br>
##
""" Slaves for products """

from kiwi.datatypes import ValidationError

from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.slaves.sellableslave import SellableDetailsSlave
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.product import Product
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ProductInformationSlave(BaseEditorSlave):
    gladefile = 'ProductInformationSlave'
    model_type = Product
    proxy_widgets = ['location', 'part_number', 'manufacturer',]
    storable_widgets = ['minimum_quantity', 'maximum_quantity',]

    def __init__(self, conn, model):
        BaseEditorSlave.__init__(self, conn, model)
        self._setup_unit_labels()

    def _setup_unit_labels(self):
        unit = self.model.sellable.unit
        if unit is None:
            unit_desc = _(u'Unit(s)')
        else:
            unit_desc = unit.description

        for label in [self.min_unit, self.max_unit]:
            label.set_text(unit_desc)

    def setup_proxies(self):
        self.proxy = self.add_proxy(
            self.model, ProductInformationSlave.proxy_widgets)

        storable = IStorable(self.model, None)
        if storable is not None:
            self.storable_proxy = self.add_proxy(
                storable, ProductInformationSlave.storable_widgets)

    def hide_stock_details(self):
        self.stock.hide()
        self.part_number_lbl.hide()
        self.part_number.hide()
        self.manufacturer_lbl.hide()
        self.manufacturer.hide()

    #
    # Kiwi Callbacks
    #

    def on_minimum_quantity__validate(self, widget, value):
        if value and value < 0:
            return ValidationError(_(u'Minimum value must be a positive value.'))

        maximum = self.maximum_quantity.read()
        if maximum and value > maximum:
            return ValidationError(_(u'Minimum must be lower than the '
                                      'maximum value.'))

    def on_maximum_quantity__validate(self, widget, value):
        if not value:
            return
        if value and value < 0:
            return ValidationError(_(u'Maximum value must be a positive value.'))

        minimum = self.minimum_quantity.read()
        if minimum and minimum > value:
            return ValidationError(_(u'Maximum must be greater than the '
                                      'minimum value.'))


class ProductDetailsSlave(SellableDetailsSlave):

    def setup_slaves(self):
        self.setup_image_slave(self.model.product)
        self.info_slave = ProductInformationSlave(self.conn, self.model.product)
        self.attach_slave('details_holder', self.info_slave)

    def hide_stock_details(self):
        self.info_slave.hide_stock_details()
