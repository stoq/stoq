# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2013 Async Open Source <http://www.async.com.br>
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
"""
Domain objects related to something that can be sold, such a |product|
or a |service|.

* :class:`Sellable` contains the description, price, cost, barcode etc.
* :class:`SellableCategory` provides a way to group sellables together, to be
  able to consistently tax, markup and calculate |commission|.
* :class:`SellableTaxConstant` contains the tax constant sent to an ECF printer.
* :class:`SellableUnit` contains the unit.
* :class:`ClientCategoryPrice` provides a price for |clients| in a |clientcategory|.
"""

# pylint: enable=E1101

from decimal import Decimal

from kiwi.currency import currency
from stoqdrivers.enum import TaxType, UnitType
from storm.expr import And, Or, In, Eq
from storm.references import Reference, ReferenceSet
from zope.interface import implementer

from stoqlib.database.properties import (BoolCol, DateTimeCol, EnumCol,
                                         IdCol, IntCol, PercentCol,
                                         PriceCol, UnicodeCol)
from stoqlib.domain.base import Domain
from stoqlib.domain.events import (CategoryCreateEvent, CategoryEditEvent,
                                   SellableCheckTaxesEvent)
from stoqlib.domain.interfaces import IDescribable
from stoqlib.domain.image import Image
from stoqlib.exceptions import SellableError, TaxError
from stoqlib.lib.defaults import quantize
from stoqlib.lib.dateutils import localnow
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.validators import is_date_in_interval

_ = stoqlib_gettext

# pyflakes: Sellable.has_image requires that Image is imported at least once
Image  # pylint: disable=W0104

#
# Base Domain Classes
#


@implementer(IDescribable)
class SellableUnit(Domain):
    """
    The unit of a |sellable|. For instance: ``Kg`` (kilo), ``l`` (liter) and
    ``h`` (hour)
    When selling a sellable in a |sale|  the quantity of a |saleitem| will
    be entered in this unit.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/sellable_unit.html>`__
    """
    __storm_table__ = 'sellable_unit'

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


@implementer(IDescribable)
class SellableTaxConstant(Domain):
    """A tax constant tied to a sellable

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/sellable_tax_constant.html>`__
    """
    __storm_table__ = 'sellable_tax_constant'

    #: description of this constant
    description = UnicodeCol()

    #: a TaxType constant, used by ECF
    tax_type = IntCol()

    #: the percentage value of the tax
    tax_value = PercentCol(default=None)

    _mapping = {
        int(TaxType.NONE): u'TAX_NONE',                      # Não tributado - ICMS
        int(TaxType.EXEMPTION): u'TAX_EXEMPTION',            # Isento - ICMS
        int(TaxType.SUBSTITUTION): u'TAX_SUBSTITUTION',      # Substituição tributária - ICMS
        int(TaxType.SERVICE): u'TAX_SERVICE',                # ISS
    }

    def get_value(self):
        """
        :returns: the value to pass to ECF
        """
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
@implementer(IDescribable)
class SellableCategory(Domain):
    """ A Sellable category.

    A way to group several |sellables| together, like "Shoes", "Consumer goods",
    "Services".

    A category can define markup, tax and commission, the values of the category
    will only be used when the sellable itself lacks a value.

    Sellable categories can be grouped recursively.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/sellable_category.html>`__
    """
    __storm_table__ = 'sellable_category'

    #: The category description
    description = UnicodeCol()

    #: Define the suggested markup when calculating the sellable's price.
    suggested_markup = PercentCol(default=0)

    #: A percentage comission suggested for all the sales which products
    #: belongs to this category.
    salesperson_commission = PercentCol(default=0)

    category_id = IdCol(default=None)

    #: base category of this category, ``None`` for base categories themselves
    category = Reference(category_id, 'SellableCategory.id')

    tax_constant_id = IdCol(default=None)

    #: the |sellabletaxconstant| for this sellable category
    tax_constant = Reference(tax_constant_id, 'SellableTaxConstant.id')

    #: the children of this category
    children = ReferenceSet('id', 'SellableCategory.category_id')

    #
    #  Properties
    #

    @property
    def full_description(self):
        """The full description of the category, including its parents,
        for instance: u"Clothes:Shoes:Black Shoe 14 SL"
        """

        descriptions = [self.description]

        parent = self.category
        while parent:
            descriptions.append(parent.description)
            parent = parent.category

        return u':'.join(reversed(descriptions))

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
            return self.category.get_markup()
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
    """A table that stores special prices for |clients| based on their
    |clientcategory|.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/client_category_price.html>`__
    """
    __storm_table__ = 'client_category_price'

    sellable_id = IdCol()

    #: The |sellable| that has a special price
    sellable = Reference(sellable_id, 'Sellable.id')

    category_id = IdCol()

    #: The |clientcategory| that has the special price
    category = Reference(category_id, 'ClientCategory.id')

    #: The price for this (|sellable|, |clientcategory|)
    price = PriceCol(default=0)

    #: The max discount that may be applied.
    max_discount = PercentCol(default=0)

    @property
    def markup(self):
        if self.sellable.cost == 0:
            return Decimal(0)
        return ((self.price / self.sellable.cost) - 1) * 100

    @markup.setter
    def markup(self, markup):
        self.price = self.sellable._get_price_by_markup(markup)

    @property
    def category_name(self):
        return self.category.name

    def remove(self):
        """Removes this client category price from the database."""
        self.store.remove(self)


