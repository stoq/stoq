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
from sqlobject.sqlbuilder import AND, IN
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

class SellableUnit(Domain):
    """ A class used to represent the sellable unit.  The 'index' column
    defines if this object is one of our 'primitive units' (unit registered
    in database initialization time) or a user specified unit.
    """
    description = StringCol()
    index = IntCol()


class FancySellable:
    """A fancy class used by some kiwi entries."""
    # XXX Probably we could avoid this class with some kiwi improvements
    # waiting for bug 2365.

    def __init__(self, price=0.0, quantity=1.0, unit=None):
        self.price = price
        self.quantity = quantity
        self.unit = unit

    def get_unit_description(self):
        return self.unit and self.unit.description or ""

class AbstractSellableCategory(Domain):
    description = StringCol()
    suggested_markup = FloatCol(default=0.0)

    # A percentage commission suggested for all the sales which products
    # belongs to this category or base category
    salesperson_commission = FloatCol(default=0.0)

    def get_commission(self):
        return self.salesperson_commission


class BaseSellableCategory(Domain):
    category_data = ForeignKey('AbstractSellableCategory')

    def get_commission(self):
        return self.category_data.get_commission()

    def get_description(self):
        return self.category_data.description


class SellableCategory(Domain):
    category_data = ForeignKey('AbstractSellableCategory')
    base_category = ForeignKey('BaseSellableCategory')

    def get_markup(self):
        return self.category_data.suggested_markup or \
               self.base_category.category_data.suggested_markup

    def get_commission(self):
        return self.category_data.get_commission()

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
        if not 'kw' in kw:
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
        sellable.sell()

    #
    # Accessors
    #

    def get_total(self):
        return self.price * self.quantity

    def get_price_string(self):
        return get_formatted_price(self.price)


class OnSaleInfo(Domain):
    on_sale_price = FloatCol(default=0.0)
    on_sale_start_date = DateTimeCol(default=None)
    on_sale_end_date = DateTimeCol(default=None)


class BaseSellableInfo(Domain):
    price = FloatCol()
    description = StringCol()
    max_discount = FloatCol(default=0.0)
    commission = FloatCol(default=None)

    def get_commission(self):
        if self.commission is None:
            return 0.0
        return self.commission


