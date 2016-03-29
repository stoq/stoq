# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Purchase management """

# pylint: enable=E1101

import collections
from decimal import Decimal

from kiwi.currency import currency
from kiwi.python import Settable
from storm.expr import (Alias, And, Cast, Coalesce, Count, Eq, Join, LeftJoin,
                        Select, Sum)
from storm.info import ClassAlias
from storm.references import Reference, ReferenceSet
from zope.interface import implementer

from stoqlib.database.expr import Date, Field, NullIf, TransactionTimestamp
from stoqlib.database.properties import (DateTimeCol, UnicodeCol,
                                         PriceCol, BoolCol, QuantityCol,
                                         IdentifierCol, IdCol, EnumCol)
from stoqlib.database.runtime import get_current_user
from stoqlib.database.viewable import Viewable
from stoqlib.domain.base import Domain
from stoqlib.domain.event import Event
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.product import StockTransactionHistory, Storable
from stoqlib.domain.interfaces import IContainer, IDescribable
from stoqlib.domain.person import (Person, Branch, Company, Supplier,
                                   Transporter, LoginUser)
from stoqlib.domain.sellable import Sellable, SellableUnit
from stoqlib.exceptions import DatabaseInconsistency, StoqlibError
from stoqlib.lib.dateutils import localnow
from stoqlib.lib.defaults import quantize
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.formatters import format_quantity, get_formatted_price


_ = stoqlib_gettext


class PurchaseItem(Domain):
    """This class stores information of the purchased items.
    """

    __storm_table__ = 'purchase_item'

    quantity = QuantityCol(default=1)
    quantity_received = QuantityCol(default=0)
    quantity_sold = QuantityCol(default=0)
    quantity_returned = QuantityCol(default=0)

    #: the cost which helps the purchaser to define the
    #: main cost of a certain product.
    base_cost = PriceCol()

    cost = PriceCol()
    expected_receival_date = DateTimeCol(default=None)

    sellable_id = IdCol()

    #: the |sellable|
    sellable = Reference(sellable_id, 'Sellable.id')

    order_id = IdCol()

    #: the |purchase|
    order = Reference(order_id, 'PurchaseOrder.id')

    parent_item_id = IdCol()
    parent_item = Reference(parent_item_id, 'PurchaseItem.id')

    children_items = ReferenceSet('id', 'PurchaseItem.parent_item_id')

    def __init__(self, store=None, **kw):
        if not 'sellable' in kw:
            raise TypeError('You must provide a sellable argument')
        if not 'order' in kw:
            raise TypeError('You must provide a order argument')

        # FIXME: Avoding shadowing sellable.cost
        kw['base_cost'] = kw['sellable'].cost

        if not 'cost' in kw:
            kw['cost'] = kw['sellable'].cost

        Domain.__init__(self, store=store, **kw)

    #
    # Accessors
    #

    def get_total(self):
        return currency(self.quantity * self.cost)

    def get_total_sold(self):
        return currency(self.quantity_sold * self.cost)

    def get_received_total(self):
        return currency(self.quantity_received * self.cost)

    def has_been_received(self):
        return self.quantity_received >= self.quantity

    def has_partial_received(self):
        return self.quantity_received > 0

    def get_pending_quantity(self):
        return self.quantity - self.quantity_received

    def get_quantity_as_string(self):
        unit = self.sellable.unit
        return u"%s %s" % (format_quantity(self.quantity),
                           unit and unit.description or u"")

    def get_quantity_received_as_string(self):
        unit = self.sellable.unit
        return u"%s %s" % (format_quantity(self.quantity_received),
                           unit and unit.description or u"")

    @classmethod
    def get_ordered_quantity(cls, store, sellable):
        """Returns the quantity already ordered of a given sellable.

        :param store: a store
        :param sellable: the sellable we want to know the quantity ordered.
        :returns: the quantity already ordered of a given sellable or zero if
          no quantity have been ordered.
        """
        query = And(PurchaseItem.sellable_id == sellable.id,
                    PurchaseOrder.id == PurchaseItem.order_id,
                    PurchaseOrder.status == PurchaseOrder.ORDER_CONFIRMED)
        ordered_items = store.find(PurchaseItem, query)
        return ordered_items.sum(PurchaseItem.quantity) or Decimal(0)

    def return_consignment(self, quantity):
        """
        Return this as a consignment item

        :param quantity: the quantity to return
        """
        storable = self.sellable.product_storable
        assert storable
        storable.decrease_stock(quantity=quantity,
                                branch=self.order.branch,
                                type=StockTransactionHistory.TYPE_CONSIGNMENT_RETURNED,
                                object_id=self.id)

    def get_component_quantity(self, parent):
        """Get the quantity of a component.

        :param parent: the |purchase_item| parent_item of self
        :returns: the quantity of the component
        """
        for component in parent.sellable.product.get_components():
            if self.sellable.product == component.component:
                return component.quantity


