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
""" Production editors

This file contains several editors used in the production process:

L{ProductionItemEditor}: A base class with some information about the product or
                         material (description, location, unit). See subclasses
                         for specifc usage.

L{ProducedItemSlave}: A slave for serial number input.

L{ProductionItemProducedEditor}: A dialog to enter the number of itens produced.
                                 This uses the L{ProducedItemSlave} slave for
                                 serial number input
L{ProductionItemLostEditor}: A dialog to input the number of items lost.

L{ProductionServiceEditor}: Editor for an service item in the production order
L{ProductionMaterialEditor}: Item for an production material in the production
                             order
"""

import sys

import gtk

from kiwi.datatypes import ValidationError
from kiwi.python import Settable

from stoqlib.api import api
from stoqlib.domain.production import ProductionProducedItem
from stoqlib.domain.production import (ProductionItem, ProductionMaterial,
                                       ProductionService)
from stoqlib.gui.editors.baseeditor import BaseEditor, BaseEditorSlave
from stoqlib.lib.defaults import DECIMAL_PRECISION
from stoqlib.lib.message import info
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ProductionItemEditor(BaseEditor):
    """This is a base class for all items used in a production:
        - ProductionItem (For both Produced and Lost items)
        - ProductionService (When adding services to a production order)
        - ProductionMaterial (The material that will be consumed by an
          order)

    """

    gladefile = 'ProductionItemEditor'
    model_type = ProductionItem
    size = (-1, -1)
    model_name = _(u'Production Item')
    proxy_widgets = ['description', 'quantity', 'unit_description']
    help_section = 'production'

    def setup_location_widgets(self):
        location = self.model.product.location
        if location:
            self.location.set_text(location)
        else:
            self.location.hide()
            self.location_content.hide()

    def setup_editor_widgets(self):
        self.order_number.set_text("%04d" % self.model.order.id)
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


class ProducedItemSlave(BaseEditorSlave):
    """
    """
    gladefile = 'ProducedItemSlave'
    model_type = Settable
    proxy_widgets = ['serial_number']

    def __init__(self, conn, parent):
        self._parent = parent
        self._product = self._parent.model.product
        BaseEditorSlave.__init__(self, conn)

    #
    # BaseEditorSlave hooks
    #

    def create_model(self, conn):
        serial = ProductionProducedItem.get_last_serial_number(
                            self._product, conn)
        return Settable(serial_number=serial + 1)

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    def on_serial_number__validate(self, widget, value):
        qty = self._parent.quantity.read()
        first = value
        last = value + qty - 1
        if not ProductionProducedItem.is_valid_serial_range(self._product,
                                        first, last, self.conn):
            return ValidationError(_('There already is a serial number in '
                                     'the range %d - %d') % (first, last))


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
        self._quantity_proxy = self.add_proxy(self, ['quantity'])

    def setup_slaves(self):
        self.serial_slave = None
        if self.model.product.has_quality_tests():
            self.serial_slave = ProducedItemSlave(self.conn, self)
            self.attach_slave('place_holder', self.serial_slave)

    def get_max_quantity(self):
        return self.model.quantity - self.model.lost - self.model.produced

    def validate_confirm(self):
        serials = []
        if self.serial_slave:
            for i in range(self.produced):
                serials.append(self.serial_slave.model.serial_number + i)
        try:
            self.model.produce(self.produced, api.get_current_user(self.conn),
                               serials)
        except (ValueError, AssertionError):
            # FIXME: Adicionar mensagem exibindo produtos faltantes
            info(_(u'Can not produce this quantity. Not enough materials '
                    'allocated to this production.'))
            return False
        return True

    def on_quantity__validate(self, widget, value):
        if value <= 0:
            return ValidationError(
                _(u'Produced value should be greater than zero.'))


class ProductionMaterialLostEditor(ProductionItemProducedEditor):
    title = _(u'Lost Items')
    quantity_title = _(u'Lost:')
    quantity_attribute = 'lost'
    model_type = ProductionMaterial

    def validate_confirm(self):
        try:
            self.model.add_lost(self.lost)
        except (ValueError, AssertionError):
            info(_(u'Can not lose this quantity. Not enough materials '
                    'allocated to this production.'))
            return False
        return True

    def get_max_quantity(self):
        return self.model.allocated - self.model.lost - self.model.consumed

    def on_quantity__validate(self, widget, value):
        if value <= 0:
            return ValidationError(
                _(u'Lost value should be greater than zero.'))


class ProductionMaterialAllocateEditor(ProductionItemProducedEditor):
    title = _(u'Allocate Items')
    quantity_title = _(u'Allocate:')
    quantity_attribute = 'allocate'
    model_type = ProductionMaterial

    def validate_confirm(self):
        try:
            self.model.allocate(self.allocate)
        except (ValueError, AssertionError):
            info(_(u'Can not allocate this quantity.'))
            return False
        return True

    def get_max_quantity(self):
        return self.model.get_stock_quantity()

    def on_quantity__validate(self, widget, value):
        if value <= 0:
            return ValidationError(
                _(u'Lost value should be greater than zero.'))


#
#   Production Wizard Editors
#

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
    proxy_widgets = ['description']

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
