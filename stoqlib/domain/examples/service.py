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
""" Create service objects for an example database"""

import random

from stoqlib.domain.service import Service
from stoqlib.domain.sellable import BaseSellableInfo
from stoqlib.domain.interfaces import ISellable
from stoqlib.lib.runtime import new_transaction, print_msg


MAX_SERVICES_NUMBER = 4
PRICE_RANGE = 100, 200
COST_RANGE = 1, 99

def create_services():
    print_msg('Creating services...', break_line=False)
    conn = new_transaction()


    descriptions = ['General Service', 'Cleanness', 'Computer Maintenance',
                    'Computer Components Switch']

    # Creating services and facets
    for index in range(MAX_SERVICES_NUMBER):
        service_obj = Service(connection=conn)

        price = round(random.uniform(*PRICE_RANGE))
        description = descriptions[index]

        sellable_info = BaseSellableInfo(connection=conn,
                                         description=description,
                                         price=price)
        cost = round(random.uniform(*COST_RANGE))
        service_obj.addFacet(ISellable, connection=conn,
                             base_sellable_info=sellable_info,
                             cost=cost)

    conn.commit()
    print_msg('done.')

if __name__ == "__main__":
    create_services()
