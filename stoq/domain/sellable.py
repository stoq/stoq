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
from sqlobject.sqlbuilder import AND
from zope.interface import implements
from stoqlib.exceptions import SellError, DatabaseInconsistency

from stoq.lib.validators import is_date_in_interval, get_formatted_price
from stoq.lib.runtime import get_connection
from stoq.lib.parameters import sysparam
from stoq.domain.interfaces import ISellable, IContainer
from stoq.domain.base import (Domain, InheritableModelAdapter,
                                    InheritableModel)



_ = gettext.gettext

#
# Base Domain Classes
#

class AbstractSellableCategory(Domain):
    description = StringCol()
    suggested_markup = FloatCol(default=0.0)

    # A percentage comission suggested for all the sales which products
    # belongs to this category or base category
    salesperson_comission = FloatCol(default=0.0)

    def get_comission(self):
        return self.salesperson_comission


class BaseSellableCategory(Domain):
    category_data = ForeignKey('AbstractSellableCategory')

    def get_comission(self):
        return self.category_data.get_comission()

    def get_description(self):
        return self.category_data.description


class SellableCategory(Domain):
    category_data = ForeignKey('AbstractSellableCategory')
    base_category = ForeignKey('BaseSellableCategory')

    def get_markup(self):
        return self.category_data.suggested_markup or \
               self.base_category.category_data.suggested_markup

    def get_comission(self):
        return self.category_data.get_comission()

    def get_description(self):
        return "%s %s" % (self.base_category.get_description(),
                          self.category_data.description)


class AbstractSellableItem(InheritableModel):
    """Abstract representation of a concrete sellable."""

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
            if 'base_price' in kw:
                raise TypeError('You should not provide a base_price '
                                'argument since it is set automatically')
            if not 'sellable' in kw:
                raise TypeError('You must provide a sellable argument')
            base_price = kw['sellable'].get_price()
            kw['base_price'] = base_price
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

    def get_price_string(self):
        return get_formatted_price(self.price)


class AbstractSellable(InheritableModelAdapter):
    """A sellable (a product or a service, for instance)."""

    implements(ISellable, IContainer)

    sellableitem_table = None
    (STATE_AVAILABLE,
     STATE_SOLD,
     STATE_BLOCKED) = range(3)
    

    states = {STATE_AVAILABLE: _("Available"),
              STATE_SOLD: _("Sold"),
              STATE_BLOCKED: _("Blocked")}

    code = StringCol(alternateID=True)
    state = IntCol(default=STATE_AVAILABLE)
    price = FloatCol()
    description = StringCol()
    markup = FloatCol(default=0.0)
    cost = FloatCol(default=0.0)
    max_discount = FloatCol(default=0.0)
    comission = FloatCol(default=None)
    # This field must be mandatory, waiting for bug 2247
    unit = StringCol(default=None)
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
        if not self.sellableitem_table:
            raise TypeError("Subclasses must provide a sellableitem_table"
                            " attribute")
        conn = self.get_connection()
        table, parent = self.sellableitem_table, AbstractSellableItem
        query = table.q.id == parent.q.sellableID
        return self.sellableitem_table.select(query, connection=conn)

    def remove_item(self, item):
        if not self.sellableitem_table:
            raise TypeError("Subclasses must provide a sellableitem_table"
                            " attribute")
        conn = self.get_connection()
        if not isinstance(item, self.sellableitem_table):
            raise TypeError("Item should be of type %s, got "
                            % (self.sellableitem_table, type(item)))
        self.sellableitem_table.delete(item.id, connection=conn)

    #
    # ISellable methods
    #

    def can_be_sold(self):
        return self.state == self.STATE_AVAILABLE

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

    def add_sellable_item(self, sale, quantity=1.0, price=None):
        if not self.sellableitem_table:
            raise ValueError('Child classes must define a sellableitem_table '
                             'attribute')
        price = price or self.get_price()
        conn = self.get_connection()
        return self.sellableitem_table(connection=conn, quantity=quantity,
                                       sale=sale, sellable=self, price=price)
    #
    # Accessors
    #

    def get_price_string(self):
        return get_formatted_price(self.get_price())

    def get_comission(self):
        return self.comission

    #
    # Auxiliary methods
    #

    def get_states_string(self):
        if not self.states.has_key(self.state):
            raise DatabaseInconsistency('Invalid state for product got '
                                        '%d' % self.state)
        return self.states[self.state]

    def _set_code(self, code):
        conn = get_connection()
        query = AbstractSellable.q.code == code
        # FIXME We should raise a proper stoqlib exception here if we find
        # an existent code. Waiting for kiwi support 
        if not AbstractSellable.select(query, connection=conn).count():
            self._SO_set_code(code)

    @classmethod
    def get_available_sellables_query(cls, conn):
        service = sysparam(conn).DELIVERY_SERVICE
        delivery = ISellable(service, connection=conn)
        q1 = cls.q.id != delivery.id
        q2 = cls.q.state == cls.STATE_AVAILABLE
        return AND(q1, q2)

    @classmethod
    def get_available_sellables(cls, conn):
        """Returns sellable objects which can be added in a sale. By 
        default a delivery sellable can not be added manually by users 
        since a separated dialog is responsible for that.
        """
        query = cls.get_available_sellables_query(conn)
        return cls.select(query, connection=conn)

    def get_suggested_markup(self):
        return self.category and self.category.get_markup() 

    def set_default_comission(self):
        if not self.category:
            self.comission = 0.0
        else:
            self.comission = (self.category.get_comission() 
                              or self.category.base_category.get_comission())
