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
from stoq.domain.interfaces import ISellable
from stoq.lib.runtime import new_transaction, print_msg


MAX_SERVICES_NUMBER = 4
PRICE_RANGE = 100, 200 
COST_RANGE = 1, 99

def create_services():
    print_msg('creating services...', break_line=False)
    trans = new_transaction()
    

    sellable_data = [dict(code='General89',
                          description='General Service'),
                     dict(code='C762',
                          description='Cleanness'),
                     dict(code='872626',
                          description='Computer Maintenance'),
                     dict(code='S123',
                          description='Computer Components Switch')]


    # Creating services and facets
    for index in range(MAX_SERVICES_NUMBER):
        service_obj = Service(connection=trans)
        
        sellable_args = sellable_data[index]
        price = round(random.uniform(*PRICE_RANGE))
        cost = round(random.uniform(*COST_RANGE))
        service_obj.addFacet(ISellable, connection=trans,
                             price=price, cost=cost,
                             **sellable_args)

    trans.commit()
    print_msg('done.')
    
if __name__ == "__main__":
    create_services()
