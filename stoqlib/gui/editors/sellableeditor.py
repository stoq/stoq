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
## Author(s):   Henrique Romano             <henrique@async.com.br>
##              Evandro Vale Miquelito      <evandro@async.com.br>
##              Bruno Rafael Garcia         <brg@async.com.br>
##
""" Editors definitions for sellable"""

from sqlobject.sqlbuilder import LIKE, func
from stoqdrivers.constants import UNIT_CUSTOM, UNIT_WEIGHT
from kiwi.python import Settable

from stoqlib.database.runtime import new_transaction
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.editors import BaseEditor
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.domain.sellable import (SellableCategory, ASellable,
                                     SellableUnit)
from stoqlib.domain.interfaces import ISellable, IStorable
from stoqlib.domain.product import ProductSellableItem
from stoqlib.domain.giftcertificate import GiftCertificateItem
from stoqlib.domain.purchase import PurchaseItem
from stoqlib.domain.service import DeliveryItem
from stoqlib.gui.slaves.sellableslave import OnSaleInfoSlave
from stoqlib.gui.slaves.imageslaveslave import ImageSlave
from stoqlib.lib.validators import get_price_format_str

_ = stoqlib_gettext


#
# Slaves
#

class SellablePriceEditor(BaseEditor):
    model_name = 'Product Price'
    model_type = ASellable
    gladefile = 'SellablePriceEditor'

    proxy_widgets = ('cost',
                     'markup',
                     'max_discount',
                     'commission',
                     'price')

    general_widgets = ('base_markup',)

    def set_widget_formats(self):
        widgets = (self.markup, self.base_markup, self.max_discount,
                   self.commission)
        for widget in widgets:
            widget.set_data_format(get_price_format_str())

    #
    # BaseEditor hooks
    #

    def get_title(self, *args):
        return _('Price settings')

    def setup_proxies(self):
        self.set_widget_formats()
        self.main_proxy = self.add_proxy(self.model,
                                         SellablePriceEditor.proxy_widgets)
        if self.model.markup is not None:
            return
        sellable = ISellable(self.model.get_adapted())
        self.model.markup = sellable.get_suggested_markup()
        self.main_proxy.update('markup')

    def setup_slaves(self):
        slave = OnSaleInfoSlave(self.conn, self.model.on_sale_info)
        self.attach_slave('on_sale_holder', slave)

    #
    # Kiwi handlers
    #

    def after_price__content_changed(self, entry_box):
        self.handler_block(self.markup, 'changed')
        self.main_proxy.update("markup")
        self.handler_unblock(self.markup, 'changed')

    def after_markup__content_changed(self, spin_button):
        self.handler_block(self.price, 'changed')
        self.main_proxy.update("price")
        self.handler_unblock(self.price, 'changed')


#
# Editors
#


