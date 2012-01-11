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

from stoqlib.database.runtime import get_connection
from stoqlib.domain.commission import CommissionSource
from stoqlib.domain.product import Product, ProductSupplierInfo
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import IStorable, ISupplier
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
        conn = get_connection()
        suppliers = Person.iselect(ISupplier, connection=conn)
        if not suppliers.count():
            raise ValueError('You must have at least one suppliers on your '
                             'database at this point.')
        self.supplier = suppliers[0]

        self.units = {}
        for unit in SellableUnit.select(connection=conn):
            self.units[unit.description] = unit

        self.tax_constant = sysparam(conn).DEFAULT_PRODUCT_TAX_CONSTANT

    def _get_or_create(self, table, trans, **attributes):
        obj = table.selectOneBy(connection=trans, **attributes)
        if obj is None:
            obj = table(connection=trans, **attributes)
        return obj

    def process_one(self, data, fields, trans):
        base_category = self._get_or_create(
            SellableCategory, trans,
            suggested_markup=int(data.markup),
            salesperson_commission=int(data.commission),
            category=None,
            description=data.base_category)

        # create a commission source
        self._get_or_create(
            CommissionSource, trans,
            direct_value=int(data.commission),
            installments_value=int(data.commission2),
            category=base_category)

        category = self._get_or_create(
            SellableCategory, trans,
            description=data.category,
            suggested_markup=int(data.markup2),
            category=base_category)

        if 'unit' in fields:
            if not data.unit in self.units:
                raise ValueError("invalid unit: %s" % data.unit)
            unit = self.units[data.unit]
        else:
            unit = None
        sellable = Sellable(connection=trans,
                            cost=float(data.cost),
                            code=data.barcode,
                            barcode=data.barcode,
                            category=category,
                            description=data.description,
                            price=int(data.price),
                            unit=unit,
                            tax_constant=self.tax_constant)
        product = Product(sellable=sellable, connection=trans)

        ProductSupplierInfo(connection=trans,
                            supplier=self.supplier,
                            is_main_supplier=True,
                            base_cost=float(data.cost),
                            product=product)
        product.addFacet(IStorable, connection=trans)
