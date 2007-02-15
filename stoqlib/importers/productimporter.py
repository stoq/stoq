# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source
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
## Author(s):       Johan Dahlin                <jdahlin@async.com.br>
##
##

from stoqlib.database.runtime import get_connection
from stoqlib.domain.product import Product, ProductSupplierInfo
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import ISellable, IStorable, ISupplier
from stoqlib.domain.sellable import (BaseSellableCategory,
                                     SellableCategory,
                                     SellableUnit,
                                     BaseSellableInfo)
from stoqlib.importers.csvimporter import CSVImporter

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
        conn = get_connection()
        suppliers = Person.iselect(ISupplier, connection=conn)
        if not suppliers.count():
            raise ValueError('You must have at least one suppliers on your '
                             'database at this point.')
        self.supplier = suppliers[0]

        self.units = {}
        for unit in SellableUnit.select(connection=conn):
            self.units[unit.description] = unit

    def process_one(self, data, fields, trans):
        product = Product(connection=trans)

        ProductSupplierInfo(connection=trans,
                            supplier=self.supplier,
                            is_main_supplier=True,
                            product=product)

        base_category = BaseSellableCategory(
            suggested_markup=data.markup,
            salesperson_commission=data.commission,
            description=data.base_category,
            connection=trans)

        category = SellableCategory(
            description=data.category,
            salesperson_commission=data.commission2,
            suggested_markup=data.markup2,
            base_category=base_category,
            connection=trans)

        sellable_info = BaseSellableInfo(
            connection=trans,
            description=data.description,
            price=data.price)

        if 'unit' in fields:
            if not data.unit in self.units:
                raise ValueError("invalid unit: %s" % data.unit)
            unit = self.units[data.unit]
        else:
            unit = None
        product.addFacet(
            ISellable, connection=trans,
            cost=data.cost,
            barcode=data.barcode,
            category=category,
            base_sellable_info=sellable_info,
            unit=unit)
        product.addFacet(IStorable, connection=trans)
