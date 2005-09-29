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
## Author(s):        Henrique Romano <henrique@async.com.br>
##
"""
stoq/examples/sale.py

    Create a simple sale to an example database.
"""

import gettext
import sys
from datetime import datetime, timedelta

from stoqlib.exceptions import SellError

from stoq.lib.runtime import new_transaction
from stoq.domain.till import get_current_till_operation, Till
from stoq.domain.payment import Payment
from stoq.domain.sale import Sale
from stoq.domain.product import Product
from stoq.domain.interfaces import ISellable, IClient, IPaymentGroup
from stoq.domain.person import Person
from stoq.lib.parameters import sysparam

_ = gettext.gettext

# Number of installments for the sale
DEFAULT_PAYMENTS_NUMBER = 4

# Interval between payments (in days)
DEFAULT_PAYMENTS_INTERVAL = 30

# Number of sales to be created
DEFAULT_SALE_NUMBER = 4

def get_till(conn):
    till = get_current_till_operation(conn)
    if till is None:
        till = Till(connection=conn, 
                    branch=sysparam(conn).CURRENT_BRANCH)
        till.open_till()

    return till

def get_clients(conn):
    client_table = Person.getAdapterClass(IClient)
    result = client_table.select(connection=conn)
    if result.count() <= 0:
        raise SellError("You must have clients to create a sale!")
    return list(result)

def get_all_products(conn):
    result = Product.select(connection=conn)
    if result.count() <= 0:
        raise SellError("You have nothing to sale!")
        sys.exit()
    return list(result)

#
# Main
#

def create_sales():
    conn = new_transaction()
    print "Creating Sale... ",

    till = get_till(conn)

    clients = get_clients(conn)
    if not len(clients) >= DEFAULT_SALE_NUMBER:
        raise SellError("You don't have clients to create all the sales.")

    product_list = get_all_products(conn)
    if not len(product_list) >= DEFAULT_SALE_NUMBER:
        raise SellError("You don't have products to create all the sales.")

    payment_method = sysparam(conn).MONEY_PAYMENT_METHOD

    for i in range(DEFAULT_SALE_NUMBER):
        #
        # Setting up the items
        #
        sale = Sale(connection=conn, till=till, client=clients[i], 
                    code='#%03d' % (i + 1))
        sellable_facet = ISellable(product_list[i], connection=conn)
        sellable_facet.add_sellable_item(sale=sale)

        sale.total = sellable_facet.price

        #
        # Setting up the payments
        #
        pg_facet = sale.addFacet(IPaymentGroup, connection=conn,
                                 thirdparty=clients[i].get_adapted())
        each_payment = sale.total / DEFAULT_PAYMENTS_NUMBER
        due_date = datetime.now()
        for i in range(DEFAULT_PAYMENTS_NUMBER):
            payment = Payment(due_date=due_date, value=each_payment,
                              connection=conn,method=payment_method,
                              group=pg_facet)
            pg_facet.add_item(payment)
            due_date += timedelta(days=DEFAULT_PAYMENTS_INTERVAL)

    conn.commit()

    print "done."


if __name__ == '__main__':
    create_sales()

