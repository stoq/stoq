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
from kiwi.currency import currency
from kiwi.ui.objectlist import Column
from storm.expr import LeftJoin
from stoqdrivers.enum import TaxType

from stoqlib.api import api
from stoqlib.domain.sellable import (Sellable, ClientCategoryPrice,
                                     SellableUnit, SellableCategory,
                                     SellableTaxConstant)
from stoqlib.domain.fiscal import CfopData
from stoqlib.gui.base.lists import ModelListDialog, ModelListSlave
from stoqlib.gui.editors.sellableeditor import SellableTaxConstantEditor
from stoqlib.gui.dialogs.masseditordialog import (Field, MassEditorSearch,
                                                  AccessorField, ReferenceField)
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.message import info
from stoqlib.database.viewable import Viewable
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
            AccessorField(_('Code'), 'sellable', 'code', unicode, unique=True),
            AccessorField(_('Barcode'), 'sellable', 'barcode', unicode, unique=True),
            ReferenceField(_('Category'), 'sellable', 'category',
                           SellableCategory, 'description'),
            AccessorField(_('Description'), 'sellable', 'description', unicode),
            ReferenceField(_('Unit'), 'sellable', 'unit',
                           SellableUnit, 'description', visible=False),
            ReferenceField(_('C.F.O.P.'), 'sellable', 'default_sale_cfop',
                           CfopData, 'description', visible=False),

            # Sellable values
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

            # Product Fields
            AccessorField(_('NCM'), 'product', 'ncm', unicode, visible=False),
            AccessorField(_('Location'), 'product', 'location', unicode, visible=False),
            AccessorField(_('Brand'), 'product', 'brand', unicode, visible=False),
            AccessorField(_('Family'), 'product', 'family', unicode, visible=False),
            AccessorField(_('Model'), 'product', 'model', unicode, visible=False),

            ReferenceField(_('Manufacturer'), 'product', 'manufacturer',
                           ProductManufacturer, 'name', visible=False),
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
    from stoqlib.gui.base.dialogs import run_dialog
    ec = api.prepare_test()
    retval = run_dialog(SellableMassEditorDialog, None, ec.store)
    if retval:
        ec.store.commit()
    print('RETVAL', retval)
