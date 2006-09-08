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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
""" Create product objects for an example database.

    Remember that this script must always be called after
    examples/person.py, oterwise the stocks won't be created properly.
"""


from stoqdrivers.constants import UNIT_CUSTOM

from stoqlib.domain.examples import log
from stoqlib.domain.product import Product, ProductSupplierInfo
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import ISellable, IStorable, ISupplier
from stoqlib.domain.sellable import (BaseSellableCategory,
                                     SellableCategory,
                                     SellableUnit,
                                     BaseSellableInfo)
from stoqlib.lib.runtime import new_transaction


MAX_PRODUCT_NUMBER = 4

def create_products():
    log.info('Creating products')
    trans = new_transaction()

    base_category_data = ['Keyboard',
                          'Mouse',
                          'Monitor',
                          'Processor']

    barcodes = ['015432', '32587', '65742', '12478']

    category_data = ['Generic',
                     'Optical',
                     'LCD',
                     'AMD Durom']

    descriptions = ['Keyboard AXDR', 'Optical Mouse 45FG',
                    'Monitor LCD SXDF', 'Processor AMD Durom 1.2Ghz']

    prices = [100, 121, 150, 104] # (100, 200]
    quantites = [40, 1, 38, 46] # (1, 50]
    costs = [87, 71, 9, 45] # (1, 99]
    stock_costs = [90, 10, 60, 87] # (1, 99]
    commissions = [13, 4, 17, 27] # (1, 40]
    commissions2 = [27, 16, 23, 13] # (1, 40]
    markups = [44, 43, 78, 32] # (30, 80]
    markups2 = [36, 33, 67, 52] # (30, 80]

    supplier_table = Person.getAdapterClass(ISupplier)
    suppliers = supplier_table.select(connection=trans)
    if suppliers.count() < MAX_PRODUCT_NUMBER:
        raise ValueError('You must have at least four suppliers on your '
                         'database at this point.')

    units = SellableUnit.select(connection=trans)
    if units.count() < MAX_PRODUCT_NUMBER:
        SellableUnit(connection=trans, description='Cx', index=UNIT_CUSTOM)
        units = SellableUnit.select(connection=trans)

    # Creating products and facets
    for index in range(MAX_PRODUCT_NUMBER):
        product_obj = Product(connection=trans)

        # Adding a main supplier for the product recently created
        supplier = suppliers[index]
        supplier_info = ProductSupplierInfo(connection=trans,
                                            supplier=supplier,
                                            is_main_supplier=True,
                                            product=product_obj)

        base_cat_desc = base_category_data[index]
        commission = commissions[index]
        markup = markups[index]
        base_cat = BaseSellableCategory(suggested_markup=markup,
                                        salesperson_commission=commission,
                                        description=base_cat_desc,
                                        connection=trans)

        cat_desc = category_data[index]
        commission = commissions2[index]
        markup = markups2[index]
        cat = SellableCategory(description=cat_desc,
                               salesperson_commission=commission,
                               suggested_markup=markup,
                               base_category=base_cat,
                               connection=trans)

        description = descriptions[index]
        price = prices[index]
        sellable_info = BaseSellableInfo(connection=trans,
                                         description=description,
                                         price=price)

        cost = costs[index]
        unit = units[index]
        barcode = barcodes[index]

        product_obj.addFacet(ISellable, connection=trans, category=cat,
                             cost=cost, unit=unit, barcode=barcode,
                             base_sellable_info=sellable_info)

        storable = product_obj.addFacet(IStorable, connection=trans)

        # Setting a initial value for Stocks
        for stock_item in storable.get_stocks():
            stock_item.quantity = quantites[index]
            stock_item.stock_cost = stock_costs[index]
            stock_item.logic_quantity = stock_item.quantity * 2

    trans.commit()


if __name__ == "__main__":
    create_products()
