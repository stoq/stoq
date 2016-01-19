# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2008 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

from decimal import Decimal

from stoqlib.database.runtime import get_default_store
from stoqlib.domain.commission import CommissionSource
from stoqlib.domain.person import Supplier
from stoqlib.domain.product import (Product, ProductSupplierInfo,
                                    Storable)
from stoqlib.domain.sellable import (Sellable,
                                     SellableCategory,
                                     SellableUnit)
from stoqlib.importers.csvimporter import CSVImporter
from stoqlib.lib.parameters import sysparam


class ProductImporter(CSVImporter):
    fields = ['base_category',
              'barcode',
              'category',
              'description',
              'price',
              'cost',
              'commission',
              'commission2',
              'markup',
              'markup2'
              ]

    optional_fields = [
        'unit',
    ]

    def __init__(self):
        super(ProductImporter, self).__init__()
        default_store = get_default_store()
        suppliers = default_store.find(Supplier)
        if not suppliers.count():
            raise ValueError(u'You must have at least one suppliers on your '
                             u'database at this point.')
        self.supplier = suppliers[0]

        self.units = {}
        for unit in default_store.find(SellableUnit):
            self.units[unit.description] = unit

        self.tax_constant_id = sysparam.get_object_id(
            'DEFAULT_PRODUCT_TAX_CONSTANT')
        self._code = 1

    def _get_or_create(self, table, store, **attributes):
        obj = store.find(table, **attributes).one()
        if obj is None:
            obj = table(store=store, **attributes)
        return obj

    def process_one(self, data, fields, store):
        base_category = self._get_or_create(
            SellableCategory, store,
            suggested_markup=Decimal(data.markup),
            salesperson_commission=Decimal(data.commission),
            category=None,
            description=data.base_category)

        # create a commission source
        self._get_or_create(
            CommissionSource, store,
            direct_value=Decimal(data.commission),
            installments_value=Decimal(data.commission2),
            category=base_category)

        category = self._get_or_create(
            SellableCategory, store,
            description=data.category,
            suggested_markup=Decimal(data.markup2),
            category=base_category)

        sellable = Sellable(store=store,
                            cost=Decimal(data.cost),
                            category=category,
                            description=data.description,
                            price=Decimal(data.price))
        sellable.barcode = data.barcode
        sellable.code = u'%02d' % self._code
        self._code += 1
        if u'unit' in fields:
            if not data.unit in self.units:
                raise ValueError(u"invalid unit: %s" % data.unit)
            sellable.unit = store.fetch(self.units[data.unit])
        sellable.tax_constant_id = self.tax_constant_id

        product = Product(sellable=sellable, store=store)

        supplier = store.fetch(self.supplier)
        ProductSupplierInfo(store=store,
                            supplier=supplier,
                            is_main_supplier=True,
                            base_cost=Decimal(data.cost),
                            product=product)
        Storable(product=product, store=store)