@implementer(IContainer)
class PurchaseOrder(Domain):
    """Purchase and order definition."""

    __storm_table__ = 'purchase_order'

    ORDER_QUOTING = u'quoting'
    ORDER_PENDING = u'pending'
    ORDER_CONFIRMED = u'confirmed'
    ORDER_CONSIGNED = u'consigned'
    ORDER_CANCELLED = u'cancelled'
    ORDER_CLOSED = u'closed'

    statuses = collections.OrderedDict([
        (ORDER_QUOTING, _(u'Quoting')),
        (ORDER_PENDING, _(u'Pending')),
        (ORDER_CONFIRMED, _(u'Confirmed')),
        (ORDER_CONSIGNED, _(u'Consigned')),
        (ORDER_CANCELLED, _(u'Cancelled')),
        (ORDER_CLOSED, _(u'Closed')),
    ])

    FREIGHT_FOB = u'fob'
    FREIGHT_CIF = u'cif'

    freight_types = {FREIGHT_FOB: _(u'FOB'),
                     FREIGHT_CIF: _(u'CIF')}

    #: A numeric identifier for this object. This value should be used instead of
    #: :obj:`Domain.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IdentifierCol()

    status = EnumCol(allow_none=False, default=ORDER_QUOTING)
    open_date = DateTimeCol(default_factory=localnow, allow_none=False)
    quote_deadline = DateTimeCol(default=None)
    expected_receival_date = DateTimeCol(default_factory=localnow)
    expected_pay_date = DateTimeCol(default_factory=localnow)
    receival_date = DateTimeCol(default=None)
    confirm_date = DateTimeCol(default=None)
    notes = UnicodeCol(default=u'')
    salesperson_name = UnicodeCol(default=u'')
    freight_type = EnumCol(allow_none=False, default=FREIGHT_FOB)
    expected_freight = PriceCol(default=0)

    surcharge_value = PriceCol(default=0)
    discount_value = PriceCol(default=0)

    consigned = BoolCol(default=False)
    supplier_id = IdCol()
    supplier = Reference(supplier_id, 'Supplier.id')
    branch_id = IdCol()
    branch = Reference(branch_id, 'Branch.id')
    transporter_id = IdCol(default=None)
    transporter = Reference(transporter_id, 'Transporter.id')
    responsible_id = IdCol()
    responsible = Reference(responsible_id, 'LoginUser.id')
    group_id = IdCol()
    group = Reference(group_id, 'PaymentGroup.id')

    #
    # IContainer Implementation
    #

    def get_items(self, with_children=True):
        """Get the items of the purchase order

        :param with_children: indicate if we should fetch children_items or not
        """
        query = PurchaseItem.order == self
        if not with_children:
            query = And(query, Eq(PurchaseItem.parent_item_id, None))
        return self.store.find(PurchaseItem, query)

    def remove_item(self, item):
        if item.order is not self:
            raise ValueError(_(u'Argument item must have an order attribute '
                               'associated with the current purchase instance'))
        item.order = None
        self.store.maybe_remove(item)

    def add_item(self, sellable, quantity=Decimal(1), parent=None):
        store = self.store
        return PurchaseItem(store=store, order=self,
                            sellable=sellable, quantity=quantity,
                            parent_item=parent)

    #
    # Properties
    #

    @property
    def discount_percentage(self):
        """Discount by percentage.
        Note that percentage must be added as an absolute value not as a
        factor like 1.05 = 5 % of surcharge
        The correct form is 'percentage = 3' for a discount of 3 %"""
        discount_value = self.discount_value
        if not discount_value:
            return currency(0)
        subtotal = self.purchase_subtotal
        assert subtotal > 0, (u'the subtotal should not be zero '
                              u'at this point')
        total = subtotal - discount_value
        percentage = (1 - total / subtotal) * 100
        return quantize(percentage)

    @discount_percentage.setter
    def discount_percentage(self, value):
        self.discount_value = self._get_percentage_value(value)

    @property
    def surcharge_percentage(self):
        """Surcharge by percentage.
        Note that surcharge must be added as an absolute value not as a
        factor like 0.97 = 3 % of discount.
        The correct form is 'percentage = 3' for a surcharge of 3 %"""
        surcharge_value = self.surcharge_value
        if not surcharge_value:
            return currency(0)
        subtotal = self.purchase_subtotal
        assert subtotal > 0, (u'the subtotal should not be zero '
                              u'at this point')
        total = subtotal + surcharge_value
        percentage = ((total / subtotal) - 1) * 100
        return quantize(percentage)

    @surcharge_percentage.setter
    def surcharge_percentage(self, value):
        self.surcharge_value = self._get_percentage_value(value)

    @property
    def payments(self):
        """Returns all valid payments for this purchase

        This will return a list of valid payments for this purchase, that
        is, all payments on the payment group that were not cancelled.
        If you need to get the cancelled too, use self.group.payments.

        :returns: a list of |payment|
        """
        return self.group.get_valid_payments()

    #
    # Private
    #

    def _get_percentage_value(self, percentage):
        if not percentage:
            return currency(0)
        subtotal = self.purchase_subtotal
        percentage = Decimal(percentage)
        return subtotal * (percentage / 100)

    def _payback_paid_payments(self):
        paid_value = self.group.get_total_paid()

        # If we didn't pay anything yet, there is no need to create a payback.
        if not paid_value:
            return

        money = PaymentMethod.get_by_name(self.store, u'money')
        payment = money.create_payment(
            Payment.TYPE_IN, self.group, self.branch,
            paid_value, description=_(u'%s Money Returned for Purchase %s') % (
                u'1/1', self.identifier))
        payment.set_pending()
        payment.pay()

    #
    # Public API
    #

    def is_paid(self):
        for payment in self.payments:
            if not payment.is_paid():
                return False
        return True

    def can_cancel(self):
        """Find out if it's possible to cancel the order

        :returns: True if it's possible to cancel the order, otherwise False
        """
        # FIXME: Canceling partial orders disabled until we fix bug 3282
        for item in self.get_items():
            if item.has_partial_received():
                return False
        return self.status in [self.ORDER_QUOTING,
                               self.ORDER_PENDING,
                               self.ORDER_CONFIRMED]

    def can_close(self):
        """Find out if it's possible to close the order

        :returns: True if it's possible to close the order, otherwise False
        """

        # Consigned orders can be closed only after being confirmed
        if self.status == self.ORDER_CONSIGNED:
            return False

        for item in self.get_items():
            if not item.has_been_received():
                return False
        return True

    def confirm(self, confirm_date=None):
        """Confirms the purchase order

        :param confirm_data: optional, datetime
        """
        if confirm_date is None:
            confirm_date = TransactionTimestamp()

        if self.status not in [PurchaseOrder.ORDER_PENDING,
                               PurchaseOrder.ORDER_CONSIGNED]:
            fmt = _(u'Invalid order status, it should be '
                    u'ORDER_PENDING or ORDER_CONSIGNED, got %s')
            raise ValueError(fmt % (self.status_str, ))

        # In consigned purchases there is no payments at this point.
        if self.status != PurchaseOrder.ORDER_CONSIGNED:
            for payment in self.payments:
                payment.set_pending()

        if self.supplier:
            self.group.recipient = self.supplier.person

        self.responsible = get_current_user(self.store)
        self.status = PurchaseOrder.ORDER_CONFIRMED
        self.confirm_date = confirm_date

        Event.log(self.store, Event.TYPE_ORDER,
                  _(u"Order %s, total value %2.2f, supplier '%s' "
                    u"is now confirmed") % (self.identifier,
                                            self.purchase_total,
                                            self.supplier.person.name))

    def set_consigned(self):
        if self.status != PurchaseOrder.ORDER_PENDING:
            raise ValueError(
                _(u'Invalid order status, it should be '
                  u'ORDER_PENDING, got %s') % (self.status_str, ))

        self.responsible = get_current_user(self.store)
        self.status = PurchaseOrder.ORDER_CONSIGNED

    def close(self):
        """Closes the purchase order
        """
        if self.status != PurchaseOrder.ORDER_CONFIRMED:
            raise ValueError(_(u'Invalid status, it should be confirmed '
                               u'got %s instead') % self.status_str)
        self.status = self.ORDER_CLOSED

        Event.log(self.store, Event.TYPE_ORDER,
                  _(u"Order %s, total value %2.2f, supplier '%s' "
                    u"is now closed") % (self.identifier,
                                         self.purchase_total,
                                         self.supplier.person.name))

    def cancel(self):
        """Cancels the purchase order
        """
        assert self.can_cancel()

        # we have to cancel the payments too
        self._payback_paid_payments()
        self.group.cancel()

        self.status = self.ORDER_CANCELLED

    def receive_item(self, item, quantity_to_receive):
        if not item in self.get_pending_items():
            raise StoqlibError(_(u'This item is not pending, hence '
                                 u'cannot be received'))
        quantity = item.quantity - item.quantity_received
        if quantity < quantity_to_receive:
            raise StoqlibError(_(u'The quantity that you want to receive '
                                 u'is greater than the total quantity of '
                                 u'this item %r') % item)
        self.increase_quantity_received(item, quantity_to_receive)

    def increase_quantity_received(self, purchase_item, quantity_received):
        sellable = purchase_item.sellable
        items = [item for item in self.get_items()
                 if item.sellable.id == sellable.id]
        qty = len(items)
        if not qty:
            raise ValueError(_(u'There is no purchase item for '
                               u'sellable %r') % sellable)

        purchase_item.quantity_received += quantity_received

    def update_products_cost(self):
        """Update purchase's items cost

        Update the costs of all products on this purchase
        to the costs specified in the order.
        """
        for item in self.get_items():
            item.sellable.cost = item.cost
            product = item.sellable.product
            product_supplier = product.get_product_supplier_info(self.supplier)
            product_supplier.base_cost = item.cost

    @property
    def status_str(self):
        return PurchaseOrder.translate_status(self.status)

    @property
    def freight_type_name(self):
        if not self.freight_type in self.freight_types.keys():
            raise DatabaseInconsistency(_(u'Invalid freight_type, got %d')
                                        % self.freight_type)
        return self.freight_types[self.freight_type]

    @property
    def branch_name(self):
        return self.branch.get_description()

    @property
    def supplier_name(self):
        return self.supplier.get_description()

    @property
    def transporter_name(self):
        if not self.transporter:
            return u""
        return self.transporter.get_description()

    @property
    def responsible_name(self):
        return self.responsible.get_description()

    @property
    def purchase_subtotal(self):
        """Get the subtotal of the purchase.
        The sum of all the items cost * items quantity
        """
        return currency(self.get_items().sum(
            PurchaseItem.cost * PurchaseItem.quantity) or 0)

    @property
    def purchase_total(self):
        subtotal = self.purchase_subtotal
        total = subtotal - self.discount_value + self.surcharge_value
        if total < 0:
            raise ValueError(_(u'Purchase total can not be lesser than zero'))
        # XXX: Since the purchase_total value must have two digits
        # (at the moment) we need to format the value to a 2-digit number and
        # then convert it to currency data type, because the subtotal value
        # may return a 3-or-more-digit value, depending on COST_PRECISION_DIGITS
        # parameters.
        return currency(get_formatted_price(total))

    @property
    def received_total(self):
        """Like {purchase_subtotal} but only takes into account the
        received items
        """
        return currency(self.get_items().sum(
            PurchaseItem.cost *
            PurchaseItem.quantity_received) or 0)

    def get_remaining_total(self):
        """The total value to be paid for the items not received yet
        """
        return self.purchase_total - self.received_total

    def get_pending_items(self, with_children=True):
        """
        Returns a sequence of all items which we haven't received yet.
        """
        return self.get_items(with_children=with_children).find(
            PurchaseItem.quantity_received < PurchaseItem.quantity)

    def get_partially_received_items(self):
        """
        Returns a sequence of all items which are partially received.
        """
        return self.get_items().find(
            PurchaseItem.quantity_received > 0)

    def get_open_date_as_string(self):
        return self.open_date and self.open_date.strftime("%x") or u""

    def get_quote_deadline_as_string(self):
        return self.quote_deadline and self.quote_deadline.strftime("%x") or u""

    def get_receiving_orders(self):
        """Returns all ReceivingOrder related to this purchase order
        """
        from stoqlib.domain.receiving import PurchaseReceivingMap, ReceivingOrder
        tables = [PurchaseReceivingMap, ReceivingOrder]
        query = And(PurchaseReceivingMap.purchase_id == self.id,
                    PurchaseReceivingMap.receiving_id == ReceivingOrder.id)
        return self.store.using(*tables).find(ReceivingOrder, query)

    def get_data_for_labels(self):
        """ This function returns some necessary data to print the purchase's
        items labels
        """
        for purchase_item in self.get_items():
            sellable = purchase_item.sellable
            label_data = Settable(barcode=sellable.barcode, code=sellable.code,
                                  description=sellable.description,
                                  price=sellable.price,
                                  quantity=purchase_item.quantity)
            yield label_data

    def has_batch_item(self):
        """Fetch the storables from this purchase order and returns ``True`` if
        any of them is a batch storable.

        :returns: ``True`` if this purchase order has batch items, ``False`` if
        it doesn't.
        """
        return not self.store.find(Storable,
                                   And(self.id == PurchaseOrder.id,
                                       PurchaseOrder.id == PurchaseItem.order_id,
                                       PurchaseItem.sellable_id == Sellable.id,
                                       Sellable.id == Storable.id,
                                       Eq(Storable.is_batch, True))).is_empty()

    #
    # Classmethods
    #

    @classmethod
    def translate_status(cls, status):
        if not status in cls.statuses:
            raise DatabaseInconsistency(_(u'Got an unexpected status value: '
                                          u'%s') % status)
        return cls.statuses[status]