class AbstractSellable(InheritableModelAdapter):
    """A sellable (a product or a service, for instance)."""

    implements(ISellable, IContainer)

    sellableitem_table = None
    (STATUS_AVAILABLE,
     STATUS_SOLD,
     STATUS_CLOSED,
     STATUS_BLOCKED) = range(4)
    

    statuses = {STATUS_AVAILABLE: _("Available"),
                STATUS_SOLD: _("Sold"),
                STATUS_CLOSED: _("Closed"),
                STATUS_BLOCKED: _("Blocked")}

    code = StringCol(alternateID=True)
    status = IntCol(default=STATUS_AVAILABLE)
    markup = FloatCol(default=0.0)
    cost = FloatCol(default=0.0)
    unit = ForeignKey("SellableUnit", default=None)
    base_sellable_info = ForeignKey('BaseSellableInfo')
    on_sale_info = ForeignKey('OnSaleInfo')
    category = ForeignKey('SellableCategory', default=None)

    def _create(self, id, **kw):
        if not 'kw' in kw:
            conn = self.get_connection()
            if not 'on_sale_info' in kw:
                kw['on_sale_info'] = OnSaleInfo(connection=conn)
        InheritableModelAdapter._create(self, id, **kw)

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
        return self.status == self.STATUS_AVAILABLE

    def sell(self):
        if not self.can_be_sold():
            raise ValueError('This sellable is not available '
                             'to be sold')
        self.status = self.STATUS_SOLD

    def get_price(self):
        if self.on_sale_info.on_sale_price:
            today = datetime.datetime.today()
            start_date = self.on_sale_info.on_sale_start_date
            end_date = self.on_sale_info.on_sale_end_date
            if is_date_in_interval(today, start_date, end_date):
                return self.on_sale_info.on_sale_price
        return self.base_sellable_info.price

    def add_sellable_item(self, sale, quantity=1.0, price=None, **kwargs):
        """Add a new sellable item instance tied to the current 
        sellable object
        """
        if not self.sellableitem_table:
            raise ValueError('Child classes must define a sellableitem_table '
                             'attribute')
        price = price or self.get_price()
        conn = self.get_connection()
        return self.sellableitem_table(connection=conn, quantity=quantity,
                                       sale=sale, sellable=self,
                                       price=price, **kwargs)
    #
    # Accessors
    #

    def get_price_string(self):
        return get_formatted_price(self.get_price())

    def get_commission(self):
        return self.base_sellable_info.commission

    def get_short_description(self):
        return '%s %s' % (self.code, self.base_sellable_info.description)

    def get_unit_description(self):
        return self.unit and self.unit.description or ""

    def get_status_string(self):
        if not self.statuses.has_key(self.status):
            raise DatabaseInconsistency('Invalid status for product got '
                                        '%d' % self.status)
        return self.statuses[self.status]

    def get_suggested_markup(self):
        return self.category and self.category.get_markup() 

    #
    # Classmethods
    #

    @classmethod
    def get_available_sellables_query(cls, conn):
        service = sysparam(conn).DELIVERY_SERVICE
        delivery = ISellable(service, connection=conn)
        q1 = cls.q.id != delivery.id
        q2 = cls.q.status == cls.STATUS_AVAILABLE
        return AND(q1, q2)

    @classmethod
    def get_available_sellables(cls, conn):
        """Returns sellable objects which can be added in a sale. By 
        default a delivery sellable can not be added manually by users 
        since a separated dialog is responsible for that.
        """
        query = cls.get_available_sellables_query(conn)
        return cls.select(query, connection=conn)

    @classmethod
    def get_sold_sellables(cls, conn):
        """Returns sellable objects which can be added in a sale. By 
        default a delivery sellable can not be added manually by users 
        since a separated dialog is responsible for that.
        """
        query = cls.q.status == cls.STATUS_SOLD
        return cls.select(query, connection=conn)


    @classmethod
    def _get_sellables_by_code(cls, conn, code, extra_query, 
                              notify_callback):
        query = AND(cls.q.code == code, extra_query)
        sellables = cls.select(query, connection=conn)
        qty = sellables.count()
        if not qty:
            msg = _("The sellable with code '%s' doesn't exists" % code)
            notify_callback(msg)
            return
        if qty != 1:
            raise DatabaseInconsistency('You should have only one '
                                        'sellable with code %s' 
                                        % code)
        return sellables[0]

    @classmethod
    def get_availables_by_code(cls, conn, code, notify_callback):
        """Returns a list of avaliable sellables that can be sold. 
        A sellable that can be sold can have only one possible 
        status: STATUS_AVAILABLE
        
        """
        extra_query = cls.q.status == cls.q.STATUS_AVAILABLE
        return cls._get_sellables_by_code(conn, code, extra_query, 
                                          notify_callback)

    @classmethod
    def get_availables_and_sold_by_code(cls, conn, code, notify_callback):
        statuses = [cls.q.STATUS_AVAILABLE, cls.q.STATUS_SOLD]
        extra_query = IN(cls.q.status, statuses)
        return cls._get_sellables_by_code(conn, code, extra_query, 
                                          notify_callback)

    #
    # General methods
    #

    def _set_code(self, code):
        conn = get_connection()
        query = AbstractSellable.q.code == code
        # FIXME We should raise a proper stoqlib exception here if we find
        # an existing code. Waiting for kiwi support 
        if not AbstractSellable.select(query, connection=conn).count():
            self._SO_set_code(code)

    def set_default_commission(self):
        if not self.category:
            self.commission = 0.0
        else:
            commission = self.category.base_category.get_commission()
            self.commission = (self.category.get_commission() 
                               or commission) 
