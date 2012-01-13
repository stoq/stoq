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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" This module implements base classes to 'sellable objects', such a product
or a service, implemented in your own modules.
"""

import datetime
from decimal import Decimal

from kiwi.datatypes import currency
from stoqdrivers.enum import TaxType, UnitType
from zope.interface import implements

from stoqlib.database.orm import BoolCol, PriceCol, PercentCol
from stoqlib.database.orm import DateTimeCol, UnicodeCol, IntCol, ForeignKey
from stoqlib.database.orm import SingleJoin
from stoqlib.database.orm import AND, IN, OR
from stoqlib.domain.interfaces import IDescribable
from stoqlib.domain.base import Domain
from stoqlib.domain.events import CategoryCreateEvent, CategoryEditEvent
from stoqlib.exceptions import (DatabaseInconsistency, SellableError,
                                BarcodeDoesNotExists, TaxError)
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.validators import is_date_in_interval

_ = stoqlib_gettext

#
# Base Domain Classes
#


class SellableUnit(Domain):
    """ A class used to represent the sellable unit.

    @cvar SYSTEM_PRIMITIVES: The values on the list are enums used to fill
      'unit_index' column above. That list is useful for many things,
      e.g. See if the user can delete the unit. It should not be possible
      to delete a primitive one.
    @cvar description: The unit description
    @cvar unit_index:  This column defines if this object represents a custom
      product unit (created by the user through the product editor) or
      a 'native unit', like 'Km', 'Lt' and 'pc'.
      This data is used mainly to interact with stoqdrivers, since when adding
      an item in a coupon we need to know if its unit must be specified as
      a description (using CUSTOM_PM constant) or as an index (using UNIT_*).
      Also, this is directly related to the DeviceSettings editor.
    @cvar allow_fraction: If the unit allows to be represented in fractions.
      e.g. We can have 1 car, 2 cars, but not 1/2 car.
    """
    implements(IDescribable)

    SYSTEM_PRIMITIVES = [UnitType.WEIGHT,
                         UnitType.METERS,
                         UnitType.LITERS]

    _inheritable = False
    description = UnicodeCol()
    # Using an int cast on UnitType because
    # SQLObject doesn't recognize it's type.
    unit_index = IntCol(default=int(UnitType.CUSTOM))
    allow_fraction = BoolCol(default=True)

    # IDescribable

    def get_description(self):
        return self.description


class SellableTaxConstant(Domain):
    """A tax constant tied to a sellable
    """
    implements(IDescribable)

    description = UnicodeCol()
    tax_type = IntCol()
    tax_value = PercentCol(default=None)

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


# pylint: disable=E1101
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
    suggested_markup = PercentCol(default=0)
    salesperson_commission = PercentCol(default=0)
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
# pylint: enable=E1101

    #
    # Domain hooks
    #

    def on_create(self):
        CategoryCreateEvent.emit(self)

    def on_update(self):
        CategoryEditEvent.emit(self)


class ClientCategoryPrice(Domain):
    """A table that stores special prices for clients based on their
    category.

    @ivar sellable: The sellable that has a special price
    @ivar category: The category that has the special price
    @ivar price: The price for this (sellable, category)
    @ivar max_discount: The max discount that may be applied.
    """
    sellable = ForeignKey('Sellable')
    category = ForeignKey('ClientCategory')
    price = PriceCol(default=0)
    max_discount = PercentCol(default=0)

    def _get_markup(self):
        if self.sellable.cost == 0:
            return Decimal(0)
        return ((self.price / self.sellable.cost) - 1) * 100

    def _set_markup(self, markup):
        self.price = self.sellable._get_price_by_markup(markup)

    markup = property(_get_markup, _set_markup)

    @property
    def category_name(self):
        return self.category.name

    def remove(self):
        """Removes this client category price from the database."""
        self.delete(self.id, self.get_connection())


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
     STATUS_UNAVAILABLE,
     STATUS_CLOSED,
     STATUS_BLOCKED) = range(4)

    statuses = {STATUS_AVAILABLE: _(u'Available'),
                STATUS_UNAVAILABLE: _(u'Unavailable'),
                STATUS_CLOSED: _(u'Closed'),
                STATUS_BLOCKED: _(u'Blocked')}

    code = UnicodeCol(default='')
    barcode = UnicodeCol(default='')
    # This default status is used when a new sellable is created,
    # so it must be *always* UNAVAILABLE (that means no stock for it).
    status = IntCol(default=STATUS_UNAVAILABLE)
    cost = PriceCol(default=0)
    base_price = PriceCol(default=0)
    description = UnicodeCol(default='')
    max_discount = PercentCol(default=0)
    commission = PercentCol(default=0)

    notes = UnicodeCol(default='')
    unit = ForeignKey("SellableUnit", default=None)

    category = ForeignKey('SellableCategory', default=None)
    tax_constant = ForeignKey('SellableTaxConstant', default=None)

    product = SingleJoin('Product', joinColumn='sellable_id')
    service = SingleJoin('Service', joinColumn='sellable_id')

    default_sale_cfop = ForeignKey("CfopData", default=None)

    on_sale_price = PriceCol(default=0)
    on_sale_start_date = DateTimeCol(default=None)
    on_sale_end_date = DateTimeCol(default=None)

    def _create(self, id, **kw):
        markup = None
        if not 'kw' in kw:
            # markup specification must to reflect in the sellable price, since
            # there is no such column -- but we can only change the price right
            # after Domain._create() get executed.
            markup = kw.pop('markup', None)

        category = kw.get('category', None)
        if 'price' not in kw and 'cost' in kw and category:
            markup = markup or category.get_markup()
            cost = kw.get('cost', currency(0))
            kw['price'] = cost * (markup / currency(100) + 1)
        if 'commission' not in kw and category:
            kw['commission'] = category.get_commission()

        Domain._create(self, id, **kw)

    #
    # ORMObject setters
    #

    def _set_code(self, code):
        if self.check_code_exists(code):
            raise SellableError(_("The code %s already exists") % code)
        self._SO_set_code(code)

    def _set_barcode(self, barcode):
        if self.check_barcode_exists(barcode):
            raise SellableError(_("The barcode %s already exists") % barcode)
        self._SO_set_barcode(barcode)

    #
    # Helper methods
    #

    def _get_price_by_markup(self, markup):
        return self.cost + (self.cost * (markup / currency(100)))

    def _get_status_string(self):
        if not self.status in self.statuses:
            raise DatabaseInconsistency(_('Invalid status for product got %d')
                                        % self.status)
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
        if self.on_sale_price:
            today = datetime.datetime.today()
            start_date = self.on_sale_start_date
            end_date = self.on_sale_end_date
            if is_date_in_interval(today, start_date, end_date):
                return self.on_sale_price
        return self.base_price

    def _set_price(self, price):
        if price < 0:
            # Just a precaution for gui validation fails.
            price = 0

        if self.on_sale_price:
            today = datetime.datetime.today()
            start_date = self.on_sale_start_date
            end_date = self.on_sale_end_date
            if is_date_in_interval(today, start_date, end_date):
                self.on_sale_price = price
                return
        self.base_price = price

    price = property(_get_price, _set_price)

    #
    #  Accessors
    #

    def can_be_sold(self):
        """Whether the sellable is available and can be sold.
        @returns: if the item can be sold
        @rtype: boolean
        """
        # FIXME: Perhaps this should be done elsewhere. Johan 2008-09-26
        if self.service == sysparam(self.get_connection()).DELIVERY_SERVICE:
            return True
        return self.status == self.STATUS_AVAILABLE

    def is_unavailable(self):
        """Whether the sellable is unavailable.
        @returns: if the item is unavailable
        @rtype: boolean
        """
        return self.status == self.STATUS_UNAVAILABLE

    def set_unavailable(self):
        """Mark the sellable as unavailable"""
        if self.is_unavailable():
            raise ValueError('This sellable is already unavailable')
        self.status = self.STATUS_UNAVAILABLE

    def is_closed(self):
        """Whether the sellable is closed or not.

        @returns: True if closed, False otherwise.
        """
        return self.status == Sellable.STATUS_CLOSED

    def close(self):
        """Mark the sellable as closed"""
        if self.is_closed():
            raise ValueError('This sellable is already closed')

        assert self.can_close()
        self.status = Sellable.STATUS_CLOSED

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

        False if the product/service was used in some cases below:
            - Sold or received
            - The product is in a purchase
        """
        from stoqlib.domain.sale import SaleItem
        if SaleItem.selectBy(connection=self.get_connection(),
                             sellable=self).count():
            # FIXME: Find a better way of doing this.
            # Quotes (and maybe other cases) don't go to the history,
            # so make sure there's nothing left on SaleItem referencing
            # this sellable.
            return False

        # If the product is in a purchase.
        from stoqlib.domain.purchase import PurchaseItem
        if PurchaseItem.selectBy(connection=self.get_connection(),
                                 sellable=self).count():
            return False

        if self.product:
            return self.product.can_remove()
        elif self.service:
            return self.service.can_remove()

        return False

    def can_close(self):
        """Whether we can close this sellable.

        @returns: True if the product has no stock left or the service
            is not required by the system (i.e. Delivery service is
            required). False otherwise.
        """
        if self.service:
            return self.service.can_close()
        return self.is_unavailable()

    def get_commission(self):
        return self.commission

    def get_short_description(self):
        """Returns a short description of the current sale
        @returns: description
        @rtype: string
        """
        return u'%s %s' % (self.id, self.description)

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

    def get_category_prices(self):
        """Returns all client category prices associated with this sellable.
        """
        return ClientCategoryPrice.selectBy(sellable=self,
                                            connection=self.get_connection())

    def get_category_price_info(self, category):
        """Returns the L{ClientCategoryPrice} information for the given
        L{ClientCategory} and this sellabe.

        @returns: the L{ClientCategoryPrice} or None
        """
        info = ClientCategoryPrice.selectOneBy(sellable=self,
                                        category=category,
                                        connection=self.get_connection())
        return info

    def get_price_for_category(self, category):
        """Given the L{ClientCategory}, returns the price for that category
        or the default sellable price.

        @param category: a L{ClientCategory}
        @returns: The value that should be used as a price for this
        sellable.
        """
        info = self.get_category_price_info(category)
        if info:
            return info.price
        return self.price

    def check_code_exists(self, code):
        """Returns True if we already have a sellable with the given code
        in the database.
        """
        return self.check_unique_value_exists('code', code)

    def check_barcode_exists(self, barcode):
        """Returns True if we already have a sellable with the given barcode
        in the database.
        """
        return self.check_unique_value_exists('barcode', barcode)

    def check_taxes_validity(self):
        """Check if icms taxes are valid.

        This check is done because some icms taxes (such as CSOSN 101) have
        a 'valid until' field on it. If these taxes has expired, we cannot sell
        the sellable.
        Check this method using assert inside a try clause. This method will
        raise TaxError if there are any issues with the sellable taxes.
        """
        icms_template = self.product and self.product.icms_template
        if not icms_template:
            return
        elif not icms_template.p_cred_sn:
            return
        elif not icms_template.is_p_cred_sn_valid():
            # Translators: ICMS tax rate credit = Alíquota de crédito do ICMS
            raise TaxError(_("You cannot sell this item before updating "
                             "the 'ICMS tax rate credit' field on '%s' "
                             "Tax Class.\n"
                             "If you don't know what this means, contact "
                             "the system administrator.")
                              % icms_template.product_tax_template.name)

    def is_valid_quantity(self, new_quantity):
        """Whether the new quantity is valid for this sellable or not.

        If the new quantity is fractioned, check on this sellable unit if it
        allows fractioned quantities. If not, this new quantity cannot be used.

        @returns: True if new quantity is Ok, False otherwise.
        """
        if self.unit and not self.unit.allow_fraction:
            return not bool(new_quantity % 1)

        return True

    def is_valid_price(self, newprice, category=None):
        """Returns True if the new price respects the maximum discount
        configured for the sellable, otherwise returns False.

        @param newprice: The new price that we are trying to sell this
        sellable for.
        @param category: Optionally define a category that we will get the
        price info from.
        """
        info = None
        if category:
            info = self.get_category_price_info(category)
        if not info:
            info = self
        if newprice < info.price - (info.price * info.max_discount / 100):
            return False
        return True

    #
    # IDescribable implementation
    #

    def get_description(self, full_description=False):
        desc = self.description
        if full_description and self.get_category_description():
            desc = "[%s] %s" % (self.get_category_description(), desc)

        return desc

    #
    # Domain hooks
    #

    def on_update(self):
        product = self.product
        if product:
            product.on_update()

        service = self.service
        if service:
            service.on_update()

    #
    # Classmethods
    #

    def remove(self):
        """Remove this sellable from the database (including the product or
        service).
        """
        assert self.can_remove()

        # Remove category price before delete the sellable.
        category_prices = self.get_category_prices()
        for category_price in category_prices:
            category_price.remove()

        if self.product:
            self.product.remove()
        elif self.service:
            self.service.remove()

        conn = self.get_connection()
        self.delete(self.id, conn)

    @classmethod
    def get_available_sellables_for_quote_query(cls, conn):
        service_sellable = sysparam(conn).DELIVERY_SERVICE.sellable
        return AND(cls.q.id != service_sellable.id,
                   OR(cls.q.status == cls.STATUS_AVAILABLE,
                      cls.q.status == cls.STATUS_UNAVAILABLE))

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
    def get_unblocked_sellables_query(cls, conn, storable=False, supplier=None,
                                      consigned=False):
        """Helper method for get_unblocked_sellables"""
        from stoqlib.domain.product import Product, ProductSupplierInfo
        query = AND(OR(cls.get_available_sellables_query(conn),
                       cls.q.status == cls.STATUS_UNAVAILABLE),
                    cls.q.id == Product.q.sellableID,
                    Product.q.consignment == consigned)
        if storable:
            from stoqlib.domain.product import Product, ProductAdaptToStorable
            query = AND(query,
                        Sellable.q.id == Product.q.sellableID,
                        ProductAdaptToStorable.q.originalID == Product.q.id)

        if supplier:
            query = AND(query,
                        Sellable.q.id == Product.q.sellableID,
                        Product.q.id == ProductSupplierInfo.q.productID,
                        ProductSupplierInfo.q.supplierID == supplier.id)

        return query

    @classmethod
    def get_unblocked_sellables(cls, conn, storable=False, supplier=None,
                                consigned=False):
        """
        Returns unblocked sellable objects, which means the
        available sellables plus the sold ones.
        @param conn: a database connection
        @param storable: if True, only return Storables
        @param supplier: a supplier or None, if set limit the returned
          object to this supplier
        """
        query = cls.get_unblocked_sellables_query(conn, storable, supplier,
                                                  consigned)
        return cls.select(query, connection=conn)

    @classmethod
    def get_unavailable_sellables(cls, conn):
        """Returns sellable objects which can be added in a sale. By
        default a delivery sellable can not be added manually by users
        since a separated dialog is responsible for that.
        """
        return cls.selectBy(status=cls.STATUS_UNAVAILABLE, connection=conn)

    @classmethod
    def _get_sellables_by_barcode(cls, conn, barcode, extra_query):
        sellable = cls.selectOne(
            AND(Sellable.q.barcode == barcode,
                extra_query), connection=conn)
        if sellable is None:
            raise BarcodeDoesNotExists(
                _("The sellable with barcode '%s' doesn't exists or is "
                  "not available to be sold") % barcode)
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
    def get_availables_and_unavailable_by_barcode(cls, conn, barcode):
        """Returns a list of avaliable sellables and also sellables that
        can be sold.  Here we will get sellables with the following
        statuses: STATUS_AVAILABLE, STATUS_UNAVAILABLE

        @param conn: a orm Transaction instance
        @param barcode: a string representing a sellable barcode
        """
        statuses = [cls.STATUS_AVAILABLE, cls.STATUS_UNAVAILABLE]
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
