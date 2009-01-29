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
##              Fabio Morbec                <fabio@async.com.br>
##              Gilma Gomes de Souza        <anaiort@gmail.com>
##
""" Editors definitions for sellable"""

import gtk

from kiwi.datatypes import ValidationError
from kiwi.python import Settable
from kiwi.ui.objectlist import Column
from stoqdrivers.enum import TaxType, UnitType

from stoqlib.database.orm import LIKE, const
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.purchase import PurchaseItem
from stoqlib.domain.receiving import ReceivingOrderItem
from stoqlib.domain.sale import SaleItem, DeliveryItem
from stoqlib.domain.sellable import (SellableCategory, Sellable,
                                     SellableUnit,
                                     SellableTaxConstant)
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.lists import ModelListDialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.slaves.commissionslave import CommissionSlave
from stoqlib.gui.slaves.sellableslave import OnSaleInfoSlave
from stoqlib.gui.slaves.imageslaveslave import ImageSlave
from stoqlib.lib.message import info
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.validators import get_price_format_str

_ = stoqlib_gettext

class _TemporarySellableUnit(object):
    def __init__(self, description, unit_index):
        self.description = description
        self.unit_index = unit_index

#
# Editors
#
class SellableTaxConstantEditor(BaseEditor):
    gladefile = 'SellableTaxConstantEditor'
    model_type = SellableTaxConstant
    model_name = _('Taxes and Tax rates')
    proxy_widgets = ('description',
                     'tax_value')

    def __init__(self, conn, model=None):
        BaseEditor.__init__(self, conn, model)



    #
    # BaseEditor
    #

    def create_model(self, conn):
        return SellableTaxConstant(tax_type=int(TaxType.CUSTOM),
                                   tax_value=None,
                                   description=u'',
                                   connection=conn)

    def on_confirm(self):
        return self.model

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model,
                                    SellableTaxConstantEditor.proxy_widgets)


class SellableTaxConstantsDialog(ModelListDialog):

    # ModelListDialog
    model_type = SellableTaxConstant
    editor_class = SellableTaxConstantEditor
    size = (500, 300)
    title = _("Taxes")

    # ListDialog
    columns = [
        Column('description', _('Description'), data_type=str,
               width=200),
        Column('value', _('Tax rate'), data_type=str),
    ]

    def selection_changed(self, constant):
        if constant is None:
            return
        is_custom = constant.tax_type == TaxType.CUSTOM
        self.listcontainer.remove_button.set_sensitive(is_custom)
        self.listcontainer.edit_button.set_sensitive(is_custom)

    def delete_model(self, model, trans):
        sellables = Sellable.selectBy(tax_constant=model, connection=trans)
        quantity = sellables.count()
        if quantity > 0:
            msg = _(u"You can't remove this tax, since %d products or "
                    "services are taxed with '%s'." % (
                    quantity, model.get_description()))
            info(msg)
        else:
            SellableTaxConstant.delete(model.id, connection=trans)


class SellablePriceEditor(BaseEditor):
    model_name = _(u'Product Price')
    model_type = Sellable
    gladefile = 'SellablePriceEditor'

    proxy_widgets = ('cost',
                     'markup',
                     'max_discount',
                     'price')

    general_widgets = ('base_markup',)

    def set_widget_formats(self):
        widgets = (self.markup, self.base_markup, self.max_discount)
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
        sellable = self.model.sellable
        self.model.markup = sellable.get_suggested_markup()
        self.main_proxy.update('markup')

    def setup_slaves(self):
        slave = OnSaleInfoSlave(self.conn, self.model.on_sale_info)
        self.attach_slave('on_sale_holder', slave)

        commission_slave = CommissionSlave(self.conn, self.model)
        self.attach_slave('on_commission_data_holder', commission_slave)
        if self.model.category:
            desc = self.model.category.description
            label = _('Calculate Commission From: %s') % desc
            commission_slave.change_label(label)

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

    def on_confirm(self):
        slave = self.get_slave('on_commission_data_holder')
        slave.confirm()
        return self.model

#
# Editors
#


