# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
## Author(s):   Henrique Romano             <henrique@async.com.br>
##              Evandro Vale Miquelito      <evandro@async.com.br>
##              Bruno Rafael Garcia         <brg@async.com.br>
##
"""
stoq/gui/editors/sellable.py:

   Editors definitions for sellable.
"""

import gettext

from sqlobject.sqlbuilder import LIKE, func
from stoqlib.gui.editors import BaseEditor
from stoqlib.gui.dialogs import run_dialog
from stoqlib.exceptions import DatabaseInconsistency
from stoqdrivers.constants import UNIT_CUSTOM

from stoq.domain.sellable import (SellableCategory, AbstractSellable,
                                  SellableUnit)
from stoq.domain.interfaces import ISellable, IStorable
from stoq.domain.product import ProductSellableItem
from stoq.domain.giftcertificate import GiftCertificateItem
from stoq.domain.purchase import PurchaseItem
from stoq.gui.slaves.sellable import OnSaleInfoSlave
from stoq.lib.runtime import new_transaction
from stoq.lib.parameters import sysparam
from stoq.lib.validators import get_price_format_str

_ = gettext.gettext


#
# Slaves
#

class SellablePriceEditor(BaseEditor):
    model_name = 'Product Price'
    model_type = AbstractSellable
    gladefile = 'SellablePriceEditor'

    proxy_widgets = ('cost',
                     'markup',
                     'max_discount',
                     'commission',
                     'price')

    general_widgets = ('base_markup',)

    def __init__(self, conn, model=None):
        BaseEditor.__init__(self, conn, model)
        self.update_markup()
        self.update_commission()

    def set_widget_formats(self):
        widgets = (self.markup, self.base_markup, self.max_discount,
                   self.commission, self.price, self.cost)
        for widget in widgets:
            widget.set_data_format(get_price_format_str())

    def update_markup(self):
        price = self.model.base_sellable_info.price or 1.0
        cost = self.model.cost or 1.0
        self.model.markup = ((price / cost) - 1) * 100
        self.main_proxy.update('markup')

    def update_commission(self):
        if self.model.get_commission() is not None:
            return
        self.model.set_default_commission()
        self.main_proxy.update('base_sellable_info.commission')

    def update_price(self):
        cost = self.model.cost
        markup = self.model.markup 
        # XXX: Kiwi call spinbutton's callback two times, in the first one
        # the spin value is None, so we need to manage this.
        if markup is None:
            return
        self.model.base_sellable_info.price = cost + ((markup / 100) * cost)
        self.main_proxy.update('base_sellable_info.price')

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
        assert sellable
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
        self.update_markup()
        self.handler_unblock(self.markup, 'changed')

    def after_markup__content_changed(self, spin_button):
        self.handler_block(self.price, 'changed')
        self.update_price()
        self.handler_unblock(self.price, 'changed')


#
# Editors
#


