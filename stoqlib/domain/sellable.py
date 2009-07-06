# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
""" This module implements base classes to 'sellable objects', such a product
or a service, implemented in your own modules.
"""

import datetime
from decimal import Decimal

from kiwi.datatypes import currency
from stoqdrivers.enum import TaxType
from zope.interface import implements

from stoqlib.database.orm import PriceCol, DecimalCol
from stoqlib.database.orm import DateTimeCol, UnicodeCol, IntCol, ForeignKey
from stoqlib.database.orm import SingleJoin
from stoqlib.database.orm import AND, IN, OR
from stoqlib.domain.interfaces import IDescribable
from stoqlib.domain.base import Domain
from stoqlib.exceptions import (DatabaseInconsistency, SellableError,
                                BarcodeDoesNotExists)
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.validators import is_date_in_interval

_ = stoqlib_gettext

#
# Base Domain Classes
#

class SellableUnit(Domain):
    """ A class used to represent the sellable unit.

    @cvar description: The unit description
    @cvar unit_index:  This column defines if this object represents a custom
      product unit (created by the user through the product editor) or
      a 'native unit', like 'Km', 'Lt' and 'pc'.
      This data is used mainly to interact with stoqdrivers, since when adding
      an item in a coupon we need to know if its unit must be specified as
      a description (using CUSTOM_PM constant) or as an index (using UNIT_*).
      Also, this is directly related to the DeviceSettings editor.
    """
    _inheritable = False
    description = UnicodeCol()
    unit_index = IntCol()

class SellableTaxConstant(Domain):
    """A tax constant tied to a sellable
    """
    implements(IDescribable)

    description = UnicodeCol()
    tax_type = IntCol()
    tax_value = DecimalCol(default=None)

    _mapping = {
        int(TaxType.NONE): 'TAX_NONE',                      # Não tributado - ICMS
        int(TaxType.EXEMPTION): 'TAX_EXEMPTION',            # Isento - ICMS
        int(TaxType.SUBSTITUTION): 'TAX_SUBSTITUTION',      # Substituição tributária - ICMS
        int(TaxType.SERVICE): 'TAX_SERVICE',                # ISS
        }

    def get_value(self):
        return SellableTaxConstant._mapping.get(
            self.tax_type, self.tax_value)


    @classmethod
    def get_by_type(cls, tax_type, conn):
        """Fetch the tax constant for tax_type
        @param tax_type: the tax constant to fetch
        @param conn: a database connection
        @returns: a L{SellableTaxConstant} or None if none is found
        """
        return SellableTaxConstant.selectOneBy(
            tax_type=int(tax_type),
            connection=conn)

    # IDescribable

    def get_description(self):
        return self.description


class SellableCategory(Domain):
    """ Sellable category. This class can represents a
    sellable's category as well its base category.

    @cvar description: The category description
    @cvar suggested_markup: Define the suggested markup when calculating the
       sellable's price.
    @cvar salesperson_comission: A percentage comission suggested for all the
       sales which products belongs to this category.
    @cvar category: base category of this category, None for base categories
       themselves
    """

    description = UnicodeCol()
    suggested_markup = DecimalCol(default=0)
    salesperson_commission = DecimalCol(default=0)
    category = ForeignKey('SellableCategory', default=None)
    tax_constant = ForeignKey('SellableTaxConstant', default=None)

    implements(IDescribable)

    def get_commission(self):
        """Returns the commission for this category.
        If it's unset, return the value of the base category, if any
        @returns: the commission
        """
        if self.category:
            return (self.salesperson_commission or
                    self.category.get_commission())
        return self.salesperson_commission

    def get_markup(self):
        """Returns the markup for this category.
        If it's unset, return the value of the base category, if any
        @returns: the markup
        """
        if self.category:
            return self.suggested_markup or self.category.get_markup()
        return self.suggested_markup

    def get_tax_constant(self):
        """Returns the tax constant for this category.
        If it's unset, return the value of the base category, if any
        @returns: the tax constant
        """
        if self.category:
            return self.tax_constant or self.category.get_tax_constant()
        return self.tax_constant

    # FIXME: Remove?
    def get_description(self):
        return self.description

    def get_full_description(self):
        if self.category:
            return ("%s %s"
                    % (self.category.get_description(), self.description))
        return self.description

    def check_category_description_exists(self, description, conn):
        category = SellableCategory.selectOneBy(description=description,
                                                connection=conn)
        return category is None or category is self

    #
    # Classmethods
    #

    @classmethod
    def get_base_categories(cls, conn):
        """Returns all available base categories
        @param conn: a database connection
        @returns: categories
        """
        return cls.select(cls.q.categoryID == None, connection=conn)


