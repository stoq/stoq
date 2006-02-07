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
import datetime

from stoqlib.exceptions import SellError
from stoqlib.lib.defaults import INTERVALTYPE_MONTH

from stoqlib.lib.runtime import new_transaction, print_msg
from stoqlib.lib.parameters import sysparam
from stoq.examples.payment import MAX_INSTALLMENTS_NUMBER
from stoqlib.domain.till import get_current_till_operation, Till
from stoqlib.domain.sale import Sale
from stoqlib.domain.product import Product
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import (ISellable, IClient, IPaymentGroup,
                                    ISalesPerson, ICheckPM)

_ = gettext.gettext

# Number of installments for the sale
DEFAULT_PAYMENTS_NUMBER = 4

# Interval between payments (in days)
DEFAULT_PAYMENTS_INTERVAL = 30

# Number of sales to be created
DEFAULT_SALE_NUMBER = 4

DEFAULT_PAYMENT_INTERVAL_TYPE = INTERVALTYPE_MONTH
DEFAULT_PAYMENT_INTERVALS = 1

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
    print_msg("Creating sales... ", break_line=False)

    till = get_till(conn)

    clients = get_clients(conn)
    if not len(clients) >= DEFAULT_SALE_NUMBER:
        raise SellError("You don't have clients to create all the sales.")

    product_list = get_all_products(conn)
    if not len(product_list) >= DEFAULT_SALE_NUMBER:
        raise SellError("You don't have products to create all the sales.")

    destination = sysparam(conn).DEFAULT_PAYMENT_DESTINATION
    salesperson_table = Person.getAdapterClass(ISalesPerson)
    salespersons = salesperson_table.select(connection=conn)
    qty = salespersons.count()
    if qty < DEFAULT_SALE_NUMBER:
        raise ValueError('You should have at last %d salespersons defined '
                         'in database at this point, got %d instead' % 
                         (DEFAULT_SALE_NUMBER, qty))

    open_dates = [datetime.datetime.today(),
                  datetime.datetime.today() + datetime.timedelta(10),
                  datetime.datetime.today() + datetime.timedelta(15),
                  datetime.datetime.today() + datetime.timedelta(23)]

    installments_numbers = [i * 2 for i in range(1, 
                                                 DEFAULT_SALE_NUMBER + 1)]
    
    statuses = Sale.statuses.keys()
    method = sysparam(conn).BASE_PAYMENT_METHOD
    check_method = ICheckPM(method, connection=conn)
                 
    # We need to increment payment_id attribute automatically. Waiting
    # for SQLObject support
    payment_id = 1
    for index in range(DEFAULT_SALE_NUMBER):
        
        #
        # Setting up the sale
        #
        
        open_date = open_dates[index]
        status = statuses[index]
        salesperson = salespersons[index]
        sale = Sale(connection=conn, till=till, client=clients[index], 
                    order_number='#%03d' % (index + 1), status=status,
                    open_date=open_date, salesperson=salesperson)
        sellable_facet = ISellable(product_list[index], connection=conn)
        sellable_facet.add_sellable_item(sale=sale)
        sale_total = sellable_facet.base_sellable_info.price

        #
        # Setting up the payments
        #

        pg_facet = sale.addFacet(IPaymentGroup, connection=conn,
                                 installments_number=DEFAULT_PAYMENTS_NUMBER)
        installments = installments_numbers[index]
        if installments > MAX_INSTALLMENTS_NUMBER:
            raise ValueError('Number of installments for this payment '
                             'method can not be greater than %d, got %d' 
                             % (installments, MAX_INSTALLMENTS_NUMBER))
        check_method.setup_inpayments(pg_facet, installments, open_date,
                                      DEFAULT_PAYMENT_INTERVAL_TYPE,
                                      DEFAULT_PAYMENTS_INTERVAL, 
                                      sale_total)
        sale.set_valid()

    conn.commit()
    print_msg("done.")

if __name__ == '__main__':
    create_sales()

