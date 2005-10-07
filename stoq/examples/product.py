#!/usr/bin/env python
# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
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
"""
stoq/examples/products.py:

    Create product objects for an example database.

    Remember that this script must always be called after
    examples/person.py, oterwise the stocks won't be created properly.
"""

from stoq.domain.product import Product, ProductSupplierInfo
from stoq.domain.person import Person
from stoq.domain.interfaces import ISellable, IStorable, ISupplier
from stoq.domain.sellable import (BaseSellableCategory,
                                  SellableCategory,
                                  AbstractSellableCategory)
from stoq.lib.runtime import new_transaction


MAX_PRODUCTS_NUMBER = 4
    
def create_products():
    print 'Creating products...'
    trans = new_transaction()

    base_category_data= [dict(description='Keyboard', 
                              suggested_markup=25.5,
                              salesperson_comission=31.7),
                         dict(description='Mouse', 
                              suggested_markup=15.5,
                              salesperson_comission=32.7),
                         dict(description='Monitor', 
                              suggested_markup=26.5,
                              salesperson_comission=33.7),
                         dict(description='Processor', 
                              suggested_markup=29.5,
                              salesperson_comission=39.7)]

    category_data = [dict(description='Generic', 
                          suggested_markup=1.4,
                          salesperson_comission=30.9),
                     dict(description='Optical', 
                          suggested_markup=2.4,
                          salesperson_comission=31.9),
                     dict(description='LCD', 
                          suggested_markup=3.4,
                          salesperson_comission=32.9),
                     dict(description='AMD Durom', 
                          suggested_markup=7.4,
                          salesperson_comission=36.9)]

    sellable_data = [dict(code='K15',
                          description='Keyboard AXDR', 
                          price=99.9),
                     dict(code='M73',
                          description='Optical Mouse 45FG', 
                          price=39.5),
                     dict(code='MO25',
                          description='Monitor LCD SXDF', 
                          price=435.7),
                     dict(code='P83',
                          description='Processor AMD Durom 1.2Ghz', 
                          price=877.22)]

    supplier_table = Person.getAdapterClass(ISupplier)
    suppliers = supplier_table.select(connection=trans)
    if suppliers.count() < MAX_PRODUCTS_NUMBER:
        raise ValueError('You must have at least four suppliers on your '
                         'database at this point.')


    # Creating products and facets
    value = 10.0
    for index in range(MAX_PRODUCTS_NUMBER):
        product_obj = Product(connection=trans)

        # Adding a main supplier for the product recently created
        supplier = suppliers[index]
        supplier_info = ProductSupplierInfo(connection=trans,
                                            supplier=supplier,
                                            is_main_supplier=True, 
                                            product=product_obj)
        
        base_cat_args = base_category_data[index]
        abstract_data = AbstractSellableCategory(connection=trans,
                                                 **base_cat_args)
        base_cat = BaseSellableCategory(connection=trans,
                                        category_data=abstract_data)
        cat_args = category_data[index] 
        abstract_data = AbstractSellableCategory(connection=trans,
                                                 **cat_args)
        cat = SellableCategory(connection=trans,
                               base_category=base_cat,
                               category_data=abstract_data)

        sellable_args = sellable_data[index]
        product_obj.addFacet(ISellable, connection=trans,
                             category=cat,
                             **sellable_args)

        storable = product_obj.addFacet(IStorable, connection=trans)

        # Setting a initial value for Stocks
        for stock_item in storable.get_stocks():
            stock_item.quantity = value
            stock_item.stock_cost = value * 5
            stock_item.logic_quantity = value * 2
            value += 3
        
    trans.commit()
    print 'done.'


if __name__ == "__main__":
    create_products()
