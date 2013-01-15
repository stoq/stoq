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

from kiwi.currency import currency
from stoqdrivers.enum import TaxType, UnitType
from storm.expr import And, In, Or
from storm.references import Reference, ReferenceSet
from zope.interface import implements

from stoqlib.database.orm import BoolCol, PriceCol, PercentCol
from stoqlib.database.orm import DateTimeCol, UnicodeCol, IntCol
from stoqlib.domain.base import Domain
from stoqlib.domain.events import CategoryCreateEvent, CategoryEditEvent
from stoqlib.domain.interfaces import IDescribable
from stoqlib.domain.image import Image
from stoqlib.exceptions import (DatabaseInconsistency, SellableError,
                                BarcodeDoesNotExists, TaxError)
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.validators import is_date_in_interval

_ = stoqlib_gettext

# pyflakes: Sellable.has_image requires that Image is imported at least once
Image

#
# Base Domain Classes
#


class SellableUnit(Domain):
    """ A class used to represent the sellable unit.

    """
    __storm_table__ = 'sellable_unit'

    implements(IDescribable)

    #: The values on the list are enums used to fill
    # ``'unit_index'`` column above. That list is useful for many things,
    # e.g. See if the user can delete the unit. It should not be possible
    # to delete a primitive one.
    SYSTEM_PRIMITIVES = [UnitType.WEIGHT,
                         UnitType.METERS,
                         UnitType.LITERS]

    #: The unit description
    description = UnicodeCol()

    # FIXME: Using an int cast on UnitType because
    #        SQLObject doesn't recognize it's type.
    #: This column defines if this object represents a custom product unit
    #: (created by the user through the product editor) or a *native unit*,
    #: like ``Km``, ``Lt`` and ``pc``.
    #:
    #: This data is used mainly to interact with stoqdrivers, since when adding
    #: an item in a coupon we need to know if its unit must be specified as
    #: a description (using ``CUSTOM_PM`` constant) or as an index (using UNIT_*).
    #: Also, this is directly related to the DeviceSettings editor.
    unit_index = IntCol(default=int(UnitType.CUSTOM))

    #: If the unit allows to be represented in fractions.
    #:  e.g. We can have 1 car, 2 cars, but not 1/2 car.
    allow_fraction = BoolCol(default=True)

    # IDescribable

    def get_description(self):
        return self.description


class SellableTaxConstant(Domain):
    """A tax constant tied to a sellable
    """
    implements(IDescribable)

    __storm_table__ = 'sellable_tax_constant'

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
    def get_by_type(cls, tax_type, store):
        """Fetch the tax constant for tax_type
        :param tax_type: the tax constant to fetch
        :param store: a store
        :returns: a |sellabletaxconstant| or ``None`` if none is found
        """
        return store.find(SellableTaxConstant, tax_type=int(tax_type)).one()

    # IDescribable

    def get_description(self):
        return self.description


