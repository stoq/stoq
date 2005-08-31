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
stoq/domain/sellable.py:

   This module implements base classes to "sellable objects", such a product
   or a service, implemented in your own modules.
"""
import datetime
import gettext

from sqlobject import DateTimeCol, StringCol, IntCol, FloatCol, ForeignKey
from stoqlib.exceptions import SellError

from stoq.domain.base_model import (Domain, InheritableModelAdapter,
                                    InheritableModel)
from stoq.domain.interfaces import ISellable, IContainer
from stoq.lib.validators import is_date_in_interval
from stoq.lib.parameters import sysparam
from stoq.lib.runtime import get_connection


_ = gettext.gettext
__connection__ = get_connection()



#
# Base Domain Classes
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


class AbstractSellableItem(InheritableModel):
    """ Abstract representation of a concrete sellable"""

    quantity = FloatCol()
    base_price = FloatCol()
    price = FloatCol()
    sale = ForeignKey('Sale')
    sellable = ForeignKey('AbstractSellable')

    def _create(self, id, **kw):
        # XXX This code doesn't work in the constructor because the
        # connection argument is not set properly there. Waiting for
        # SQLObject improvements.
        if not 'kw' in kw:
            if not 'price' in kw:
                raise TypeError('You should provide a price argument.')
            if not 'base_price' in kw:
                kw['base_price'] = kw['price']
            if not 'quantity' in kw:
                kw['quantity'] = 1.0
        InheritableModel._create(self, id, **kw)

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


class AbstractSellable(InheritableModelAdapter):
    """ A sellable (a product or a service, for instance). """

    __implements__ = ISellable, IContainer

    sellable_table = None

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



    #
    # IContainer methods
    #



    
    def add_item(self, item):
        raise NotImplementedError("You should call add_selabble_item "
                                  "instead.")

    def get_items(self):
        if not self.sellable_table:
            raise TypeError("Subclasses must provide a sellable_table"
                            " attribute")
        conn = self.get_connection()
        table, parent = self.sellable_table, AbstractSellableItem
        query = table.q.id == parent.q.sellableID
        return self.sellable_table.select(query, connection=conn)

    def remove_item(self, item):
        if not self.sellable_table:
            raise TypeError("Subclasses must provide a sellable_table"
                            " attribute")
        conn = self.get_connection()
        if not isinstance(item, self.sellable_table):
            raise TypeError("Item should be of type %s, got "
                            % (self.sellable_table, type(item)))
        self.sellable_table.delete(item.id, connection=conn)



    #
    # ISellable methods
    #



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
    # Auxiliary methods
    #



    def get_suggested_markup(self):
        return self.category and self.category.get_markup() 



#
# Auxiliary functions
#



def get_formated_price(float_value):
    conn = get_connection()
    precision = sysparam(conn).SELLABLE_PRICE_PRECISION
    money = _('$')
    return '%s %.*f' % (money, int(precision), float_value)
