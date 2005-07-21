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
tests/transactions.py:

    Testing multiple transactions behavior instantiating main domain 
    objects.
"""

from stoq.lib import i18n
from stoq.domain.person import Person, PersonAdaptToCompany
from stoq.domain.service import Service, ServiceAdaptToSellable
from stoq.domain.product import (Product, ProductAdaptToSellable,
                                 ProductAdaptToStockItem)
from stoq.domain.interfaces import (ISellable, ISellableItem, 
                                    ICompany, ISupplier, 
                                    IBranch, IStockItem,
                                    IStorable, IClient, 
                                    IIndividual)
from stoq.domain.sellable import AbstractSellable
from stoq.lib.runtime import new_transaction

def test_services():
    print '>> testing service module...'

    trans = new_transaction()
    
    service1 = Service(connection=trans)
    service1.addFacet(ISellable, code=23, price=34.87, 
                      description='This is a test service', 
                      connection=trans)

    service2 = Service(notes='Cleanness', connection=trans)
    service2.addFacet(ISellable, code=25, price=24.11, 
                      description='Generic service', 
                      connection=trans)

    service3 = Service(notes='Generic service', connection=trans)
    service3.addFacet(ISellable, code=29, price=122.96, 
                      description='Cleanness', 
                      connection=trans)
    trans.commit()
    print '>> searching...'
    print '>> len services: '
    print Service.select().count()
    print '>> len sellable services: '
    print ServiceAdaptToSellable.select().count()

    print '='*40
    print 'done.'
    
def test_products():
    print '>> testing product module...'

    trans = new_transaction()
    trans2 = new_transaction()
    trans3 = new_transaction()
    
    # First transaction
    product_obj = Product(notes='This is a test product', connection=trans)
    product_obj.addFacet(ISellable, code=111, price=75.99, 
                                      description='Dell computer',
                                      connection=trans)
    storable = product_obj.addFacet(IStorable, connection=trans)
    storable.fill_stocks()
    trans.commit()
    
    # Second transaction
    product_obj2 = Product(notes='Another test product', connection=trans2)
    storable = product_obj2.addFacet(IStorable, connection=trans2)
    storable.fill_stocks()

    sellablep = product_obj2.addFacet(ISellable, code=51, price=25.5, 
                                      description='Keyboard MTek',
                                      connection=trans2)
    trans2.commit()


    # Third transaction
    sellabe_item = product_obj.addFacet(ISellableItem, price=5.5, 
                                        quantity=1.0, base_price=2.2,
                                        connection=trans3)
    trans3.commit()
    print '>> sellable item: '
    print sellabe_item
    

    print '>> searching...'
    print '>> len products: '
    print Product.select().count()
    print '>> len abstract sellable: '
    print AbstractSellable.select().count()

    print '>> using an abstract sellable'
    query = "child_name = 'ProductAdaptToSellable'"
    item = AbstractSellable.select(query)[0]
    s = ProductAdaptToSellable.select("""id = %d""" % item.id)
    print 'sellable object: ', s[0]

    print '='*40
    print 'done.'


def test_person_and_stock():
    print '>> testing person and stock modules...'

    trans = new_transaction()
    trans2 = new_transaction()



    #
    # Persons job - using transaction = trans
    #

    

    person_obj = Person(name='John Wayne', connection=trans)
    person_obj.addFacet(ICompany, cnpj='222', connection=trans)
    person_obj.addFacet(IIndividual, connection=trans)
    person_obj.addFacet(IClient, connection=trans)
    supplier = person_obj.addFacet(ISupplier, connection=trans)
    person_obj.addFacet(IBranch, connection=trans)

    print '>> Company and Supplier: '
    print ICompany(person_obj)
    print ISupplier(person_obj)

    branch = IBranch(person_obj)
    branch.setConnection(trans)
    print '>> branch: '
    print branch

    # More persons for a better initial database
    person_obj = Person(name='Michael Caine', connection=trans)
    person_obj.addFacet(ICompany, cnpj='987262', connection=trans)
    person_obj.addFacet(IIndividual, connection=trans)
    person_obj.addFacet(ISupplier, connection=trans)
    person_obj.addFacet(IClient, connection=trans)

    person_obj = Person(name='Adolf Hitler', connection=trans)
    person_obj.addFacet(IIndividual, connection=trans)
    person_obj.addFacet(ICompany, cnpj='2133', connection=trans)
    person_obj.addFacet(ISupplier, connection=trans)
    person_obj.addFacet(IClient, connection=trans)

    person_obj = Person(name='Mickey Mouse', connection=trans)
    person_obj.addFacet(IIndividual, connection=trans)
    person_obj.addFacet(ICompany, cnpj='09822', connection=trans)
    person_obj.addFacet(ISupplier, connection=trans)
    person_obj.addFacet(IClient, connection=trans)
    trans.commit()



    #
    # Products job - using transaction = trans2
    #

    

    product_obj = Product(notes='Testing product for person module', 
                          connection=trans2)
    product_obj.addFacet(ISellable, code=21, price=9.77, 
                         description='Scanner XTR', connection=trans2)
    stock_item2 = product_obj.addFacet(IStockItem, branch=branch,
                                       stock_cost=50.25, quantity=1.1, 
                                       connection=trans2)
    print '>> stock item: '
    print stock_item2
    print '>> len of person table: '
    print Person.select(connection=trans2).count()
    table = PersonAdaptToCompany
    print '>> len of company table: '
    print table.select(connection=trans2).count()


    storable = product_obj.addFacet(IStorable, connection=trans2)
    storable.fill_stocks()
    print '>> type of storable object: '
    print type(storable)



    trans2.commit()

    print '>> searching...'
    table = ProductAdaptToStockItem
    values = table.select(connection=trans2)
    print '>> len product stock item: '
    print values.count()
    item = values[0]
    print '>> accessing some attributes of product stock item: '
    print 'quantity: %s and stock_cost: %s' % (item.quantity, \
                                               item.stock_cost)
    print ">> ... and this is pretty interesting, getting a foreing key " \
          "field as an object: "
    print 'branch: %s, branch type: %s ' % (item.branch, type(item.branch))

    print '>> Looking for the stock references of a product:'
    print 'stocks: ', [s for s in storable.get_stocks()]

    print '='*40
    print 'done.'

if __name__ == "__main__":
    test_person_and_stock()
    test_products()
    test_services()

