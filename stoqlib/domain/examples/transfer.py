# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
##  Author(s):  George Kussumoto  <george@async.com.br>
##
""" Create purchase objects for an example database"""

import datetime

from stoqlib.database.runtime import new_transaction
from stoqlib.domain.examples import log
from stoqlib.domain.person import PersonAdaptToUser, PersonAdaptToBranch
from stoqlib.domain.product import ProductHistory
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.transfer import TransferOrder, TransferOrderItem


def create_transfer():
    log.info('Creating transfer order')
    trans = new_transaction()

    employees = PersonAdaptToUser.select(connection=trans)
    if not employees.count() >= 2:
        raise ValueError('You must have at least two employees in your '
                         'database at this point.')

    sellables = Sellable.select(connection=trans)
    if not sellables.count():
        raise ValueError('You must have at least one sellables in your '
                         'database at this point.')

    branches = PersonAdaptToBranch.select(connection=trans)
    if not branches.count() >= 2:
        raise ValueError('You must have at least two branches in your '
                         'database at this point.')

    open_date = datetime.date(2007, 1, 1)
    receival_date = datetime.date(2007, 1, 1)

    order = TransferOrder(connection=trans,
                          open_date=open_date,
                          receival_date=receival_date,
                          source_branch=branches[0],
                          destination_branch=branches[1],
                          source_responsible=employees[0],
                          destination_responsible=employees[1])

    for sellable in sellables:
        if not sellable.product:
            continue
        transfer_item = TransferOrderItem(connection=trans,
                                          quantity=1,
                                          sellable=sellable,
                                          transfer_order=order)
        ProductHistory.add_transfered_item(trans,
                                           order.source_branch,
                                           transfer_item)
    trans.commit()

if __name__ == "__main__":
    create_transfer()