class SellableEditor(BaseEditor):
    """This is a base class for ProductEditor and ServiceEditor and should
    be used when editing sellable objects. Note that sellable objects
    are instances inherited by Sellable."""

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
        self.enable_window_controls()

        # image slave for sellables
        image_slave = ImageSlave(self.conn, self.model)
        self.attach_slave("sellable_image_holder", image_slave)

        self._original_barcode = self._sellable.barcode
        self.setup_widgets()

        self.set_description(
            self.model.sellable.base_sellable_info.description)

    def add_extra_tab(self, tabname, tabslave):
        self.sellable_notebook.set_show_tabs(True)
        self.sellable_notebook.set_show_border(True)

        event_box = gtk.EventBox()
        event_box.show()
        self.sellable_notebook.append_page(event_box, gtk.Label(tabname))
        self.attach_slave(tabname, tabslave, event_box)

    def set_widget_formats(self):
        for widget in (self.cost, self.stock_total_lbl, self.price):
            widget.set_data_format('%.02f')
        self.requires_weighing_label.set_size("small")
        self.requires_weighing_label.set_text("")

    def edit_sale_price(self):
        sellable = self.model.sellable
        result = run_dialog(SellablePriceEditor, self, self.conn, sellable)
        if result:
            self.sellable_proxy.update('base_sellable_info.price')

    def setup_widgets(self):
        raise NotImplementedError

    def ensure_sellable_unit(self):
        if self._unit.unit_index is None:
            self._sellable.unit = None
        else:
            if self._unit.unit_index == UnitType.CUSTOM:
                query = LIKE(const.UPPER(SellableUnit.q.description),
                             "%%%s%%" % self._unit.description.upper())
            else:
                query = SellableUnit.q.unit_index == self._unit.unit_index

            s_unit = SellableUnit.selectOne(query, connection=self.conn)
            if s_unit is None:
                s_unit = SellableUnit(description=self._unit.description,
                                      unit_index=self._unit.unit_index,
                                      connection=self.conn)
            self._sellable.unit = s_unit

    def update_unit_entry(self):
        self.unit_entry.set_sensitive(self._unit.unit_index == UnitType.CUSTOM)

    def update_requires_weighing_label(self):
        if self._unit.unit_index == UnitType.WEIGHT:
            self.requires_weighing_label.set_text(self._requires_weighing_text)
        else:
            self.requires_weighing_label.set_text("")

    #
    # BaseEditor hooks
    #

    def setup_combos(self):
        category_list = SellableCategory.select(
            SellableCategory.q.categoryID != None,
            connection=self.conn).orderBy('description')

        items = [(cat.get_description(), cat) for cat in category_list]
        self.category_combo.prefill(items)

        primitive_units = SellableUnit.select(
            SellableUnit.q.unit_index != int(UnitType.CUSTOM),
            connection=self.conn)
        items = [(_("No unit"), None)]
        items.extend([(obj.description, obj.unit_index)
                          for obj in primitive_units])
        items.append((_("Specify:"), int(UnitType.CUSTOM)))
        self.unit_combo.prefill(items)

    def setup_proxies(self):
        self.set_widget_formats()
        self._sellable = self.model.sellable

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
            self._unit = _TemporarySellableUnit(
                            description=self._sellable.unit.description,
                            unit_index=self._sellable.unit.unit_index)
        else:
            self._unit = _TemporarySellableUnit(description=None,
                                                unit_index=None)

        self.setup_combos()
        self.unit_proxy = self.add_proxy(self._unit,
                                         SellableEditor.sellable_unit_widgets)
        self.update_requires_weighing_label()
        self.update_unit_entry()

    #
    # Kiwi handlers
    #

    def on_unit_combo__changed(self, combo):
        self.update_requires_weighing_label()
        self.update_unit_entry()

    def on_sale_price_button__clicked(self, button):
        self.edit_sale_price()

    def validate_confirm(self, *args):
        barcode = self.barcode_proxy.model.barcode
        if barcode != self._original_barcode:
            if Sellable.check_barcode_exists(barcode):
                msg = _('The barcode %s already exists') % barcode
                self.barcode.set_invalid(msg)
                return False
            self._sellable.barcode = barcode
        self.ensure_sellable_unit()
        return True

    def on_price__validate(self, entry, value):
        if value <= 0:
           return ValidationError(_("Price cannot be zero or negative"))

    def on_cost__validate(self, entry, value):
        if value <= 0:
           return ValidationError(_("Cost cannot be zero or negative"))

    def on_unit_entry__validate(self, entry, value):
        unit = self._unit
        if unit.unit_index == UnitType.CUSTOM and not value:
            return ValidationError(_(u"Unit must have a description"))

    def on_category_combo__content_changed(self, widget):
        category_cb = self.category_combo.get_text()
        category = SellableCategory.selectOneBy(description=category_cb,
                                                connection=self.conn)
        self.model.category = category

class SellableItemEditor(BaseEditor):
    gladefile = 'SellableItemEditor'
    proxy_widgets = ('quantity',
                     'price',
                     'total')
    model_names = {ReceivingOrderItem: _('Receiving Item'),
                   SaleItem: _('Sale Item'),
                   DeliveryItem: _('Delivery Item'),
                   PurchaseItem: _('Purchase Item')}

    def __init__(self, conn, model_type=ReceivingOrderItem, model=None,
                 restrict_increase_qty=True):
        self.model_name = self._get_model_name(model_type)
        self.model_type = model_type
        BaseEditor.__init__(self, conn, model)
        if restrict_increase_qty:
            if isinstance(self.model, ReceivingOrderItem):
                quantity = self.model.get_remaining_quantity()
            else:
                quantity = self.model.quantity
            self.quantity.set_range(1, quantity)
        self.set_description(
            self.model.sellable.base_sellable_info.description)


    def _get_model_name(self, model_type):
        if not self.model_names.has_key(model_type):
            raise ValueError('Invalid model type for SellableItemEditor, '
                             'got %s' % model_type)
        return self.model_names[model_type]

    #
    # BaseEditor hooks
    #

    def setup_proxies(self):
        # We need to setup the widgets format before the proxy fill them
        # with the values.
        self.setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    SellableItemEditor.proxy_widgets)

    def setup_widgets(self):
        sellable = self.model.sellable
        self.sellable_name.set_text(sellable.base_sellable_info.description)

    #
    # Callbacks
    #

    def after_quantity__value_changed(self, spinbutton):
        self.proxy.update('total')
