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
stoq/examples/service.py:

    Create service objects for an example database.
"""

import random

from stoq.domain.service import Service
from stoq.domain.sellable import BaseSellableInfo
from stoq.domain.interfaces import ISellable
from stoq.lib.runtime import new_transaction, print_msg


MAX_SERVICES_NUMBER = 4
PRICE_RANGE = 100, 200 
COST_RANGE = 1, 99

def create_services():
    print_msg('Creating services...', break_line=False)
    conn = new_transaction()
    

    descriptions = ['General Service', 'Cleanness', 'Computer Maintenance',
                    'Computer Components Switch']
    codes = ['General89', 'C762', '872626', 'S123']


    # Creating services and facets
    for index in range(MAX_SERVICES_NUMBER):
        service_obj = Service(connection=conn)
        
        price = round(random.uniform(*PRICE_RANGE))
        description = descriptions[index]

        sellable_info = BaseSellableInfo(connection=conn, 
                                         description=description,
                                         price=price)
        cost = round(random.uniform(*COST_RANGE))
        code = codes[index]
        
        service_obj.addFacet(ISellable, connection=conn,
                             base_sellable_info=sellable_info,
                             cost=cost, code=code)

    conn.commit()
    print_msg('done.')
    
if __name__ == "__main__":
    create_services()
