# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
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

This module contains classes for working with loans.

The main class is :class:`Loan` which can hold a
set of :class:`LoanItem`.
"""

# pylint: enable=E1101

from decimal import Decimal

from kiwi.currency import currency
from kiwi.python import Settable
from storm.references import Reference, ReferenceSet
from zope.interface import implementer

from stoqlib.database.expr import Round
from stoqlib.database.properties import (UnicodeCol, DateTimeCol, PriceCol,
                                         QuantityCol, IdentifierCol,
                                         IdCol, EnumCol)
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IContainer, IInvoice, IInvoiceItem
from stoqlib.domain.product import StockTransactionHistory
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.lib.dateutils import localnow
from stoqlib.lib.defaults import DECIMAL_PRECISION, quantize
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


@implementer(IInvoiceItem)
class LoanItem(Domain):
    """An item in a :class:`loan <Loan>`

    Note that when changing :obj:`~.quantity`, :obj:`~.return_quantity`
    or :obj:`~.sale_quantity` you will need to call :meth:`.sync_stock`
    to synchronize the stock (increase or decrease it).

    Also note that objects of this type should never be created manually, only
    by calling :meth:`Loan.add_sellable`

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/loan_item.html>`__
    """
    __storm_table__ = 'loan_item'

    #: The total quantity that was loaned. The product stock for this
    #: will be decreased when the loan stock is synchonized
    quantity = QuantityCol()

    #: The loadned quantity that was sold. Will increase stock so
    #: it's decreased correctly when the
    #: :class:`sale <stoqlib.domain.sale.Sale>` is confirmed
    sale_quantity = QuantityCol(default=Decimal(0))

    #: The loaned quantity that was returned. Will increase stock
    return_quantity = QuantityCol(default=Decimal(0))

    #: price to use for this :obj:`~.sellable` when creating
    #: a :class:`sale <stoqlib.domain.sale.Sale>`
    price = PriceCol()

    #: original price of a sellable
    base_price = PriceCol()

    sellable_id = IdCol(allow_none=False)

    #: :class:`sellable <stoqlib.domain.sellable.Sellable>` that is loaned
    #: cannot be *None*
    sellable = Reference(sellable_id, 'Sellable.id')

    batch_id = IdCol()

    #: If the sellable is a storable, the |batch| that it was returned in
    batch = Reference(batch_id, 'StorableBatch.id')

    loan_id = IdCol()

    #: :class:`loan <Loan>` this item belongs to
    loan = Reference(loan_id, 'Loan.id')

    def __init__(self, *args, **kwargs):
        # stores the total quantity that was loaned before synching stock
        self._original_quantity = 0
        # stores the loaned quantity that was returned before synching stock
        self._original_return_quantity = self.return_quantity

        super(LoanItem, self).__init__(*args, **kwargs)

    def __storm_loaded__(self):
        super(LoanItem, self).__storm_loaded__()
        self._original_quantity = self.quantity
        self._original_return_quantity = self.return_quantity

    @property
    def branch(self):
        return self.loan.branch

    @property
    def storable(self):
        return self.sellable.product_storable

    #
    # IInvoiceItem implementation
    #

    @property
    def icms_info(self):
        # FIXME: We must return the ICMS values, based on calculation between
        # the ProductIcmsTemplate and the loan_item.
        return None

    @property
    def ipi_info(self):
        # FIXME: We must return the IPI values, based on calculation between
        # the ProductIpiTemplate and the loan_item.
        return None

    @property
    def nfe_cfop_code(self):
        client_address = self.loan.client.person.get_main_address()
        our_address = self.loan.branch.person.get_main_address()

        same_state = True
        if (our_address.city_location.state != client_address.city_location.state):
            same_state = False

        if same_state:
            return u'5917'
        else:
            return u'6917'

    def sync_stock(self):
        """Synchronizes the stock, increasing/decreasing it accordingly.
        Using the stored values when this object is created/loaded, compute how
        much we should increase or decrease the stock quantity.

        When setting :obj:`~.quantity`, :obj:`~.return_quantity`
        or :obj:`~.sale_quantity` be sure to call this to properly
        synchronize the stock (increase or decrease it). That counts
        for object creation too.
        """
        loaned = self._original_quantity - self.quantity
        returned = self.return_quantity - self._original_return_quantity
        diff_quantity = loaned + returned

        if diff_quantity > 0:
            self.storable.increase_stock(diff_quantity, self.branch,
                                         StockTransactionHistory.TYPE_RETURNED_LOAN,
                                         self.id, batch=self.batch)
        elif diff_quantity < 0:
            diff_quantity = - diff_quantity
            self.storable.decrease_stock(diff_quantity, self.branch,
                                         StockTransactionHistory.TYPE_LOANED,
                                         self.id, batch=self.batch)

        # Reset the values used to calculate the stock quantity, just like
        # when the object as loaded from the database again.
        self._original_quantity = self.quantity
        self._original_return_quantity = self.return_quantity

    def get_remaining_quantity(self):
        """The remaining quantity that wasn't returned/sold yet

        This is the same as
        :obj:`.quantity` - :obj:`.sale_quantity` - :obj:`.return_quantity`
        """
        return self.quantity - self.sale_quantity - self.return_quantity

    def get_quantity_unit_string(self):
        return u"%s %s" % (self.quantity,
                           self.sellable.unit_description)

    def get_total(self):
        return currency(self.price * self.quantity)

    def set_discount(self, discount):
        """Apply *discount* on this item

        Note that the discount will be applied based on :obj:`.base_price`
        and then substitute :obj:`.price`, making any previous
        discount/surcharge being lost

        :param decimal.Decimal discount: the discount to be applied
            as a percentage, e.g. 10.0, 22.5
        """
        self.price = quantize(self.base_price * (1 - discount / 100))


@implementer(IContainer)
@implementer(IInvoice)
class Loan(Domain):
    """
    A loan is a collection of |sellable| that is being loaned
    to a |client|, the items are expected to be either be
    returned to stock or sold via a |sale|.

    A loan that can hold a set of :class:`loan items <LoanItem>`

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/loan.html>`__
    `manual <http://doc.stoq.com.br/manual/loan.html>`__
    """

    __storm_table__ = 'loan'

    #: The request for a loan has been added to the system,
    #: we know which of the items the client wishes to loan,
    #: it's not defined if the client has actually picked up
    #: the items.
    STATUS_OPEN = u'open'

    #: All the products or other sellable items have been
    #: returned and are available in stock.
    STATUS_CLOSED = u'closed'

    # FIXME: This is missing a few states,
    #        STATUS_LOANED: stock is completely synchronized
    statuses = {STATUS_OPEN: _(u'Opened'),
                STATUS_CLOSED: _(u'Closed')}

    #: A numeric identifier for this object. This value should be used instead of
    #: :obj:`Domain.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IdentifierCol()

    #: status of the loan
    status = EnumCol(allow_none=False, default=STATUS_OPEN)

    #: notes related to this loan.
    notes = UnicodeCol(default=u'')

    #: date loan was opened
    open_date = DateTimeCol(default_factory=localnow)

    #: date loan was closed
    close_date = DateTimeCol(default=None)

    #: loan expires on this date, we expect the items to
    #: to be returned by this date
    expire_date = DateTimeCol(default=None)

    removed_by = UnicodeCol(default=u'')

    #: branch where the loan was done
    branch_id = IdCol()
    branch = Reference(branch_id, 'Branch.id')

    #: :class:`user <stoqlib.domain.person.LoginUser>` of the system
    #: that made the loan
    # FIXME: Should probably be a SalesPerson, we can find the
    #        LoginUser via te.user_id
    responsible_id = IdCol()
    responsible = Reference(responsible_id, 'LoginUser.id')

    #: client that loaned the items
    client_id = IdCol(default=None)
    client = Reference(client_id, 'Client.id')

    client_category_id = IdCol(default=None)

    #: the |clientcategory| used for price determination.
    client_category = Reference(client_category_id, 'ClientCategory.id')

    #: a list of all items loaned in this loan
    loaned_items = ReferenceSet('id', 'LoanItem.loan_id')

    #: |payments| generated by this loan
    payments = None

    #: |transporter| used in loan
    transporter = None

    #
    # Classmethods
    #

    @classmethod
    def get_status_name(cls, status):
        if not status in cls.statuses:
            raise DatabaseInconsistency(_("Invalid status %d") % status)
        return cls.statuses[status]

    #
    # IContainer implementation
    #

    def add_item(self, loan_item):
        assert not loan_item.loan
        loan_item.loan = self

    def get_items(self):
        return self.store.find(LoanItem, loan=self)

    def remove_item(self, loan_item):
        loan_item.loan = None
        self.store.maybe_remove(loan_item)

    #
    # IInvoice implementation
    #

    @property
    def comments(self):
        return [Settable(comment=self.notes)]

    @property
    def discount_value(self):
        discount = currency(0)
        for item in self.get_items():
            if item.price > item.sellable.base_price:
                continue
            discount += item.sellable.base_price - item.price
        return discount

    @property
    def invoice_subtotal(self):
        return self.get_sale_base_subtotal()

    @property
    def invoice_total(self):
        return self.get_total_amount()

    @property
    def recipient(self):
        return self.client.person

    @property
    def invoice_number(self):
        # TODO: After, use the invoice number that will be saved in new database table (Invoice)
        return 1

    @property
    def operation_nature(self):
        # TODO: Save the operation nature in new loan table field.
        return _(u"Loan")

    #
    # Public API
    #

    def add_sellable(self, sellable, quantity=1, price=None, batch=None):
        """Adds a new sellable item to a loan

        :param sellable: the |sellable|
        :param quantity: quantity to add, defaults to 1
        :param price: optional, the price, it not set the price
          from the sellable will be used
        :param batch: the |batch| this sellable comes from if the sellable is a
          storable. Should be ``None`` if it is not a storable or if the storable
          does not have batches.
        """
        self.validate_batch(batch, sellable=sellable)
        price = price or sellable.price
        base_price = sellable.price
        return LoanItem(store=self.store,
                        quantity=quantity,
                        loan=self,
                        sellable=sellable,
                        batch=batch,
                        price=price,
                        base_price=base_price)

    def get_available_discount_for_items(self, user=None, exclude_item=None):
        """Get available discount for items in this loan

        The available items discount is the total discount not used
        by items in this sale. For instance, if we have 2 products
        with a price of 100 and they can have 10% of discount, we have
        20 of discount available. If one of those products price
        is set to 98, that is, using 2 of it's discount, the available
        discount is now 18.

        :param user: passed to
            :meth:`stoqlib.domain.sellable.Sellable.get_maximum_discount`
            together with :obj:`.client_category` to check for the max
            discount for sellables on this sale
        :param exclude_item: a |saleitem| to exclude from the calculations.
            Useful if you are trying to get some extra discount for that
            item and you don't want it's discount to be considered here
        :returns: the available discount
        """
        available_discount = currency(0)
        used_discount = currency(0)

        for item in self.get_items():
            if item == exclude_item:
                continue
            # Don't put surcharges on the discount, or it can end up negative
            if item.price > item.sellable.base_price:
                continue

            used_discount += item.sellable.base_price - item.price
            max_discount = item.sellable.get_maximum_discount(
                category=self.client_category, user=user) / 100
            available_discount += item.base_price * max_discount

        return available_discount - used_discount

    def set_items_discount(self, discount):
        """Apply discount on this sale's items

        :param decimal.Decimal discount: the discount to be applied
            as a percentage, e.g. 10.0, 22.5
        """
        new_total = currency(0)

        item = None
        candidate = None
        for item in self.get_items():
            item.set_discount(discount)
            new_total += item.price * item.quantity
            if item.quantity == 1:
                candidate = item

        # Since we apply the discount percentage above, items can generate a
        # 3rd decimal place, that will be rounded to the 2nd, making the value
        # differ. Find that difference and apply it to a sale item, preferable
        # to one with a quantity of 1 since, for instance, applying +0,1 to an
        # item with a quantity of 4 would make it's total +0,4 (+0,3 extra than
        # we are trying to adjust here).
        discount_value = (self.get_sale_base_subtotal() * discount) / 100
        diff = new_total - self.get_sale_base_subtotal() + discount_value
        if diff:
            item = candidate or item
            item.price -= diff

    #
    # Accessors
    #

    def get_total_amount(self):
        """
        Fetches the total value of the loan, that is to be paid by
        the client.

        It can be calculated as::

            Sale total = Sum(product and service prices) + surcharge +
                             interest - discount

        :returns: the total value
        """
        return currency(self.get_items().sum(
            Round(LoanItem.price * LoanItem.quantity,
                        DECIMAL_PRECISION)) or 0)

    def get_client_name(self):
        if self.client:
            return self.client.person.name
        return u''

    def get_branch_name(self):
        if self.branch:
            return self.branch.get_description()
        return u''

    def get_responsible_name(self):
        return self.responsible.person.name

    #
    # Public API
    #

    def sync_stock(self):
        """Synchronizes the stock of *self*'s :class:`loan items <LoanItem>`

        Just a shortcut to call :meth:`LoanItem.sync_stock` of all of
        *self*'s :class:`loan items <LoanItem>` instead of having
        to do that one by one.
        """
        for loan_item in self.get_items():
            # No need to sync stock for products that dont need.
            if not loan_item.sellable.product.manage_stock:
                continue
            loan_item.sync_stock()

    def can_close(self):
        """Checks if the loan can be closed. A loan can be closed if it is
        opened and all the items have been returned or sold.
        :returns: True if the loan can be closed, False otherwise.
        """
        if self.status != Loan.STATUS_OPEN:
            return False
        for item in self.get_items():
            if item.sale_quantity + item.return_quantity != item.quantity:
                return False
        return True

    def get_sale_base_subtotal(self):
        """Get the base subtotal of items

        Just a helper that, unlike :meth:`.get_sale_subtotal`, will
        return the total based on item's base price.

        :returns: the base subtotal
        """
        subtotal = self.get_items().sum(LoanItem.quantity *
                                        LoanItem.base_price)
        return currency(subtotal)

    def close(self):
        """Closes the loan. At this point, all the loan items have been
        returned to stock or sold."""
        assert self.can_close()
        self.close_date = localnow()
        self.status = Loan.STATUS_CLOSED