class OnSaleInfo(Domain):
    on_sale_price = PriceCol(default=0)
    on_sale_start_date = DateTimeCol(default=None)
    on_sale_end_date = DateTimeCol(default=None)


class BaseSellableInfo(Domain):
    implements(IDescribable)

    price = PriceCol(default=0)
    description = UnicodeCol(default='')
    max_discount = DecimalCol(default=0)
    commission = DecimalCol(default=0)

    def get_commission(self):
        return self.commission

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.description



class Sellable(Domain):
    """ Sellable information of a certain item such a product
    or a service. Note that sellable is not actually a concrete item but
    only its reference as a sellable. Concrete items are created by
    IContainer routines.

    @ivar status: status the sellable is in
    @type status: enum
    @ivar price: price of sellable
    @type price: float
    @ivar description: full description of sallable
    @type description: string
    @ivar category: a reference to category table
    @type category: L{SellableCategory}
    @ivar markup: ((cost/price)-1)*100
    @type markup: float
    @ivar cost: final cost of sellable
    @type cost: float
    @ivar max_discount: maximum discount allowed
    @type max_discount: float
    @ivar commission: commission to pay after selling this sellable
    @type commission: float
    @ivar on_sale_price: A special price used when we have a "on sale" state
    @type on_sale_price: float
    @ivar on_sale_start_date:
    @ivar on_sale_end_date:
    """

    implements(IDescribable)

    (STATUS_AVAILABLE,
     STATUS_SOLD,
     STATUS_CLOSED,
     STATUS_BLOCKED) = range(4)


    statuses = {STATUS_AVAILABLE:   _(u"Available"),
                STATUS_SOLD:        _(u"Sold"),
                STATUS_CLOSED:      _(u"Closed"),
                STATUS_BLOCKED:     _(u"Blocked")}

    code = UnicodeCol(default='')
    barcode = UnicodeCol(default='')
    # This default status is used when a new sellable is created,
    # so it must be *always* SOLD (that means no stock for it).
    status = IntCol(default=STATUS_SOLD)
    cost = PriceCol(default=0)
    notes = UnicodeCol(default='')
    unit = ForeignKey("SellableUnit", default=None)
    base_sellable_info = ForeignKey('BaseSellableInfo')
    on_sale_info = ForeignKey('OnSaleInfo')
    category = ForeignKey('SellableCategory', default=None)
    tax_constant = ForeignKey('SellableTaxConstant', default=None)

    product = SingleJoin('Product', joinColumn='sellable_id')
    service = SingleJoin('Service', joinColumn='sellable_id')


    def _create(self, id, **kw):
        markup = None
        if not 'kw' in kw:
            conn = self.get_connection()
            if not 'on_sale_info' in kw:
                kw['on_sale_info'] = OnSaleInfo(connection=conn)
            # markup specification must to reflect in the sellable price, since
            # there is no such column -- but we can only change the price right
            # after Domain._create() get executed.
            markup = kw.pop('markup', None)

        Domain._create(self, id, **kw)
        # I'm not checking price in 'kw' because it can be specified through
        # base_sellable_info, and then we'll not update the price properly;
        # instead, I check for "self.price" that, at this point (after
        # Domain._create excecution) is already set and
        # accessible through Sellable's price's accessor.
        if not self.price and ('cost' in kw and 'category' in kw):
            markup = markup or kw['category'].get_markup()
            cost = kw.get('cost', currency(0))
            self.price = cost * (markup / currency(100) + 1)
        if not self.commission and self.category:
            self.commission = self.category.get_commission()

    #
    # ORMObject setters
    #

    def _set_code(self, code):
        if self.check_code_exists(code):
            raise SellableError("The code %s already exists" % code)
        self._SO_set_code(code)

    def _set_barcode(self, barcode):
        if self.check_barcode_exists(barcode):
            raise SellableError("The barcode %s already exists" % barcode)
        self._SO_set_barcode(barcode)

    #
    # Helper methods
    #

    def _get_price_by_markup(self, markup):
        return self.cost + (self.cost * (markup / currency(100)))

    def _get_status_string(self):
        if not self.statuses.has_key(self.status):
            raise DatabaseInconsistency('Invalid status for product got '
                                        '%d' % self.status)
        return self.statuses[self.status]

    #
    # Properties
    #

    def _get_markup(self):
        if self.cost == 0:
            return Decimal(0)
        return ((self.price / self.cost) - 1) * 100

    def _set_markup(self, markup):
        self.price = self._get_price_by_markup(markup)

    markup = property(_get_markup, _set_markup)

    def _get_price(self):
        if self.on_sale_info.on_sale_price:
            today = datetime.datetime.today()
            start_date = self.on_sale_info.on_sale_start_date
            end_date = self.on_sale_info.on_sale_end_date
            if is_date_in_interval(today, start_date, end_date):
                return self.on_sale_info.on_sale_price
        return self.base_sellable_info.price

    def _set_price(self, price):
        self.base_sellable_info.price = price

    price = property(_get_price, _set_price)

    def _get_max_discount(self):
        return self.base_sellable_info.max_discount

    def _set_max_discount(self, discount):
        self.base_sellable_info.max_discount = discount

    max_discount = property(_get_max_discount, _set_max_discount)

    def _get_commission(self):
        return self.base_sellable_info.get_commission()

    def _set_commission(self, commission):
        self.base_sellable_info.commission = commission

    commission = property(_get_commission, _set_commission)

    def can_be_sold(self):
        """Whether the sellable is available and can be sold.
        @returns: if the item can be sold
        @rtype: boolean
        """
        # FIXME: Perhaps this should be done elsewhere. Johan 2008-09-26
        if self == sysparam(self.get_connection()).DELIVERY_SERVICE:
            return True
        return self.status == self.STATUS_AVAILABLE

    def is_sold(self):
        """Whether the sellable is sold.
        @returns: if the item is sold
        @rtype: boolean
        """
        return self.status == self.STATUS_SOLD

    def sell(self):
        """Sell the sellable"""
        if self.is_sold():
            raise ValueError('This sellable is already sold')
        self.status = self.STATUS_SOLD

    def cancel(self):
        """Cancel the sellable"""
        if self.can_be_sold():
            raise ValueError('This sellable is already available')
        self.status = self.STATUS_AVAILABLE

    def can_sell(self):
        """Make the object sellable"""
        # Identical implementation to cancel(), but it has a very different
        # use case, so we keep another method
        self.status = self.STATUS_AVAILABLE

    def can_remove(self):
        """Whether we can delete this sellable from the database.

        False if the product/service was never sold or received. True
        otherwise.
        """
        if self.product:
            return self.product.can_remove()
        else:
            return self.service.can_remove()

    def get_short_description(self):
        """Returns a short description of the current sale
        @returns: description
        @rtype: string
        """
        return u'%s %s' % (self.id, self.base_sellable_info.description)

    def get_suggested_markup(self):
        """Returns the suggested markup for the sellable
        @returns: suggested markup
        @rtype: decimal
        """
        return self.category and self.category.get_markup()

    def get_unit_description(self):
        """Returns the sellable category description
        @returns: the category description or an empty string if no category
        was set.
        """
        return self.unit and self.unit.description or u""

    def get_category_description(self):
        """Returns the description of this sellables category
        If it's unset, return the constant from the category, if any
        @returns: sellable category description
        """
        category = self.category
        return category and category.description or u""

    def get_tax_constant(self):
        """Returns the tax constant for this sellable.
        If it's unset, return the constant from the category, if any
        @returns: the tax constant or None if unset
        """
        if self.tax_constant:
            return self.tax_constant

        if self.category:
            return self.category.get_tax_constant()

    def _check_unique_value_exists(self, attribute, value):
        """Returns True if we already have a sellable with the given attribute
        and value in the database, but ignoring myself.
        """
        if not value:
            return False
        kwargs = {}
        kwargs[attribute] = value
        kwargs['connection'] = self.get_connection()
        # XXX Do not use cls instead of Sellable here since ORMObject
        # can deal properly with queries in inherited tables in this case
        result = Sellable.selectOneBy(**kwargs)
        if result is not None:
            return result is not self
        return False

    def check_code_exists(self, code):
        """Returns True if we already have a sellable with the given code
        in the database.
        """
        return self._check_unique_value_exists('code', code)

    def check_barcode_exists(self, barcode):
        """Returns True if we already have a sellable with the given barcode
        in the database.
        """
        return self._check_unique_value_exists('barcode', barcode)

    #
    # IDescribable implementation
    #

    def get_description(self, full_description=False):
        desc = self.base_sellable_info.get_description()
        if full_description and self.get_category_description():
            desc = "[%s] %s" % (self.get_category_description(), desc)

        return desc

    #
    # Classmethods
    #

    def remove(self):
        """Remove this sellable from the database (including the product or
        service).
        """
        if self.product:
            self.product.remove()
        elif self.service:
            self.service.remove()
        info = self.base_sellable_info
        on_sale = self.on_sale_info
        conn = self.get_connection()

        self.delete(self.id, conn)
        info.delete(info.id, conn)
        on_sale.delete(sale.id, conn)

    @classmethod
    def get_available_sellables_query(cls, conn):
        service = sysparam(conn).DELIVERY_SERVICE
        return AND(cls.q.id != service.id,
                   cls.q.status == cls.STATUS_AVAILABLE)

    @classmethod
    def get_available_sellables(cls, conn):
        """Returns sellable objects which can be added in a sale. By
        default a delivery sellable can not be added manually by users
        since a separated dialog is responsible for that.
        """
        query = cls.get_available_sellables_query(conn)
        return cls.select(query, connection=conn)

    @classmethod
    def get_unblocked_sellables(cls, conn, storable=False, supplier=None):
        """
        Returns unblocked sellable objects, which means the
        available sellables plus the sold ones.
        @param conn: a database connection
        @param storable: if True, only return Storables
        @param supplier: a supplier or None, if set limit the returned
          object to this supplier
        """
        query = OR(cls.get_available_sellables_query(conn),
                   cls.q.status == cls.STATUS_SOLD)
        if storable:
            from stoqlib.domain.product import Product, ProductAdaptToStorable
            query = AND(query,
                        Sellable.q.id == Product.q.sellableID,
                        ProductAdaptToStorable.q._originalID == Product.q.id)

        if supplier:
            from stoqlib.domain.product import Product, ProductSupplierInfo
            query = AND(query,
                        Sellable.q.id == Product.q.sellableID,
                        Product.q.id == ProductSupplierInfo.q.productID,
                        ProductSupplierInfo.q.supplierID == supplier.id)
        return cls.select(query, connection=conn)

    @classmethod
    def get_sold_sellables(cls, conn):
        """Returns sellable objects which can be added in a sale. By
        default a delivery sellable can not be added manually by users
        since a separated dialog is responsible for that.
        """
        return cls.selectBy(status=cls.STATUS_SOLD, connection=conn)

    @classmethod
    def _get_sellables_by_barcode(cls, conn, barcode, extra_query):
        sellable = cls.selectOne(
            AND(Sellable.q.barcode == barcode,
                extra_query), connection=conn)
        if sellable is None:
            raise BarcodeDoesNotExists(
                _("The sellable with barcode '%s' doesn't exists or is "
                  "not available to be sold" % barcode))
        return sellable

    @classmethod
    def get_availables_by_barcode(cls, conn, barcode):
        """Returns a list of avaliable sellables that can be sold.
        A sellable that can be sold can have only one possible
        status: STATUS_AVAILABLE

        @param conn: a orm Transaction instance
        @param barcode: a string representing a sellable barcode
        """
        return cls._get_sellables_by_barcode(
            conn, barcode,
            Sellable.q.status == Sellable.STATUS_AVAILABLE)

    @classmethod
    def get_availables_and_sold_by_barcode(cls, conn, barcode):
        """Returns a list of avaliable sellables and also sellables that
        can be sold.  Here we will get sellables with the following
        statuses: STATUS_AVAILABLE, STATUS_SOLD

        @param conn: a orm Transaction instance
        @param barcode: a string representing a sellable barcode
        """
        statuses = [cls.STATUS_AVAILABLE, cls.STATUS_SOLD]
        return cls._get_sellables_by_barcode(conn, barcode,
                                             IN(cls.q.status, statuses))
    @classmethod
    def get_unblocked_by_categories(cls, conn, categories,
                                    include_uncategorized=True):
        """Returns the available sellables by a list of categories.

        @param conn: a orm Transaction instance
        @param categories: a list of SellableCategory instances
        @param include_uncategorized: whether or not include the sellables
            without a category
        """
        #FIXME: This query should be faster, waiting for #3696

        if include_uncategorized:
            categories.append(None)
        for sellable in cls.get_unblocked_sellables(conn):
            if sellable.category in categories:
                yield sellable
