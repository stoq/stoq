#!/usr/bin/env python
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
""" Create product objects for an example database.

    Remember that this script must always be called after
    examples/person.py, oterwise the stocks won't be created properly.
"""


import random

from stoqdrivers.constants import UNIT_CUSTOM

from stoqlib.domain.product import Product, ProductSupplierInfo
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import ISellable, IStorable, ISupplier
from stoqlib.domain.sellable import (BaseSellableCategory,
                                     SellableCategory,
                                     AbstractSellableCategory,
                                     BaseSellableInfo, SellableUnit)
from stoqlib.lib.runtime import new_transaction, print_msg


MAX_PRODUCT_NUMBER = 4

PRICE_RANGE = 100, 200
QUANTITY_RANGE = 1, 50
COST_RANGE = 1, 99

MARKUP_RANGE = 30, 80
COMMISION_RANGE = 1, 40


def get_commission_and_markup():
    commission = round(random.uniform(*COMMISION_RANGE), 2)
    markup = round(random.uniform(*MARKUP_RANGE), 2)
    return commission, markup

def create_products():
    print_msg('Creating products...', break_line=False)
    conn = new_transaction()

    base_category_data= ['Keyboard',
                         'Mouse',
                         'Monitor',
                         'Processor']

    category_data = ['Generic',
                     'Optical',
                     'LCD',
                     'AMD Durom']

    codes = ['K15', 'M73', 'M025', 'P83']

    descriptions = ['Keyboard AXDR', 'Optical Mouse 45FG',
                    'Monitor LCD SXDF', 'Processor AMD Durom 1.2Ghz']

    supplier_table = Person.getAdapterClass(ISupplier)
    suppliers = supplier_table.select(connection=conn)
    if suppliers.count() < MAX_PRODUCT_NUMBER:
        raise ValueError('You must have at least four suppliers on your '
                         'database at this point.')

    units = SellableUnit.select(connection=conn)
    if units.count() < MAX_PRODUCT_NUMBER:
        SellableUnit(connection=conn, description='Cx', index=UNIT_CUSTOM)
        units = SellableUnit.select(connection=conn)

    # Creating products and facets
    for index in range(MAX_PRODUCT_NUMBER):
        product_obj = Product(connection=conn)

        # Adding a main supplier for the product recently created
        supplier = suppliers[index]
        supplier_info = ProductSupplierInfo(connection=conn,
                                            supplier=supplier,
                                            is_main_supplier=True,
                                            product=product_obj)

        base_cat_desc = base_category_data[index]
        commission, markup = get_commission_and_markup()
        table = AbstractSellableCategory
        abstract_data = table(connection=conn, suggested_markup=markup,
                              salesperson_commission=commission,
                              description=base_cat_desc)

        base_cat = BaseSellableCategory(connection=conn,
                                        category_data=abstract_data)

        cat_desc = category_data[index]
        commission, markup = get_commission_and_markup()
        table = AbstractSellableCategory
        abstract_data = table(connection=conn, description=cat_desc,
                              salesperson_commission=commission,
                              suggested_markup=markup)

        cat = SellableCategory(connection=conn,
                               base_category=base_cat,
                               category_data=abstract_data)

        description = descriptions[index]
        price = random.randrange(*PRICE_RANGE)
        sellable_info = BaseSellableInfo(connection=conn,
                                         description=description,
                                         price=price)

        cost = random.randrange(*COST_RANGE)
        code = codes[index]
        unit = units[index]

        product_obj.addFacet(ISellable, connection=conn, category=cat,
                             code=code, cost=cost, unit=unit,
                             base_sellable_info=sellable_info)

        storable = product_obj.addFacet(IStorable, connection=conn)

        # Setting a initial value for Stocks
        for stock_item in storable.get_stocks():
            stock_item.quantity = random.randint(*QUANTITY_RANGE)
            stock_item.stock_cost = random.randrange(*COST_RANGE)
            stock_item.logic_quantity = stock_item.quantity * 2

    conn.commit()
    print_msg('done.')


if __name__ == "__main__":
    create_products()
