#!/usr/bin/env python
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
"""
stoq/examples/products.py:

    Create product objects for an example database.

    Remember that this script must always be called after
    examples/person.py, oterwise the stocks won't be created properly.
"""


import random

from stoq.domain.product import Product, ProductSupplierInfo
from stoq.domain.person import Person
from stoq.domain.interfaces import ISellable, IStorable, ISupplier
from stoq.domain.sellable import (BaseSellableCategory,
                                  SellableCategory,
                                  AbstractSellableCategory)
from stoq.lib.runtime import new_transaction, print_msg


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
    trans = new_transaction()

    base_category_data= ['Keyboard', 
                         'Mouse', 
                         'Monitor', 
                         'Processor']

    category_data = ['Generic', 
                     'Optical', 
                     'LCD', 
                     'AMD Durom']

    sellable_data = [dict(code='K15',
                          description='Keyboard AXDR'), 
                     dict(code='M73',
                          description='Optical Mouse 45FG'), 
                     dict(code='MO25',
                          description='Monitor LCD SXDF'), 
                     dict(code='P83',
                          description='Processor AMD Durom 1.2Ghz')]

    supplier_table = Person.getAdapterClass(ISupplier)
    suppliers = supplier_table.select(connection=trans)
    if suppliers.count() < MAX_PRODUCT_NUMBER:
        raise ValueError('You must have at least four suppliers on your '
                         'database at this point.')


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
        commission, markup = get_commission_and_markup()
        table = AbstractSellableCategory
        abstract_data = table(connection=trans, suggested_markup=markup,
                              salesperson_comission=commission,
                              description=base_cat_desc)

        base_cat = BaseSellableCategory(connection=trans,
                                        category_data=abstract_data)

        cat_desc = category_data[index] 
        commission, markup = get_commission_and_markup()
        table = AbstractSellableCategory
        abstract_data = table(connection=trans, description=cat_desc,
                              salesperson_comission=commission,
                              suggested_markup=markup)

        cat = SellableCategory(connection=trans,
                               base_category=base_cat,
                               category_data=abstract_data)

        sellable_args = sellable_data[index]
        price = random.randrange(*PRICE_RANGE)
        cost = random.randrange(*COST_RANGE)
        product_obj.addFacet(ISellable, connection=trans, category=cat, 
                             price=price, cost=cost, **sellable_args)

        storable = product_obj.addFacet(IStorable, connection=trans)

        # Setting a initial value for Stocks
        for stock_item in storable.get_stocks():
            stock_item.quantity = random.randint(*QUANTITY_RANGE)
            stock_item.stock_cost = random.randrange(*COST_RANGE)
            stock_item.logic_quantity = stock_item.quantity * 2
        
    trans.commit()
    print_msg('done.')


if __name__ == "__main__":
    create_products()
