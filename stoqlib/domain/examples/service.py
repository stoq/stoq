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

from stoqlib.database.runtime import new_transaction
from stoqlib.domain.examples import log
from stoqlib.domain.service import Service
from stoqlib.domain.sellable import BaseSellableInfo
from stoqlib.domain.interfaces import ISellable


MAX_SERVICES_NUMBER = 4

def create_services():
    log.info('Creating services')
    trans = new_transaction()


    descriptions = ['General Service', 'Cleanness', 'Computer Maintenance',
                    'Computer Components Switch']

    barcodes = ['20058', '20059', '20060', '20061']

    prices = [149, 189, 155, 199]
    costs = [105, 65, 103, 89]
    # Creating services and facets
    for index in range(MAX_SERVICES_NUMBER):
        service_obj = Service(connection=trans)

        price = prices[index]
        description = descriptions[index]

        sellable_info = BaseSellableInfo(connection=trans,
                                         description=description,
                                         price=price)
        cost = costs[index]
        barcode = barcodes[index]
        service_obj.addFacet(ISellable, connection=trans,
                             base_sellable_info=sellable_info,
                             cost=cost, barcode=barcode)

    trans.commit()

if __name__ == "__main__":
    create_services()