class SellableEditor(BaseEditor):
    """This is a base class for ProductEditor and ServiceEditor and should be used
    when editing sellable objects. Note that sellable objects are instances
    inherited by AbstractSellable."""

    # This must be be properly defined in the child classes
    model_name = None
    model_type = None

    gladefile = 'SellableEditor' 
    product_widgets = ('notes',)
    sellable_unit_widgets = ("unit_combo",
                             "unit_entry")
    sellable_widgets = ('code',
                        'description',
                        'category_combo',
                        'cost',
                        'price')

    storable_widgets = ('stock_total_lbl',)

    def __init__(self, conn, model=None):
        self._sellable = None
        BaseEditor.__init__(self, conn, model)
        self.notes.set_accepts_tab(False)
        self.setup_widgets()
        self._original_code = self.sellable_proxy.model.code

    def set_widget_formats(self):
        for widget in (self.cost, self.stock_total_lbl, self.price):
            widget.set_data_format('%.02f')

    def edit_sale_price(self):
        sellable = ISellable(self.model, connection=self.conn)
        result = run_dialog(SellablePriceEditor, self, self.conn, sellable)
        if result:
            self.sellable_proxy.update('base_sellable_info.price')

    def setup_widgets(self):
        raise NotImplementedError

    def ensure_sellable_unit(self):
        unit = self._sellable.unit
        if unit.index == -1:
            self._sellable.unit = None
        else:
            if unit.index == UNIT_CUSTOM:
                query = LIKE(func.UPPER(SellableUnit.q.description),
                             "%%%s%%" % unit.description.upper())
            else:
                query = SellableUnit.q.index == unit.index
            conn = new_transaction()
            result = SellableUnit.select(query, connection=conn)
            count = result.count()
            if not count:
                return
            elif count > 1:
                raise DatabaseInconsistency("It is not possible to have "
                                            "more than one SellableUnit "
                                            "object representing the same "
                                            "unit.")
            self._sellable.unit = SellableUnit.get(result[0].id,
                                                   connection=self.conn)
        SellableUnit.delete(unit.id, connection=self.conn)

    def update_unit_entry(self):
        if (self._sellable and self._sellable.unit
            and self._sellable.unit.index == UNIT_CUSTOM):
            enabled = True
        else:
            enabled = False
        self.unit_entry.set_sensitive(enabled)

    #
    # BaseEditor hooks
    #

    def get_title_model_attribute(self, model):
        sellable = ISellable(model, connection=self.conn)
        return sellable.base_sellable_info.description

    def setup_combos(self):
        table = SellableCategory
        category_list = table.select(connection=self.conn)
        items = [('%s %s' % (obj.base_category.category_data.description, 
                             obj.category_data.description), obj)
                 for obj in category_list]
        self.category_combo.prefill(items)
        query = SellableUnit.q.index != UNIT_CUSTOM
        primitive_units = SellableUnit.select(query, connection=self.conn)
        items = [(_("No unit"), -1)]
        items.extend([(obj.description, obj.index)
                          for obj in primitive_units])
        items.append((_("Specify:"), UNIT_CUSTOM))
        self.unit_combo.prefill(items)

    def setup_proxies(self):
        self.set_widget_formats()
        self.setup_combos()
        self.main_proxy = self.add_proxy(self.model,
                                         SellableEditor.product_widgets)
        self._sellable = ISellable(self.model, connection=self.conn)
        self.sellable_proxy = self.add_proxy(self._sellable,
                                             SellableEditor.sellable_widgets)
        storable = IStorable(self.model, connection=self.conn)
        self.storable_proxy = self.add_proxy(storable,
                                             SellableEditor.storable_widgets)
        if self._sellable.unit:
            self._sellable.unit = self._sellable.unit.clone()
        else:
            self._sellable.unit = SellableUnit(description=None, index=None,
                                               connection=self.conn)
        self.unit_proxy = self.add_proxy(self._sellable.unit,
                                         SellableEditor.sellable_unit_widgets)
        self.update_unit_entry()

    #
    # Kiwi handlers
    #

    def on_unit_combo__changed(self, *args):
        self.update_unit_entry()

    def on_sale_price_button__clicked(self, button):
        self.edit_sale_price()

    def validate_confirm(self, *args):
        code = self.code.get_text()
        confirmed = True
        if code != self._original_code:
            conn = new_transaction() 
            qty = AbstractSellable.selectBy(code=code, connection=conn).count()
            if qty:
                msg = _('This code already exists!')
                self.code.set_invalid(msg)
                confirmed = False
            conn._connection.close()
        if confirmed:
            self.ensure_sellable_unit()
        return confirmed


class SellableItemEditor(BaseEditor):
    gladefile = 'SellableItemEditor'
    size = (550, 115)
    proxy_widgets = ('quantity', 
                     'value',
                     'total_label')
    model_names = {ProductSellableItem: _('Product Item'),
                   GiftCertificateItem: _('Gift Certificate'),
                   PurchaseItem: _('Gift Certificate')}

    def __init__(self, conn, model_type=ProductSellableItem, model=None,
                 value_attr=None):
        self.model_name = self._get_model_name(model_type)
        self.model_type = model_type
        self.value_attr = value_attr
        BaseEditor.__init__(self, conn, model)

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

    def get_title_model_attribute(self, model):
        return model.sellable.base_sellable_info.description

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
        format = get_price_format_str()
        self.value.set_data_format(format)
        self.total_label.set_data_format(format)
        if not sysparam(self.conn).EDIT_SELLABLE_PRICE:
            self.disable_price_fields()

    #
    # Callbacks
    #

    def on_quantity__value_changed(self, *args):
        self.proxy.update('total')

    def after_quantity__value_changed(self, *args):
        self.proxy.update('total')

    def after_value__changed(self, *args):
        self.proxy.update('total')

