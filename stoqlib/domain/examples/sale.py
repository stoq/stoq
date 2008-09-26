# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2008 Async Open Source <http://www.async.com.br>
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
## Author(s):        Henrique Romano <henrique@async.com.br>
##                   Johan Dahlin    <jdahlin@async.com.br>
##
""" Create a simple sale to an example database"""

import datetime
import sys

from stoqlib.database.runtime import (new_transaction,
                                      get_current_station, get_current_branch)
from stoqlib.domain.examples import log
from stoqlib.domain.interfaces import IClient, ISalesPerson
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.person import Person
from stoqlib.domain.product import Product
from stoqlib.domain.sale import Sale
from stoqlib.domain.till import Till
from stoqlib.exceptions import SellError
from stoqlib.lib.defaults import INTERVALTYPE_MONTH, calculate_interval
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

# Number of sales to be created
DEFAULT_SALE_NUMBER = 4

def get_till(trans):
    till = Till.get_current(trans)
    if till is None:
        log.info('Creating a new till')
        till = Till(connection=trans, station=get_current_station(trans))
        till.open_till()
    else:
        log.info('Returning existing till')
    return till

def get_clients(trans):
    client_table = Person.getAdapterClass(IClient)
    result = client_table.select(connection=trans)
    if result.count() <= 0:
        raise SellError("You must have clients to create a sale!")
    return list(result)

def get_all_products(trans):
    result = Product.select(connection=trans)
    if result.count() <= 0:
        raise SellError("You have nothing to sale!")
        sys.exit()
    return list(result)

def _create_sale(trans, open_date, status, branch, salesperson, client,
                    coupon_id, product, installments_number):
    group = PaymentGroup(connection=trans)
    sale = Sale(client=client, status=status,
                open_date=open_date, coupon_id=coupon_id,
                salesperson=salesperson, branch=branch,
                cfop=sysparam(trans).DEFAULT_SALES_CFOP,
                group=group,
                connection=trans)
    sale.set_valid()
    sale.add_sellable(product.sellable)
    method = PaymentMethod.get_by_name(trans, 'check')

    interval = calculate_interval(INTERVALTYPE_MONTH, 30)
    due_dates = []
    sale_total = product.sellable.base_sellable_info.price
    for i in range(installments_number):
        due_dates.append(open_date + datetime.timedelta(i * interval))
    for p in method.create_inpayments(group, sale_total, due_dates):
        p.get_adapted().open_date = open_date

    return sale

#
# Main
#

def create_sales():
    trans = new_transaction()
    log.info("Creating sales")

    sale_statuses = Sale.statuses.keys()
    sale_statuses.remove(Sale.STATUS_CANCELLED)
    clients = get_clients(trans)
    if not len(clients) >= DEFAULT_SALE_NUMBER:
        raise SellError("You don't have clients to create all the sales.")
    product_list = get_all_products(trans)
    if not len(product_list) >= DEFAULT_SALE_NUMBER:
        raise SellError("You don't have products to create all the sales.")
    salespersons = Person.iselect(ISalesPerson, connection=trans)
    if salespersons.count() < DEFAULT_SALE_NUMBER:
        raise ValueError('You should have at last %d salespersons defined '
                         'in database at this point, got %d instead' %
                         (DEFAULT_SALE_NUMBER, salespersons.count()))
    branch = get_current_branch(trans)
    till = get_till(trans)
    open_dates = [datetime.datetime.today(),
                  datetime.datetime.today() + datetime.timedelta(10),
                  datetime.datetime.today() + datetime.timedelta(15),
                  datetime.datetime.today() + datetime.timedelta(23)]
    installments_numbers = [i * 2 for i in range(1, DEFAULT_SALE_NUMBER + 1)]
    for index, (open_date, status, salesperson, client, product,
                installments_number) in enumerate(zip(open_dates,
                                                      sale_statuses,
                                                      salespersons,
                                                      clients,
                                                      product_list,
                                                      installments_numbers)):
        _create_sale(trans, open_date, status, branch, salesperson,
                     client, index, product, installments_number)

    till.close_till()

    # This is sort of hack, set the opening/closing dates to the date before
    # it's run, so we can open/close the till in the tests, which uses
    # the examples.
    yesterday = datetime.date.today() - datetime.timedelta(1)
    till.opening_date = yesterday
    till.closing_date = yesterday

    trans.commit()

if __name__ == '__main__':
    create_sales()
