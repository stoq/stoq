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
"""
stoq/domain/service.py:
    
    Base classes to manage services informations
"""

import gettext

from stoqlib.exceptions import SellError
from sqlobject import StringCol, DateTimeCol

from stoq.domain.base_model import Domain, ModelAdapter
from stoq.domain.sellable import AbstractSellable, AbstractSellableItem
from stoq.domain.interfaces import ISellable, IDelivery, IContainer
from stoq.domain.product import ProductSellableItem
from stoq.lib.runtime import get_connection



_ = gettext.gettext
__connection__ = get_connection()



#
# Base Domain Classes
#



class Service(Domain):
    """ Class responsible to store basic service informations """
    
    notes = StringCol(default='')


class ServiceSellableItem(AbstractSellableItem):
    """ A service implementation as a sellable item. """

    notes = StringCol(default=None)
    estimated_fix_date = DateTimeCol(default=None)
    completion_date = DateTimeCol(default=None)
    
    #
    # Auxiliary methods
    #

    def sell(self):
        conn = self.get_connection()
        sellable = ISellable(self.get_adapted(), connection=conn)
        if not sellable.can_be_sold():
            msg = '%s is already sold' % self.get_adapted()
            raise SellError(msg)


#
# Adapters
#


class ServiceSellableItemAdaptToDelivery(ModelAdapter):
    """ A service implementation as a delivery facet. """

    __implements__ = IDelivery, IContainer

    address = StringCol(default='')

    #
    # IContainer implementation
    #

    def add_item(self, item):
        if not isinstance(item, ProductSellableItem):
            raise TypeError("Received a %s object, expected %s." 
                            % (type(item), ProductSellableItem))
        item.delivery_data = self

    def get_items(self):
        return ProductSellableItem.selectBy(connection=self.get_connection(),
                                            delivery_dataID=self.id)

    def remove_items(self, items):
        for item in items:
            item.delivery_data = None

ServiceSellableItem.registerFacet(ServiceSellableItemAdaptToDelivery)


class ServiceAdaptToSellable(AbstractSellable):
    """ A service implementation as a sellable facet. """

    sellable_table = ServiceSellableItem

    #
    # Auxiliary methods
    #

    def add_sellable_item(self, sale, quantity, base_price, price):
        conn = self.get_connection()
        return ServiceSellableItem(connection=conn, quantity=quantity,
                                   base_price=base_price, price=price,
                                   sale=sale, sellable=self)

Service.registerFacet(ServiceAdaptToSellable)
