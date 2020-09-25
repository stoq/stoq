# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

import datetime
import decimal

from kiwi.currency import currency
from kiwi.ui.objectlist import Column
from storm.expr import LeftJoin, Cast
from stoqdrivers.enum import TaxType

from stoqlib.api import api
from stoqlib.database.viewable import Viewable
from stoqlib.database.expr import Case
from stoqlib.domain.sellable import (Sellable, ClientCategoryPrice,
                                     SellableUnit, SellableCategory,
                                     SellableTaxConstant)
from stoqlib.domain.fiscal import CfopData
from stoq.lib.gui.base.lists import ModelListDialog, ModelListSlave
from stoq.lib.gui.editors.sellableeditor import SellableTaxConstantEditor
from stoq.lib.gui.dialogs.masseditordialog import (Field, MassEditorSearch,
                                                   AccessorField, ReferenceField)
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.message import info
from stoqlib.lib.formatters import get_formatted_percentage
from stoqlib.domain.service import Service
from stoqlib.domain.product import Product, Storable, ProductManufacturer
from stoqlib.domain.person import ClientCategory

_ = stoqlib_gettext


class _SellableTaxConstantsListSlave(ModelListSlave):
    model_type = SellableTaxConstant
    editor_class = SellableTaxConstantEditor
    columns = [
        Column('description', _('Description'), data_type=str, expand=True),
        Column('value', _('Tax rate'), data_type=str, width=150),
    ]

    def selection_changed(self, constant):
        if constant is None:
            return
        is_custom = constant.tax_type == TaxType.CUSTOM
        self.listcontainer.remove_button.set_sensitive(is_custom)
        self.listcontainer.edit_button.set_sensitive(is_custom)

    def delete_model(self, model, store):
        sellables = store.find(Sellable, tax_constant=model)
        quantity = sellables.count()
        if quantity > 0:
            msg = _(u"You can't remove this tax, since %d products or "
                    "services are taxed with '%s'.") % (quantity,
                                                        model.get_description())
            info(msg)
        else:
            store.remove(model)

    def run_editor(self, store, model):
        if model and model.tax_type != TaxType.CUSTOM:
            return
        return self.run_dialog(self.editor_class, store=store, model=model)


class SellableTaxConstantsDialog(ModelListDialog):
    list_slave_class = _SellableTaxConstantsListSlave
    size = (500, 300)
    title = _("Taxes")


class CategoryPriceField(Field):
    title = _(u"Price Change Dialog")

    def __init__(self, category, validator):
        super(CategoryPriceField, self).__init__(data_type=currency,
                                                 validator=validator)
        # A cache for existing ClientCategoryPrices so that we don't have to
        # query all the time.
        self._cache = {}
        self.category = category
        self.label = _('{category} Price').format(category=category.get_description())

    def _get_category_info(self, sellable):
        if sellable.id in self._cache:
            return self._cache[sellable.id]

        self._cache[sellable.id] = sellable.get_category_price_info(self.category)
        return self._cache[sellable.id]

    def get_value(self, item):
        info = self._get_category_info(item.sellable)
        if info:
            return info.price

    def save_value(self, item):
        value = self.new_values[item]
        info = self._get_category_info(item.sellable)
        if not info:
            info = ClientCategoryPrice(sellable_id=item.sellable.id,
                                       category=self.category,
                                       price=value,
                                       store=item.store)
        else:
            info.price = value


class SellableView(Viewable):
    sellable = Sellable
    product = Product
    storable = Storable
    service = Service

    id = Sellable.id

    markup = Case(condition=(Sellable.cost == 0),
                  result=0,
                  else_=(Sellable.base_price / Sellable.cost - 1) * 100)

    # Be explict about the type to workaround an issue with storm
    need_price_update = Cast(Sellable.cost_last_updated > Sellable.price_last_updated,
                             'boolean')

    tables = [
        Sellable,
        LeftJoin(Service, Sellable.id == Service.id),
        LeftJoin(Product, Sellable.id == Product.id),
        LeftJoin(Storable, Sellable.id == Storable.id),
        LeftJoin(SellableCategory, SellableCategory.id == Sellable.category_id)
    ]