@implementer(IDescribable)
class Quotation(Domain):
    __storm_table__ = 'quotation'

    #: A numeric identifier for this object. This value should be used instead of
    #: :obj:`Domain.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IdentifierCol()

    group_id = IdCol()
    group = Reference(group_id, 'QuoteGroup.id')
    purchase_id = IdCol()
    purchase = Reference(purchase_id, 'PurchaseOrder.id')
    branch_id = IdCol()
    branch = Reference(branch_id, 'Branch.id')

    def get_description(self):
        supplier = self.purchase.supplier.person.name
        return u"Group %s - %s" % (self.group.identifier, supplier)

    #
    # Public API
    #

    def close(self):
        """Closes the quotation"""
        # we don't have a specific status for closed quotes, so we just
        # cancel it
        if not self.is_closed():
            self.purchase.cancel()

    def is_closed(self):
        """Returns if the quotation is closed or not.

        :returns: True if the quotation is closed, False otherwise.
        """
        return self.purchase.status == PurchaseOrder.ORDER_CANCELLED


@implementer(IContainer)
@implementer(IDescribable)
class QuoteGroup(Domain):

    __storm_table__ = 'quote_group'

    #: A numeric identifier for this object. This value should be used instead of
    #: :obj:`Domain.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IdentifierCol()

    branch_id = IdCol()
    branch = Reference(branch_id, 'Branch.id')

    #
    # IContainer
    #

    def get_items(self):
        return self.store.find(Quotation, group=self)

    def remove_item(self, item):
        if item.group is not self:
            raise ValueError(_(u'You can not remove an item which does not '
                               u'belong to this group.'))

        order = item.purchase
        # FIXME: Bug 5581 Removing objects with synced databases is dangerous.
        # Investigate this usage
        self.store.remove(item)
        for order_item in order.get_items():
            order.remove_item(order_item)
        self.store.remove(order)

    def add_item(self, item):
        store = self.store
        return Quotation(purchase=item, group=self, branch=self.branch,
                         store=store)

    #
    # IDescribable
    #

    def get_description(self):
        return _(u"quote number %s") % self.identifier

    #
    # Public API
    #

    def cancel(self):
        """Cancel a quote group."""
        store = self.store
        for quote in self.get_items():
            quote.close()
            # FIXME: Bug 5581 Removing objects with synced databases is
            # dangerous. Investigate this usage
            store.remove(quote)


