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
## Author(s):   George Kussumoto        <george@async.com.br>
##
""" Production editors """

import sys

import gtk

from kiwi.datatypes import ValidationError

from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.domain.production import (ProductionItem, ProductionMaterial,
                                       ProductionService)
from stoqlib.lib.defaults import DECIMAL_PRECISION
from stoqlib.lib.message import info
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ProductionItemEditor(BaseEditor):
    gladefile = 'ProductionItemEditor'
    model_type = ProductionItem
    size = (-1, 150)
    model_name = _(u'Production Item')
    proxy_widgets = ['description', 'quantity', 'unit_description',]

    def setup_location_widgets(self):
        location = self.model.product.location
        if location:
            self.location.set_text(location)
        else:
            self.location.hide()
            self.location_content.hide()

    def setup_editor_widgets(self):
        self.order_number.set_text("%04d" %  self.model.order.id)
        self.quantity.set_adjustment(
            gtk.Adjustment(lower=0, upper=self.get_max_quantity(), step_incr=1))
        self.quantity.set_digits(DECIMAL_PRECISION)

    def get_max_quantity(self):
        """Returns the maximum quantity allowed in the quantity spinbutton.
        """
        return sys.maxint

    def setup_proxies(self):
        self.setup_editor_widgets()
        self.setup_location_widgets()
        self.proxy = self.add_proxy(
            self.model, ProductionItemEditor.proxy_widgets)

    #
    # Kiwi callbacks
    #

    def on_quantity__validate(self, widget, value):
        if not value or value <= 0:
            return ValidationError(_(u'This quantity should be positive.'))


class ProductionItemProducedEditor(ProductionItemEditor):
    title = _(u'Produce Items')

    quantity_title = _(u'Produced:')
    quantity_attribute = 'produced'

    def __init__(self, conn, model):
        ProductionItemEditor.__init__(self, conn, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self.quantity_lbl.set_text(self.quantity_title)
        self.proxy.remove_widget('quantity')
        self.quantity.set_property('model-attribute', self.quantity_attribute)
        self._quantity_proxy = self.add_proxy(self, ['quantity',])

    def get_max_quantity(self):
        return self.model.quantity - self.model.lost - self.model.produced

    def validate_confirm(self):
        try:
            self.model.produce(self.produced)
        except (ValueError, AssertionError):
            info(_(u'Can not produce this quantity. Not enough materials '
                    'can be allocated to produce this item.'))
            return False
        return True

    def on_quantity__validate(self, widget, value):
        if value <= 0:
            return ValidationError(
                _(u'Produced value should be greater than zero.'))


class ProductionItemLostEditor(ProductionItemProducedEditor):
    title = _(u'Lost Items')
    quantity_title = _(u'Lost:')
    quantity_attribute = 'lost'

    def get_max_quantity(self):
        return self.model.quantity - self.model.lost - self.model.produced

    def validate_confirm(self):
        try:
            self.model.add_lost(self.lost)
        except (ValueError, AssertionError):
            info(_(u'Can not lost this quantity. Not enough materials can '
                    'be allocated to this item.'))
            return False
        return True

    def on_quantity__validate(self, widget, value):
        if value <= 0:
            return ValidationError(
                _(u'Produced value should be greater than zero.'))


class ProductionServiceEditor(ProductionItemEditor):
    model_type = ProductionService
    model_name = _(u'Production Service')

    def setup_proxies(self):
        self.setup_editor_widgets()
        self.location_content.hide()
        self.proxy = self.add_proxy(
            self.model, ProductionServiceEditor.proxy_widgets)


class ProductionMaterialEditor(ProductionItemEditor):
    model_type = ProductionMaterial
    model_name = _(u'Production Material Item')
    proxy_widgets = ['description',]

    def setup_proxies(self):
        self.setup_editor_widgets()
        self.setup_location_widgets()
        self.proxy = self.add_proxy(
            self.model, ProductionMaterialEditor.proxy_widgets)

        self._has_components = self.model.product.has_components()
        if self._has_components:
            proxy_field = 'to_make'
            self.quantity_lbl.set_text(_(u'Quantity to make:'))
        else:
            proxy_field = 'to_purchase'
            self.quantity_lbl.set_text(_(u'Quantity to purchase:'))

        self.quantity.set_property('model-attribute', proxy_field)
        self.proxy.add_widget(proxy_field, self.quantity)

    #
    # Kiwi Callbacks
    #

    def on_quantity__validate(self, widget, value):
        if value and value < 0:
            return ValidationError(_(u'This quantity should be positive.'))