def validate_price(value):
    return value > 0


class SellableMassEditorDialog(MassEditorSearch):

    search_spec = SellableView

    def get_fields(self, store):
        # TODO: Add: status, max_discount
        default_fields = [
            # Sellable fields
            AccessorField(_('Code'), 'sellable', 'code', str, unique=True),
            AccessorField(_('Barcode'), 'sellable', 'barcode', str, unique=True),
            ReferenceField(_('Category'), 'sellable', 'category',
                           SellableCategory, 'description'),
            AccessorField(_('Description'), 'sellable', 'description', str),
            ReferenceField(_('Unit'), 'sellable', 'unit',
                           SellableUnit, 'description', visible=False),
            ReferenceField(_('C.F.O.P.'), 'sellable', 'default_sale_cfop',
                           CfopData, 'description', visible=False),

            # Sellable values
            AccessorField(_('Markup'), None, 'markup',
                          decimal.Decimal, read_only=True, visible=True,
                          format_func=get_formatted_percentage),
            AccessorField(_('Cost'), 'sellable', 'cost', currency,
                          validator=validate_price),
            AccessorField(_('Default Price'), 'sellable', 'base_price', currency,
                          validator=validate_price),
            AccessorField(_('On Sale Price'), 'sellable', 'on_sale_price', currency,
                          validator=validate_price),
            AccessorField(_('On Sale Start Date'), 'sellable', 'on_sale_start_date',
                          datetime.date),
            AccessorField(_('On Sale End Date'), 'sellable', 'on_sale_end_date',
                          datetime.date),

            # Cost and price update time
            AccessorField(_('Need Price Update'), None, 'need_price_update',
                          bool, read_only=True, visible=False),
            AccessorField(_('Cost Last Updated'), 'sellable', 'cost_last_updated',
                          datetime.date, read_only=True, visible=False),
            AccessorField(_('Price Last Updated'), 'sellable', 'price_last_updated',
                          datetime.date, read_only=True, visible=False),

            # Product Fields
            AccessorField(_('NCM'), 'product', 'ncm', str, visible=False),
            AccessorField(_('Location'), 'product', 'location', str, visible=False),
            AccessorField(_('Brand'), 'product', 'brand', str, visible=False),
            AccessorField(_('Family'), 'product', 'family', str, visible=False),
            AccessorField(_('Model'), 'product', 'model', str, visible=False),
            AccessorField(_('Width'), 'product', 'width', decimal.Decimal, visible=False),
            AccessorField(_('Height'), 'product', 'height', decimal.Decimal, visible=False),
            AccessorField(_('Depth'), 'product', 'depth', decimal.Decimal, visible=False),
            AccessorField(_('Weight'), 'product', 'weight', decimal.Decimal, visible=False),

            ReferenceField(_('Manufacturer'), 'product', 'manufacturer',
                           ProductManufacturer, 'name', visible=False),

            # Service Fields
            AccessorField(_('Service List Item Code'), 'service', 'service_list_item_code',
                          str, visible=False),
            AccessorField(_('City Taxation Code'), 'service', 'city_taxation_code',
                          str, visible=False),
            AccessorField(_('ISS Aliquot'), 'service', 'p_iss', decimal.Decimal, visible=False),
        ]

        category_fields = []
        self.categories = store.find(ClientCategory)
        for cat in self.categories:
            category_fields.append(CategoryPriceField(cat,
                                                      validator=validate_price))

        return default_fields + category_fields

    def get_items(self, store):
        return store.find(SellableView).order_by(Sellable.code)


if __name__ == '__main__':
    from stoq.lib.gui.base.dialogs import run_dialog
    ec = api.prepare_test()
    retval = run_dialog(SellableMassEditorDialog, None, ec.store)
    if retval:
        ec.store.commit()
    print('RETVAL', retval)