class PurchaseItemView(Viewable):
    """This is a view which you can use to fetch purchase items within
    a specific purchase. It's used by the PurchaseDetails dialog
    to display all the purchase items within a purchase

    :param id: id of the purchase item
    :param purchase_id: id of the purchase order the item belongs to
    :param sellable: sellable of the item
    :param cost: cost of the item
    :param quantity: quantity ordered
    :param quantity_received: quantity received
    :param total: total value of the items purchased
    :param total_received: total value of the items received
    :param description: description of the sellable
    :param unit: unit as a string or None if the product has no unit
    """

    purchase_item = PurchaseItem

    id = PurchaseItem.id
    cost = PurchaseItem.cost
    quantity = PurchaseItem.quantity
    quantity_received = PurchaseItem.quantity_received
    quantity_sold = PurchaseItem.quantity_sold
    quantity_returned = PurchaseItem.quantity_returned
    total = PurchaseItem.cost * PurchaseItem.quantity
    total_received = PurchaseItem.cost * PurchaseItem.quantity_received
    total_sold = PurchaseItem.cost * PurchaseItem.quantity_sold

    purchase_id = PurchaseOrder.id
    sellable = Sellable.id
    code = Sellable.code
    description = Sellable.description
    unit = SellableUnit.description

    tables = [
        PurchaseItem,
        Join(PurchaseOrder, PurchaseOrder.id == PurchaseItem.order_id),
        Join(Sellable, Sellable.id == PurchaseItem.sellable_id),
        LeftJoin(SellableUnit, SellableUnit.id == Sellable.unit_id),
    ]

    @property
    def quantity_as_string(self):
        return u"%s %s" % (format_quantity(self.quantity),
                           self.unit or u"")

    @property
    def quantity_received_as_string(self):
        return u"%s %s" % (format_quantity(self.quantity_received),
                           self.unit or u"")

    @classmethod
    def find_by_purchase(cls, store, purchase):
        return store.find(cls, purchase_id=purchase.id)


