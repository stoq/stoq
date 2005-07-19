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
lib/domain/sellable.py:

   This module implements base classes to "sellable objects", such a product
   or a service, implemented in your own modules.
"""
import datetime

from sqlobject import DateTimeCol, StringCol, IntCol, FloatCol, ForeignKey
from stoqlib.exceptions import SellError

from stoq.domain.base_model import Domain, InheritableModelAdapter
from stoq.domain.interfaces import ISellable, ISellableItem
from stoq.lib.validators import is_date_in_interval
from stoq.lib.parameters import get_system_parameter
from stoq.lib.runtime import get_connection, new_transaction


__connection__ = get_connection()



#
# Objects
#



class AbstractSellableCategory(Domain):
    description = StringCol()
    suggested_markup = FloatCol(default=0.0)
    # A percentage comission suggested for all the sales which products
    # belongs to this category or base category
    salesperson_comission = FloatCol(default=0.0)


class BaseSellableCategory(Domain):
    category_data = ForeignKey('AbstractSellableCategory')


class SellableCategory(Domain):
    category_data = ForeignKey('AbstractSellableCategory')
    base_category = ForeignKey('BaseSellableCategory')

    def get_markup(self):
        return self.category_data.suggested_markup or \
               self.base_category.category_data.suggested_markup


class AbstractSellable(InheritableModelAdapter):
    """ A sellable (a product or a service, for instance). """

    __implements__ = ISellable,

    STATE_AVALIABLE = 0
    STATE_SOLD = 1
    STATE_BLOCKED = 2

    code = StringCol(alternateID=True)
    state = IntCol(default=STATE_AVALIABLE)
    price = FloatCol()
    description = StringCol()
    markup = FloatCol(default=0.0)
    cost = FloatCol(default=0.0)
    max_discount = FloatCol(default=0.0)
    comission = FloatCol(default=0.0)

    on_sale_price = FloatCol(default=0.0)
    on_sale_start_date = DateTimeCol(default=None)
    on_sale_end_date = DateTimeCol(default=None)

    category = ForeignKey('SellableCategory', default=None)

    def can_be_sold(self):
        return self.state == self.STATE_AVALIABLE

    def set_sold(self):
        assert self.can_be_sold()
        self.state = self.STATE_SOLD

    def get_price(self):
        if self.on_sale_price:
            today = datetime.datetime.today()
            if is_date_in_interval(today, self.on_sale_start_date,
                                   self.on_sale_end_date):
                return self.on_sale_price
        return self.price



    #
    # Accessors
    #



    def get_price_string(self):
        return get_formated_price(self.get_price())



    #
    # Auxiliar methods
    #



    def get_suggested_markup(self):
        return self.category and self.category.get_markup() 


class AbstractSellableItem(InheritableModelAdapter):
    """ Abstract representation of a concrete sellable"""

    __implements__ = ISellableItem,
    
    quantity = FloatCol()
    base_price = FloatCol()
    price = FloatCol()

    def __init__(self, _original=None, *args, **kwargs):
        if not self.is_parent_kwargs(kwargs):
            assert 'price' in kwargs
            if not 'base_price' in kwargs:
                kwargs['base_price'] = kwargs['price']
            if not 'quantity' in kwargs:
                kwargs['quantity'] = 1
        InheritableModelAdapter.__init__(self, _original, *args, **kwargs)

    def sell(self):
        conn = self.get_connection()
        sellable = ISellable(self.get_adapted(), connection=conn)
        if not sellable.can_be_sold():
            msg = '%s is already sold' % self.get_adapted()
            raise SellError(msg)
        sellable.set_sold()


    
    #
    # Accessors
    #


    def get_total(self):
        return self.price * self.quantity



#
# Auxiliar methods
#




def get_formated_price(float_value):
    conn = new_transaction()
    sparam = get_system_parameter(conn)
    precision = sparam.SELLABLE_PRICE_PRECISION
    money = _('$')
    return '%s %.*f' % (money, int(precision), float_value)
