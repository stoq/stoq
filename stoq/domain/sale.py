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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##
"""
stoq/domain/sale.py:

    Sale object and related objects implementation.
"""

from twisted.python.components import implements

from stoq.domain.base_model import Domain
from stoq.domain.interfaces import IContainer, ISellable
from stoq.lib.runtime import get_connection
from stoq.domain.sellable import AbstractSellableItem

__connection__ = get_connection()



#
# Base Domain Classes
#



# XXX Bug 1862 will complete this class with some other important 
# attributes and routines
class Sale(Domain):
    """Sale object implementation.
    Nested imports are needed here because domain/sallable.py imports the
    current one.
    """
    
    __implements__ = IContainer


    
    #
    # IContainer methods
    #


    def add_item(self, item):
        raise NotImplementedError("You should call add_selabble_item "
                                  "SellableItem method instead.")

    def get_items(self):
        conn = self.get_connection()
        query = AbstractSellableItem.q.saleID == self.id
        return AbstractSellableItem.select(query, connection=conn)

    def remove_item(self, item):
        if not implements(item, ISellable):
            raise TypeError("Item should implement ISellable")
        conn = self.get_connection()
        table = type(item)
        table.delete(item.id, connection=conn)