#
# Views
#

# Summary for Purchased items
# Its faster to do the SUM() bellow in a subselect, since aggregate
# functions require group by for every other column, and grouping all the
# columns in PurchaseOrderView is extremelly slow, as it requires sorting all
# those columns
_ItemSummary = Select(columns=[PurchaseItem.order_id,
                               Alias(Sum(PurchaseItem.quantity), 'ordered_quantity'),
                               Alias(Sum(PurchaseItem.quantity_received), 'received_quantity'),
                               Alias(Sum(PurchaseItem.quantity *
                                     PurchaseItem.cost), 'subtotal')],
                      tables=[PurchaseItem],
                      group_by=[PurchaseItem.order_id])
PurchaseItemSummary = Alias(_ItemSummary, '_purchase_item')


class PurchaseOrderView(Viewable):
    """General information about purchase orders

    :cvar id: the id of purchase_order table
    :cvar status: the purchase order status
    :cvar open_date: the date when the order was started
    :cvar quote_deadline: the date when the quotation expires
    :cvar expected_receival_date: expected date to receive products
    :cvar expected_pay_date: expected date to pay the products
    :cvar receival_date: the date when the products were received
    :cvar confirm_date: the date when the order was confirmed
    :cvar salesperson_name: the name of supplier's salesperson
    :cvar expected_freight: the expected freight value
    :cvar surcharge_value: the surcharge value for the order total
    :cvar discount_value: the discount_value for the order total
    :cvar supplier_name: the supplier name
    :cvar transporter_name: the transporter name
    :cvar branch_name: the branch company name
    :cvar ordered_quantity: the total quantity ordered
    :cvar received_quantity: the total quantity received
    :cvar subtotal: the order subtotal (sum of product values)
    :cvar total: subtotal - discount_value + surcharge_value
    """

    Person_Supplier = ClassAlias(Person, 'person_supplier')
    Person_Transporter = ClassAlias(Person, 'person_transporter')
    Person_Branch = ClassAlias(Person, 'person_branch')
    Person_Responsible = ClassAlias(Person, 'person_responsible')

    purchase = PurchaseOrder
    branch = Branch

    id = PurchaseOrder.id
    identifier = PurchaseOrder.identifier
    identifier_str = Cast(PurchaseOrder.identifier, 'text')
    status = PurchaseOrder.status
    open_date = PurchaseOrder.open_date
    quote_deadline = PurchaseOrder.quote_deadline
    expected_receival_date = PurchaseOrder.expected_receival_date
    expected_pay_date = PurchaseOrder.expected_pay_date
    receival_date = PurchaseOrder.receival_date
    confirm_date = PurchaseOrder.confirm_date
    salesperson_name = NullIf(PurchaseOrder.salesperson_name, u'')
    expected_freight = PurchaseOrder.expected_freight
    surcharge_value = PurchaseOrder.surcharge_value
    discount_value = PurchaseOrder.discount_value

    branch_id = Branch.id
    supplier_id = Supplier.id
    supplier_name = Person_Supplier.name
    transporter_name = Coalesce(Person_Transporter.name, u'')
    branch_name = Coalesce(NullIf(Company.fancy_name, u''), Person_Branch.name)
    responsible_name = Person_Responsible.name

    ordered_quantity = Field('_purchase_item', 'ordered_quantity')
    received_quantity = Field('_purchase_item', 'received_quantity')
    subtotal = Field('_purchase_item', 'subtotal')
    total = Field('_purchase_item', 'subtotal') - \
        PurchaseOrder.discount_value + PurchaseOrder.surcharge_value

    tables = [
        PurchaseOrder,
        Join(PurchaseItemSummary,
             Field('_purchase_item', 'order_id') == PurchaseOrder.id),

        LeftJoin(Supplier, PurchaseOrder.supplier_id == Supplier.id),
        LeftJoin(Transporter, PurchaseOrder.transporter_id == Transporter.id),
        LeftJoin(Branch, PurchaseOrder.branch_id == Branch.id),
        LeftJoin(LoginUser, PurchaseOrder.responsible_id == LoginUser.id),

        LeftJoin(Person_Supplier, Supplier.person_id == Person_Supplier.id),
        LeftJoin(Person_Transporter, Transporter.person_id == Person_Transporter.id),
        LeftJoin(Person_Branch, Branch.person_id == Person_Branch.id),
        LeftJoin(Company, Company.person_id == Person_Branch.id),
        LeftJoin(Person_Responsible, LoginUser.person_id == Person_Responsible.id),
    ]

    @classmethod
    def post_search_callback(cls, sresults):
        select = sresults.get_select_expr(Count(1), Sum(cls.total))
        return ('count', 'sum'), select

    #
    # Public API
    #

    def get_open_date_as_string(self):
        return self.open_date.strftime("%x")

    @property
    def status_str(self):
        return PurchaseOrder.translate_status(self.status)

    @classmethod
    def find_confirmed(cls, store, due_date=None):
        query = cls.status == PurchaseOrder.ORDER_CONFIRMED

        if due_date:
            if isinstance(due_date, tuple):
                date_query = And(Date(cls.expected_receival_date) >= due_date[0],
                                 Date(cls.expected_receival_date) <= due_date[1])
            else:
                date_query = Date(cls.expected_receival_date) == due_date

            query = And(query, date_query)

        return store.find(cls, query)