def _validate_code(sellable, attr, code):
    if sellable.check_code_exists(code):
        raise SellableError(
            _(u"The sellable code %r already exists") % (code, ))
    return code


def _validate_barcode(sellable, attr, barcode):
    if sellable.check_barcode_exists(barcode):
        raise SellableError(
            _(u"The sellable barcode %r already exists") % (barcode, ))
    return barcode


@implementer(IDescribable)
class Sellable(Domain):
    """ Sellable information of a certain item such a |product|
    or a |service|.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/sellable.html>`__
    """
    __storm_table__ = 'sellable'

    #: the sellable is available and can be used on a |purchase|/|sale|
    STATUS_AVAILABLE = u'available'

    #: the sellable is closed, that is, it still exists for references,
    #: but it should not be possible to create a |purchase|/|sale| with it
    STATUS_CLOSED = u'closed'

    statuses = {STATUS_AVAILABLE: _(u'Available'),
                STATUS_CLOSED: _(u'Closed')}

    #: a code used internally by the shop to reference this sellable.
    #: It is usually not printed and displayed to |clients|, barcode is for that.
    #: It may be used as an shorter alternative to the barcode.
    code = UnicodeCol(default=u'', validator=_validate_code)

    #: barcode, mostly for products, usually printed and attached to the
    #: package.
    barcode = UnicodeCol(default=u'', validator=_validate_barcode)

    #: status the sellable is in
    status = EnumCol(allow_none=False, default=STATUS_AVAILABLE)

    # FIXME: This is only used for purchase orders without suppliers,
    #        Perhaps we should update this as we purchase the product
    #: cost of the sellable, this is not tied to a specific |supplier|,
    #: which may have a different cost.
    cost = PriceCol(default=0)

    #: price of sellable, how much the |client| paid.
    base_price = PriceCol(default=0)

    #: full description of sellable
    description = UnicodeCol(default=u'')

    #: maximum discount allowed
    max_discount = PercentCol(default=0)

    #: commission to pay after selling this sellable
    commission = PercentCol(default=0)

    #: notes for the sellable
    notes = UnicodeCol(default=u'')

    unit_id = IdCol(default=None)

    #: the |sellableunit|, quantities of this sellable are in this unit.
    unit = Reference(unit_id, 'SellableUnit.id')

    image_id = IdCol(default=None)

    #: the |image|, a picture representing the sellable
    image = Reference(image_id, 'Image.id')

    category_id = IdCol(default=None)

    #: a reference to category table
    category = Reference(category_id, 'SellableCategory.id')

    tax_constant_id = IdCol(default=None)

    #: the |sellabletaxconstant|, this controls how this sellable is taxed
    tax_constant = Reference(tax_constant_id, 'SellableTaxConstant.id')

    #: the |product| for this sellable or ``None``
    product = Reference('id', 'Product.id', on_remote=True)

    #: the |service| for this sellable or ``None``
    service = Reference('id', 'Service.id', on_remote=True)

    #: the |storable| for this |product|'s sellable
    product_storable = Reference('id', 'Storable.id', on_remote=True)

    default_sale_cfop_id = IdCol(default=None)

    #: the default |cfop| that will be used when selling this sellable
    default_sale_cfop = Reference(default_sale_cfop_id, 'CfopData.id')

    #: A special price used when we have a "on sale" state, this
    #: can be used for promotions
    on_sale_price = PriceCol(default=0)

    #: When the promotional/special price starts to apply
    on_sale_start_date = DateTimeCol(default=None)

    #: When the promotional/special price ends
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
        return currency(quantize(cost + (cost * (markup / currency(100)))))

    #
    # Properties
    #

    @property
    def status_str(self):
        """The sellable status as a string"""
        return self.statuses[self.status]

    @property
    def unit_description(self):
        """Returns the description of the |sellableunit| of this sellable

        :returns: the unit description or an empty string if no
          |sellableunit| was set.
        :rtype: unicode
        """
        return self.unit and self.unit.description or u""

    @property
    def markup(self):
        """Markup, the opposite of discount, a value added
        on top of the sale. It's calculated as::
          ((cost/price)-1)*100
        """
        if self.cost == 0:
            return Decimal(0)
        return ((self.price / self.cost) - 1) * 100

    @markup.setter
    def markup(self, markup):
        self.price = self._get_price_by_markup(markup)

    @property
    def price(self):
        if self.is_on_sale():
            return self.on_sale_price
        else:
            return self.base_price

    @price.setter
    def price(self, price):
        if price < 0:
            # Just a precaution for gui validation fails.
            price = 0

        if self.is_on_sale():
            self.on_sale_price = price
        else:
            self.base_price = price

    #
    #  Accessors
    #

    def is_available(self):
        """Whether the sellable is available and can be sold.

        :returns: ``True`` if the item can be sold, ``False`` otherwise.
        """
        # FIXME: Perhaps this should be done elsewhere. Johan 2008-09-26
        if sysparam.compare_object('DELIVERY_SERVICE', self.service):
            return True
        return self.status == self.STATUS_AVAILABLE

    def set_available(self):
        """Mark the sellable as available

        Being available means that it can be ordered or sold.

        :raises: :exc:`ValueError`: if the sellable is already available
        """
        if self.is_available():
            raise ValueError('This sellable is already available')
        self.status = self.STATUS_AVAILABLE

    def is_closed(self):
        """Whether the sellable is closed or not.

        :returns: ``True`` if closed, ``False`` otherwise.
        """
        return self.status == Sellable.STATUS_CLOSED

    def close(self):
        """Mark the sellable as closed.

        After the sellable is closed, this will call the close method of the
        service or product related to this sellable.

        :raises: :exc:`ValueError`: if the sellable is already closed
        """
        if self.is_closed():
            raise ValueError('This sellable is already closed')

        assert self.can_close()
        self.status = Sellable.STATUS_CLOSED

        obj = self.service or self.product
        obj.close()

    def can_remove(self):
        """Whether we can delete this sellable from the database.

        ``False`` if the product/service was used in some cases below::

          - Sold or received
          - The |product| is in a |purchase|
        """
        if self.product and not self.product.can_remove():
            return False

        if self.service and not self.service.can_remove():
            return False

        return super(Sellable, self).can_remove(
            skip=[('product', 'id'),
                  ('service', 'id'),
                  ('client_category_price', 'sellable_id')])

    def can_close(self):
        """Whether we can close this sellable.

        :returns: ``True`` if the product has no stock left or the service
            is not required by the system (i.e. Delivery service is
            required). ``False`` otherwise.
        """
        obj = self.service or self.product
        return obj.can_close()

    def get_commission(self):
        return self.commission

    def get_suggested_markup(self):
        """Returns the suggested markup for the sellable

        :returns: suggested markup
        :rtype: decimal
        """
        return self.category and self.category.get_markup()

    def get_category_description(self):
        """Returns the description of this sellables category
        If it's unset, return the constant from the category, if any

        :returns: sellable category description or an empty string if no
          |sellablecategory| was set.
        :rtype: unicode
        """
        category = self.category
        return category and category.description or u""

    def get_tax_constant(self):
        """Returns the |sellabletaxconstant| for this sellable.
        If it's unset, return the constant from the category, if any

        :returns: the |sellabletaxconstant| or ``None`` if unset
        """
        if self.tax_constant:
            return self.tax_constant

        if self.category:
            return self.category.get_tax_constant()

    def get_category_prices(self):
        """Returns all client category prices associated with this sellable.

        :returns: the client category prices
        """
        return self.store.find(ClientCategoryPrice, sellable=self)

    def get_category_price_info(self, category):
        """Returns the :class:`ClientCategoryPrice` information for the given
        :class:`ClientCategory` and this |sellable|.

        :returns: the :class:`ClientCategoryPrice` or ``None``
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

    def get_maximum_discount(self, category=None, user=None):
        user_discount = user.profile.max_discount if user else 0
        if category is not None:
            info = self.get_category_price_info(category) or self
        else:
            info = self

        return max(user_discount, info.max_discount)

    def check_code_exists(self, code):
        """Check if there is another sellable with the same code.

        :returns: ``True`` if we already have a sellable with the given code
          ``False`` otherwise.
        """
        return self.check_unique_value_exists(Sellable.code, code)

    def check_barcode_exists(self, barcode):
        """Check if there is another sellable with the same barcode.

        :returns: ``True`` if we already have a sellable with the given barcode
          ``False`` otherwise.
        """
        return self.check_unique_value_exists(Sellable.barcode, barcode)

    def check_taxes_validity(self):
        """Check if icms taxes are valid.

        This check is done because some icms taxes (such as CSOSN 101) have
        a 'valid until' field on it. If these taxes has expired, we cannot sell
        the sellable.
        Check this method using assert inside a try clause.

        :raises: :exc:`TaxError` if there are any issues with the sellable taxes.
        """
        icms_template = self.product and self.product.icms_template
        SellableCheckTaxesEvent.emit(self)
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

    def is_on_sale(self):
        """Check if the price is currently on sale.

        :return: ``True`` if it is on sale, ``False`` otherwise
        """
        if not self.on_sale_price:
            return False

        return is_date_in_interval(
            localnow(), self.on_sale_start_date, self.on_sale_end_date)

    def is_valid_quantity(self, new_quantity):
        """Whether the new quantity is valid for this sellable or not.

        If the new quantity is fractioned, check on this sellable unit if it
        allows fractioned quantities. If not, this new quantity cannot be used.

        Note that, if the sellable lacks a unit, we will not allow
        fractions either.

        :returns: ``True`` if new quantity is Ok, ``False`` otherwise.
        """
        if self.unit and not self.unit.allow_fraction:
            return not bool(new_quantity % 1)

        return True

    def is_valid_price(self, newprice, category=None, user=None,
                       extra_discount=None):
        """Checks if *newprice* is valid for this sellable

        Returns a dict indicating whether the new price is a valid price as
        allowed by the discount by the user, by the category or by the sellable
        maximum discount

        :param newprice: The new price that we are trying to sell this
            sellable for
        :param category: Optionally define a |clientcategory| that we will get
            the price info from
        :param user: The user role may allow a different discount percentage.
        :param extra_discount: some extra discount for the sellable
            to be considered for the min_price
        :returns: A dict with the following keys:
            * is_valid: ``True`` if the price is valid, else ``False``
            * min_price: The minimum price for this sellable.
            * max_discount: The maximum discount for this sellable.
        """
        if category is not None:
            info = self.get_category_price_info(category) or self
        else:
            info = self

        max_discount = self.get_maximum_discount(category=category, user=user)
        min_price = info.price * (1 - max_discount / 100)

        if extra_discount is not None:
            # The extra discount can be greater than the min_price, and
            # a negative min_price doesn't make sense
            min_price = max(currency(0), min_price - extra_discount)

        return {
            'is_valid': newprice >= min_price,
            'min_price': min_price,
            'max_discount': max_discount,
        }

    def copy_sellable(self, target=None):
        """This method copies self to another sellable

        If the |sellable| target is None, a new sellable is created.

        :param target: The |sellable| target for the copy
        returns: a |sellable| identical to self
        """
        if target is None:
            target = Sellable(store=self.store)

        props = ['base_price', 'category_id', 'cost', 'max_discount',
                 'commission', 'notes', 'unit_id', 'tax_constant_id',
                 'default_sale_cfop_id', 'on_sale_price', 'on_sale_start_date',
                 'on_sale_end_date']

        for prop in props:
            value = getattr(self, prop)
            setattr(target, prop, value)

        return target

    #
    # IDescribable implementation
    #

    def get_description(self, full_description=False):
        desc = self.description
        if full_description and self.get_category_description():
            desc = u"[%s] %s" % (self.get_category_description(), desc)

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
        """
        Remove this sellable. This will also remove the |product| or
        |sellable| and |categoryprice|
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

        self.store.remove(self)

    @classmethod
    def get_available_sellables_query(cls, store):
        """Get the sellables that are available and can be sold.

        For instance, this will filter out the internal sellable used
        by a |delivery|.

        This is similar to `.get_available_sellables`, but it returns
        a query instead of the actual results.

        :param store: a store
        :returns: a query expression
        """

        delivery = sysparam.get_object(store, 'DELIVERY_SERVICE')
        return And(cls.id != delivery.sellable.id,
                   cls.status == cls.STATUS_AVAILABLE)

    @classmethod
    def get_available_sellables(cls, store):
        """Get the sellables that are available and can be sold.

        For instance, this will filter out the internal sellable used
        by a |delivery|.

        :param store: a store
        :returns: a resultset with the available sellables
        """
        query = cls.get_available_sellables_query(store)
        return store.find(cls, query)

    @classmethod
    def get_unblocked_sellables_query(cls, store, storable=False, supplier=None,
                                      consigned=False):
        """Helper method for get_unblocked_sellables

        When supplier is not ```None``, you should use this query only with
        Viewables that join with supplier, like ProductFullStockSupplierView.

        :param store: a store
        :param storable: if ``True``, we should filter only the sellables that
          are also a |storable|.
        :param supplier: |supplier| to filter on or ``None``
        :param consigned: if the sellables are consigned

        :returns: a query expression
        """
        from stoqlib.domain.product import Product, ProductSupplierInfo
        query = And(cls.get_available_sellables_query(store),
                    cls.id == Product.id,
                    Product.consignment == consigned)
        if storable:
            from stoqlib.domain.product import Storable
            query = And(query,
                        Sellable.id == Product.id,
                        Storable.id == Product.id)

        if supplier:
            query = And(query,
                        Sellable.id == Product.id,
                        Product.id == ProductSupplierInfo.product_id,
                        ProductSupplierInfo.supplier_id == supplier.id)

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

        :rtype: queryset of sellables
        """
        query = cls.get_unblocked_sellables_query(store, storable, supplier,
                                                  consigned)
        return store.find(cls, query)

    @classmethod
    def get_unblocked_by_categories_query(cls, store, categories,
                                          include_uncategorized=True):
        """Returns the available sellables by a list of categories.

        :param store: a store
        :param categories: a list of SellableCategory instances
        :param include_uncategorized: whether or not include the sellables
            without a category

        :rtype: generator of sellables
        """
        queries = []
        if len(categories):
            queries.append(In(Sellable.category_id, [c.id for c in categories]))
        if include_uncategorized:
            queries.append(Eq(Sellable.category_id, None))

        query = cls.get_unblocked_sellables_query(store)
        return And(query, Or(*queries))