# pylint: disable=E1101
class SellableCategory(Domain):
    """ Sellable category.

    This class can represents a sellable's category as well its base category.
    """
    __storm_table__ = 'sellable_category'

    #: The category description
    description = UnicodeCol()

    #: Define the suggested markup when calculating the sellable's price.
    suggested_markup = PercentCol(default=0)

    #: A percentage comission suggested for all the sales which products
    #: belongs to this category.
    salesperson_commission = PercentCol(default=0)

    category_id = IntCol(default=None)

    #: base category of this category, ``None`` for base categories themselves
    category = Reference(category_id, 'SellableCategory.id')

    tax_constant_id = IntCol(default=None)

    tax_constant = Reference(tax_constant_id, 'SellableTaxConstant.id')

    children = ReferenceSet('id', 'SellableCategory.category_id')

    implements(IDescribable)

    #
    #  Properties
    #

    @property
    def full_description(self):
        descriptions = [self.description]

        parent = self.category
        while parent:
            descriptions.append(parent.description)
            parent = parent.category

        return ':'.join(reversed(descriptions))

    #
    #  Public API
    #

    def get_children_recursively(self):
        """Return all the children from this category, recursively

        This will return all children recursively, e.g.::

                      A
                     / \
                    B   C
                   / \
                  D   E

        In this example, calling this from A will return ``set([B, C, D, E])``
        """
        children = set(self.children)

        if not len(children):
            # Base case for the leafs
            return set()

        for child in list(children):
            children |= child.get_children_recursively()

        return children

    def get_commission(self):
        """Returns the commission for this category.
        If it's unset, return the value of the base category, if any

        :returns: the commission
        """
        if self.category:
            return (self.salesperson_commission or
                    self.category.get_commission())
        return self.salesperson_commission

    def get_markup(self):
        """Returns the markup for this category.
        If it's unset, return the value of the base category, if any

        :returns: the markup
        """
        if self.category:
            # Compare to None as markup can be '0'
            if self.suggested_markup is not None:
                return self.suggested_markup
            return  self.category.get_markup()
        return self.suggested_markup

    def get_tax_constant(self):
        """Returns the tax constant for this category.
        If it's unset, return the value of the base category, if any

        :returns: the tax constant
        """
        if self.category:
            return self.tax_constant or self.category.get_tax_constant()
        return self.tax_constant

    #
    #  IDescribable
    #

    def get_description(self):
        return self.description

    #
    # Classmethods
    #

    @classmethod
    def get_base_categories(cls, store):
        """Returns all available base categories
        :param store: a store
        :returns: categories
        """
        return store.find(cls, category_id=None)

    #
    # Domain hooks
    #

    def on_create(self):
        CategoryCreateEvent.emit(self)

    def on_update(self):
        CategoryEditEvent.emit(self)


# pylint: enable=E1101


class ClientCategoryPrice(Domain):
    """A table that stores special prices for clients based on their
    category.
    """
    __storm_table__ = 'client_category_price'

    sellable_id = IntCol()

    #: The sellable that has a special price
    sellable = Reference(sellable_id, 'Sellable.id')

    category_id = IntCol()

    #: The category that has the special price
    category = Reference(category_id, 'ClientCategory.id')

    #: The price for this (sellable, category)
    price = PriceCol(default=0)

    #: The max discount that may be applied.
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
        self.delete(self.id, self.store)


def _validate_code(sellable, attr, code):
    if sellable.check_code_exists(code):
        raise SellableError(
            _("The sellable code %r already exists") % (code, ))
    return code


def _validate_barcode(sellable, attr, barcode):
    if sellable.check_barcode_exists(barcode):
        raise SellableError(
            _("The sellable barcode %r already exists") % (barcode, ))
    return barcode