class SellableEditor(BaseEditor):
    """This is a base class for ProductEditor and ServiceEditor and should
    be used when editing sellable objects. Note that sellable objects
    are instances inherited by ASellable."""

    # This must be be properly defined in the child classes
    model_name = None
    model_type = None

    gladefile = 'SellableEditor'
    sellable_unit_widgets = ("unit_combo",
                             "unit_entry")
    barcode_widgets = 'barcode',
    sellable_widgets = ('code',
                        'description',
                        'category_combo',
                        'cost',
                        'price',
                        'notes')
    proxy_widgets = (sellable_unit_widgets +
                     sellable_widgets + barcode_widgets)

    storable_widgets = ('stock_total_lbl',)

    def __init__(self, conn, model=None):
        self._sellable = None
        self._requires_weighing_text = ("<b>%s</b>"
                                        % _(u"This unit type requires "
                                            "weighing"))
        BaseEditor.__init__(self, conn, model)

        # image slave for sellables
        image_slave = ImageSlave(self.conn, self.model)
        self.attach_slave("sellable_image_holder", image_slave)

        self._original_barcode = self._sellable.barcode
        self.setup_widgets()

        self.set_description(
            ISellable(self.model).base_sellable_info.description)

    def set_widget_formats(self):
        for widget in (self.cost, self.stock_total_lbl, self.price):
            widget.set_data_format('%.02f')
        self.requires_weighing_label.set_size("small")
        self.requires_weighing_label.set_text("")

    def edit_sale_price(self):
        sellable = ISellable(self.model)
        result = run_dialog(SellablePriceEditor, self, self.conn, sellable)
        if result:
            self.sellable_proxy.update('base_sellable_info.price')

    def setup_widgets(self):
        raise NotImplementedError

    def ensure_sellable_unit(self):
        unit = self._sellable.unit
        if unit.unit_index == -1:
            self._sellable.unit = None
        else:
            if unit.unit_index == UNIT_CUSTOM:
                query = LIKE(func.UPPER(SellableUnit.q.description),
                             "%%%s%%" % unit.description.upper())
            else:
                query = SellableUnit.q.unit_index == unit.unit_index
            trans = new_transaction()
            sellable = SellableUnit.selectOne(query, connection=trans)
            if not sellable:
                return
            self._sellable.unit = trans.get(sellable)

        SellableUnit.delete(unit.id, connection=self.trans)

    def update_unit_entry(self):
        if (self._sellable and self._sellable.unit
            and self._sellable.unit.unit_index == UNIT_CUSTOM):
            enabled = True
        else:
            enabled = False
        self.unit_entry.set_sensitive(enabled)

    def update_requires_weighing_label(self):
        if (self._sellable is not None
            and self._sellable.unit.unit_index == UNIT_WEIGHT):
            self.requires_weighing_label.set_text(self._requires_weighing_text)
        else:
            self.requires_weighing_label.set_text("")

    #
    # BaseEditor hooks
    #

    def setup_combos(self):
        category_list = SellableCategory.select(connection=self.conn)
        items = [(cat.get_full_description(), cat) for cat in category_list]
        self.category_combo.prefill(items)
        query = SellableUnit.q.unit_index != UNIT_CUSTOM
        primitive_units = SellableUnit.select(query, connection=self.conn)
        items = [(_("No unit"), -1)]
        items.extend([(obj.description, obj.unit_index)
                          for obj in primitive_units])
        items.append((_("Specify:"), UNIT_CUSTOM))
        self.unit_combo.prefill(items)

    def setup_proxies(self):
        self.set_widget_formats()
        self.setup_combos()
        self._sellable = ISellable(self.model)

        barcode = self._sellable.barcode
        self.barcode_proxy = self.add_proxy(Settable(barcode=barcode),
                                            SellableEditor.barcode_widgets)

        self.sellable_proxy = self.add_proxy(self._sellable,
                                             SellableEditor.sellable_widgets)

        storable = IStorable(self.model, None)
        if storable is not None:
            self.add_proxy(storable,
                           SellableEditor.storable_widgets)
        if self._sellable.unit:
            self._sellable.unit = self._sellable.unit.clone()
        else:
            self._sellable.unit = SellableUnit(description=None,
                                               unit_index=None,
                                               connection=self.conn)
        self.unit_proxy = self.add_proxy(self._sellable.unit,
                                         SellableEditor.sellable_unit_widgets)
        self.update_requires_weighing_label()
        self.update_unit_entry()

    #
    # Kiwi handlers
    #

    def on_unit_combo__changed(self, *args):
        self.update_requires_weighing_label()
        self.update_unit_entry()

    def on_sale_price_button__clicked(self, button):
        self.edit_sale_price()

    def validate_confirm(self, *args):
        barcode = self.barcode_proxy.model.barcode
        if barcode != self._original_barcode:
            if ASellable.check_barcode_exists(barcode):
                msg = _('The barcode %s already exists') % barcode
                self.barcode.set_invalid(msg)
                return False
            self._sellable.barcode = barcode
        self.ensure_sellable_unit()
        return True

class SellableItemEditor(BaseEditor):
    gladefile = 'SellableItemEditor'
    size = (550, 115)
    proxy_widgets = ('quantity',
                     'value',
                     'total_label')
    model_names = {ProductSellableItem: _('Product Item'),
                   GiftCertificateItem: _('Gift Certificate'),
                   DeliveryItem: _('Delivery Item'),
                   PurchaseItem: _('Gift Certificate')}

    def __init__(self, conn, model_type=ProductSellableItem, model=None,
                 value_attr=None, restrict_increase_qty=False,
                 editable_price=True):
        self.model_name = self._get_model_name(model_type)
        self.model_type = model_type
        self.value_attr = value_attr
        BaseEditor.__init__(self, conn, model)
        if restrict_increase_qty:
            self.quantity.set_range(1, self.model.quantity)
        if not editable_price:
            self.disable_price_fields()
        self.set_description(
            self.model.sellable.base_sellable_info.description)


    def _get_model_name(self, model_type):
        if not self.model_names.has_key(model_type):
            raise ValueError('Invalid model type for SellableItemEditor, '
                             'got %s' % model_type)
        return self.model_names[model_type]

    def disable_price_fields(self):
        for widget in (self.value, self.price_label):
            widget.set_sensitive(False)

    #
    # BaseEditor hooks
    #

    def setup_proxies(self):
        # We need to setup the widgets format before the proxy fill them
        # with the values.
        self.setup_widgets()
        if self.value_attr:
            self.value.set_property('model-attribute', self.value_attr)
        self.proxy = self.add_proxy(self.model,
                                    SellableItemEditor.proxy_widgets)

    def setup_widgets(self):
        sellable = self.model.sellable
        self.sellable_name.set_text(sellable.base_sellable_info.description)

    #
    # Callbacks
    #

    def on_quantity__value_changed(self, *args):
        self.proxy.update('total')

    def after_quantity__value_changed(self, *args):
        self.proxy.update('total')

    def after_value__changed(self, *args):
        self.proxy.update('total')

