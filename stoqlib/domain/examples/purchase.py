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
##  Author(s):      Evandro Vale Miquelito  <evandro@async.com.br>
##
""" Create purchase objects for an example database"""

from stoqlib.database.runtime import (new_transaction, get_current_branch,
                                      get_current_user)
from stoqlib.domain.examples import log
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import (ISupplier, IPaymentGroup,
                                       ITransporter)
from stoqlib.domain.receiving import ReceivingOrder, ReceivingOrderItem
from stoqlib.domain.sellable import ASellable
from stoqlib.lib.defaults import INTERVALTYPE_MONTH, METHOD_BILL


def create_purchases():
    log.info('Creating purchase orders')
    trans = new_transaction()

    suppliers = Person.getAdapterClass(ISupplier).get_active_suppliers(trans)
    if not suppliers.count():
        raise ValueError('You must have at least one suppliers in your '
                         'database at this point.')

    transporters = Person.getAdapterClass(ITransporter
                                          ).select(connection=trans)
    if not transporters.count():
        raise ValueError('You must have at least one suppliers in your '
                         'database at this point.')

    sellables = ASellable.select(connection=trans)
    if not sellables.count():
        raise ValueError('You must have at least one sellables in your '
                         'database at this point.')

    branch = get_current_branch(trans)
    user = get_current_user(trans)

    order = PurchaseOrder(connection=trans,
                          status=PurchaseOrder.ORDER_PENDING,
                          supplier=suppliers[1],
                          branch=branch)
    order.set_valid()
    order.addFacet(IPaymentGroup,
                   default_method=METHOD_BILL,
                   intervals=1,
                   interval_type=INTERVALTYPE_MONTH,
                   connection=trans)

    receiving_order = ReceivingOrder(purchase=order,
                                     responsible=user,
                                     supplier=suppliers[0],
                                     invoice_number=1,
                                     transporter=transporters[0],
                                     branch=branch,
                                     connection=trans)

    for sellable in sellables:
        purchase_item = order.add_item(sellable, 5)
        order.receive_item(purchase_item, 5)

        ReceivingOrderItem(connection=trans,
                           cost=sellable.cost / 2,
                           sellable=sellable,
                           quantity=5,
                           purchase_item=purchase_item,
                           receiving_order=receiving_order)
    order.confirm_order()

    receiving_order.set_valid()
    receiving_order.confirm()

    trans.commit()

if __name__ == "__main__":
    create_purchases()