class Sellable(Domain):
    """ Sellable information of a certain item such a product
    or a service. Note that sellable is not actually a concrete item but
    only its reference as a sellable. Concrete items are created by
    IContainer routines.
    """
    __storm_table__ = 'sellable'

    implements(IDescribable)

    (STATUS_AVAILABLE,
     STATUS_UNAVAILABLE,
     STATUS_CLOSED,
     STATUS_BLOCKED) = range(4)

    statuses = {STATUS_AVAILABLE: _(u'Available'),
                STATUS_UNAVAILABLE: _(u'Unavailable'),
                STATUS_CLOSED: _(u'Closed'),
                STATUS_BLOCKED: _(u'Blocked')}

    #: an internal code identifying the sellable in Stoq
    code = UnicodeCol(default='', validator=_validate_code)

    #: barcode, mostly for products, usually printed and attached to the
    #: package.
    barcode = UnicodeCol(default='', validator=_validate_barcode)

    # This default status is used when a new sellable is created,
    # so it must be *always* UNAVAILABLE (that means no stock for it).
    #: status the sellable is in
    status = IntCol(default=STATUS_UNAVAILABLE)

    #: cost of the sellable
    cost = PriceCol(default=0)

    #: price of sellable, how much the client is charged
    base_price = PriceCol(default=0)

    #: full description of sallable
    description = UnicodeCol(default='')

    #: maximum discount allowed
    max_discount = PercentCol(default=0)

    #: commission to pay after selling this sellable
    commission = PercentCol(default=0)

    notes = UnicodeCol(default='')

    unit_id = IntCol(default=None)

    #: unit of the sellable, kg/l etc
    unit = Reference(unit_id, 'SellableUnit.id')

    image_id = IntCol(default=None)
    image = Reference(image_id, 'Image.id')

    category_id = IntCol(default=None)

    #: a reference to category table
    category = Reference(category_id, 'SellableCategory.id')
    tax_constant_id = IntCol(default=None)
    tax_constant = Reference(tax_constant_id, 'SellableTaxConstant.id')

    product = Reference('id', 'Product.sellable_id', on_remote=True)
    service = Reference('id', 'Service.sellable_id', on_remote=True)

    default_sale_cfop_id = IntCol(default=None)
    default_sale_cfop = Reference(default_sale_cfop_id, 'CfopData.id')

    #: A special price used when we have a "on sale" state, this
    #: can be used for promotions
    on_sale_price = PriceCol(default=0)
    on_sale_start_date = DateTimeCol(default=None)
    on_sale_end_date = DateTimeCol(default=None)

    def __init__(self, store=None,
                 category=None,
                 cost=None,
                 commission=None,
                 description=None,
                 price=None):
        """Creates a new sellable
        :param store: a store
        :param category: category of this sellable
        :param cost: the cost, defaults to 0
        :param commission: commission for this sellable
        :param description: readable description of the sellable
        :param price: the price, defaults to 0
        """

        Domain.__init__(self, store=store)

        if category:
            if commission is None:
                commission = category.get_commission()
            if price is None and cost is not None:
                markup = category.get_markup()
                price = self._get_price_by_markup(markup, cost=cost)

        self.category = category
        self.commission = commission or currency(0)
        self.cost = cost or currency(0)
        self.description = description
        self.price = price or currency(0)

    #
    # Helper methods
    #

    def _get_price_by_markup(self, markup, cost=None):
        if cost is None:
            cost = self.cost
        return cost + (cost * (markup / currency(100)))

    def _get_status_string(self):
        if not self.status in self.statuses:
            raise DatabaseInconsistency(_('Invalid status for product got %d')
                                        % self.status)
        return self.statuses[self.status]

    #
    # Properties
    #

    @property
    def product_storable(self):
        """If this is a |product| and has stock, fetch the |storable| for this.
        This is a shortcut to avoid having to do multiple queries and
        check if |product| is set before fetching the |storable|.

        :returns: The |storable| or ``None`` if there isn't one
        """
        from stoqlib.domain.product import Product, Storable
        return self.store.find(Storable, And(Storable.q.product_id == Product.q.id,
                                      Product.q.sellable_id == self.id)).one()

    @property
    def has_image(self):
        return bool(self.image and self.image.image)

    def _get_markup(self):
        if self.cost == 0:
            return Decimal(0)
        return ((self.price / self.cost) - 1) * 100

    def _set_markup(self, markup):
        self.price = self._get_price_by_markup(markup)

    #: ((cost/price)-1)*100
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

        :returns: if the item can be sold
        :rtype: boolean
        """
        # FIXME: Perhaps this should be done elsewhere. Johan 2008-09-26
        if self.service == sysparam(self.store).DELIVERY_SERVICE:
            return True
        return self.status == self.STATUS_AVAILABLE

    def is_unavailable(self):
        """Whether the sellable is unavailable.

        :returns: if the item is unavailable
        :rtype: boolean
        """
        return self.status == self.STATUS_UNAVAILABLE

    def set_unavailable(self):
        """Mark the sellable as unavailable"""
        if self.is_unavailable():
            raise ValueError('This sellable is already unavailable')
        self.status = self.STATUS_UNAVAILABLE

    def is_closed(self):
        """Whether the sellable is closed or not.

        :returns: ``True`` if closed, False otherwise.
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

        ``False`` if the product/service was used in some cases below::

          - Sold or received
          - The |product| is in a |purchase|
        """
        from stoqlib.domain.sale import SaleItem
        if self.store.find(SaleItem, sellable=self).count():
            # FIXME: Find a better way of doing this.
            # Quotes (and maybe other cases) don't go to the history,
            # so make sure there's nothing left on SaleItem referencing
            # this sellable.
            return False

        # If the product is in a purchase.
        from stoqlib.domain.purchase import PurchaseItem
        if self.store.find(PurchaseItem, sellable=self).count():
            return False

        if self.product:
            return self.product.can_remove()
        elif self.service:
            return self.service.can_remove()

        return False

    def can_close(self):
        """Whether we can close this sellable.

        :returns: ``True`` if the product has no stock left or the service
            is not required by the system (i.e. Delivery service is
            required). ``False`` otherwise.
        """
        if self.service:
            return self.service.can_close()
        return self.is_unavailable()

    def get_commission(self):
        return self.commission

    def get_short_description(self):
        """Returns a short description of the current sellable

        :returns: description
        :rtype: string
        """
        return u'%s %s' % (self.id, self.description)

    def get_suggested_markup(self):
        """Returns the suggested markup for the sellable

        :returns: suggested markup
        :rtype: decimal
        """
        return self.category and self.category.get_markup()

    def get_unit_description(self):
        """Returns the sellable category description
        :returns: the category description or an empty string if no category
        was set.
        """
        return self.unit and self.unit.description or u""

    def get_category_description(self):
        """Returns the description of this sellables category
        If it's unset, return the constant from the category, if any

        :returns: sellable category description
        """
        category = self.category
        return category and category.description or u""

    def get_tax_constant(self):
        """Returns the |sellabletaxconstant| for this sellable.
        If it's unset, return the constant from the category, if any

        :returns: the |sellabletaxconstant| or None if unset
        """
        if self.tax_constant:
            return self.tax_constant

        if self.category:
            return self.category.get_tax_constant()

    def get_category_prices(self):
        """Returns all client category prices associated with this sellable.
        """
        return self.store.find(ClientCategoryPrice, sellable=self)

    def get_category_price_info(self, category):
        """Returns the :class:`ClientCategoryPrice` information for the given
        :class:`ClientCategory` and this sellable.

        :returns: the :class:`ClientCategoryPrice` or None
        """
        info = self.store.find(ClientCategoryPrice, sellable=self,
                                     category=category).one()
        return info

    def get_price_for_category(self, category):
        """Given the |clientcategory|, returns the price for that category
        or the default sellable price.

        :param category: a |clientcategory|
        :returns: The value that should be used as a price for this sellable.
        """
        info = self.get_category_price_info(category)
        if info:
            return info.price
        return self.price

    def check_code_exists(self, code):
        """Returns ``True`` if we already have a sellable with the given code
        in the database.
        """
        return self.check_unique_value_exists(self.q.code, code)

    def check_barcode_exists(self, barcode):
        """Returns ``True`` if we already have a sellable with the given barcode
        in the database.
        """
        return self.check_unique_value_exists(self.q.barcode, barcode)

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

        :returns: ``True`` if new quantity is Ok, ``False`` otherwise.
        """
        if self.unit and not self.unit.allow_fraction:
            return not bool(new_quantity % 1)

        return True

    def is_valid_price(self, newprice, category=None):
        """Returns True if the new price respects the maximum discount
        configured for the sellable, otherwise returns ``False``.

        :param newprice: The new price that we are trying to sell this
          sellable for.
        :param category: Optionally define a category that we will get the
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
        obj = self.product or self.service
        obj.on_update()

    #
    # Classmethods
    #

    def remove(self):
        """Remove this sellable from the database (including the |product| or
        |service|).
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

        store = self.store
        self.delete(self.id, store)

    @classmethod
    def get_available_sellables_for_quote_query(cls, store):
        service_sellable = sysparam(store).DELIVERY_SERVICE.sellable
        return And(cls.q.id != service_sellable.id,
                   Or(cls.q.status == cls.STATUS_AVAILABLE,
                      cls.q.status == cls.STATUS_UNAVAILABLE))

    @classmethod
    def get_available_sellables_query(cls, store):
        service = sysparam(store).DELIVERY_SERVICE
        return And(cls.q.id != service.id,
                   cls.q.status == cls.STATUS_AVAILABLE)

    @classmethod
    def get_available_sellables(cls, store):
        """Returns sellable objects which can be added in a |sale|. By
        default a delivery sellable can not be added manually by users
        since a separate dialog is responsible for that.
        """
        query = cls.get_available_sellables_query(store)
        return store.find(cls, query)

    @classmethod
    def get_unblocked_sellables_query(cls, store, storable=False, supplier=None,
                                      consigned=False):
        """Helper method for get_unblocked_sellables"""
        from stoqlib.domain.product import Product, ProductSupplierInfo
        query = And(Or(cls.get_available_sellables_query(store),
                       cls.q.status == cls.STATUS_UNAVAILABLE),
                    cls.q.id == Product.q.sellable_id,
                    Product.q.consignment == consigned)
        if storable:
            from stoqlib.domain.product import Storable
            query = And(query,
                        Sellable.q.id == Product.q.sellable_id,
                        Storable.q.product_id == Product.q.id)

        # FIXME: Inserting ProductSupplierInfo in this query breaks storm
        if supplier:
            query = And(query,
                        Sellable.q.id == Product.q.sellable_id,
                        Product.q.id == ProductSupplierInfo.q.product_id,
                        ProductSupplierInfo.q.supplier_id == supplier.id)

        return query

    @classmethod
    def get_unblocked_sellables(cls, store, storable=False, supplier=None,
                                consigned=False):
        """
        Returns unblocked sellable objects, which means the
        available sellables plus the sold ones.

        :param store: a store
        :param storable: if `True`, only return sellables that also are
          |storable|
        :param supplier: a |supplier| or ``None``, if set limit the returned
          object to this |supplier|
        """
        query = cls.get_unblocked_sellables_query(store, storable, supplier,
                                                  consigned)
        return store.find(cls, query)

    @classmethod
    def get_unavailable_sellables(cls, store):
        """Returns sellable objects which can be added in a |sale|. By
        default a |delivery| sellable can not be added manually by users
        since a separate dialog is responsible for that.
        """
        return store.find(cls, status=cls.STATUS_UNAVAILABLE)

    @classmethod
    def _get_sellables_by_barcode(cls, store, barcode, extra_query):
        sellable = store.find(cls,
            And(Sellable.q.barcode == barcode,
                extra_query)).one()
        if sellable is None:
            raise BarcodeDoesNotExists(
                _("The sellable with barcode '%s' doesn't exists or is "
                  "not available to be sold") % barcode)
        return sellable

    @classmethod
    def get_availables_by_barcode(cls, store, barcode):
        """Returns a list of avaliable sellables that can be sold.
        A sellable that can be sold can have only one possible
        status: STATUS_AVAILABLE

        :param store: a store
        :param barcode: a string representing a sellable barcode
        """
        return cls._get_sellables_by_barcode(
            store, barcode,
            Sellable.q.status == Sellable.STATUS_AVAILABLE)

    @classmethod
    def get_availables_and_unavailable_by_barcode(cls, store, barcode):
        """Returns a list of avaliable sellables and also sellables that
        can be sold.  Here we will get sellables with the following
        statuses: STATUS_AVAILABLE, STATUS_UNAVAILABLE

        :param store: a store
        :param barcode: a string representing a sellable barcode
        """
        statuses = [cls.STATUS_AVAILABLE, cls.STATUS_UNAVAILABLE]
        return cls._get_sellables_by_barcode(store, barcode,
                                             In(cls.q.status, statuses))

    @classmethod
    def get_unblocked_by_categories(cls, store, categories,
                                    include_uncategorized=True):
        """Returns the available sellables by a list of categories.

        :param store: a store
        :param categories: a list of SellableCategory instances
        :param include_uncategorized: whether or not include the sellables
            without a category
        """
        #FIXME: This query should be faster, waiting for #3696

        if include_uncategorized:
            categories.append(None)
        for sellable in cls.get_unblocked_sellables(store):
            if sellable.category in categories:
                yield sellable
