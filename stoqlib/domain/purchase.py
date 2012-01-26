# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2009 Async Open Source <http://www.async.com.br>
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

from decimal import Decimal
import datetime

from kiwi.argcheck import argcheck
from kiwi.datatypes import currency
from zope.interface import implements

from stoqlib.database.orm import ForeignKey, IntCol, DateTimeCol, UnicodeCol
from stoqlib.database.orm import AND, INNERJOINOn, LEFTJOINOn, const
from stoqlib.database.orm import Viewable, Alias
from stoqlib.database.orm import PriceCol, BoolCol, QuantityCol
from stoqlib.database.runtime import get_current_user
from stoqlib.domain.base import Domain
from stoqlib.domain.event import Event
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.interfaces import (IPaymentTransaction, IContainer,
                                       IDescribable)
from stoqlib.domain.person import (Person, PersonAdaptToBranch,
                                   PersonAdaptToSupplier,
                                   PersonAdaptToTransporter,
                                   PersonAdaptToUser)
from stoqlib.domain.sellable import Sellable, SellableUnit
from stoqlib.exceptions import DatabaseInconsistency, StoqlibError
from stoqlib.lib.defaults import quantize
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.formatters import format_quantity, get_formatted_price


_ = stoqlib_gettext


class PurchaseItem(Domain):
    """This class stores information of the purchased items.

    B{Importante attributes}
        - I{base_cost}: the cost which helps the purchaser to define the
                        main cost of a certain product.
    """
    quantity = QuantityCol(default=1)
    quantity_received = QuantityCol(default=0)
    quantity_sold = QuantityCol(default=0)
    quantity_returned = QuantityCol(default=0)
    base_cost = PriceCol()
    cost = PriceCol()
    expected_receival_date = DateTimeCol(default=None)
    sellable = ForeignKey('Sellable')
    order = ForeignKey('PurchaseOrder')

    def _create(self, id, **kw):
        if not 'sellable' in kw:
            raise TypeError('You must provide a sellable argument')
        if not 'order' in kw:
            raise TypeError('You must provide a order argument')

        # FIXME: Avoding shadowing sellable.cost
        kw['base_cost'] = kw['sellable'].cost

        if not 'cost' in kw:
            kw['cost'] = kw['sellable'].cost

        Domain._create(self, id, **kw)

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
        if not self.has_been_received:
            return Decimal(0)
        return self.quantity - self.quantity_received

    def get_quantity_as_string(self):
        unit = self.sellable.unit
        return "%s %s" % (format_quantity(self.quantity),
                          unit and unit.description or u"")

    def get_quantity_received_as_string(self):
        unit = self.sellable.unit
        return "%s %s" % (format_quantity(self.quantity_received),
                          unit and unit.description or u"")

    @classmethod
    def get_ordered_quantity(cls, conn, sellable):
        """Returns the quantity already ordered of a given sellable.
        @param conn: a database connection
        @param sellable: the sellable we want to know the quantity ordered.
        @returns: the quantity already ordered of a given sellable or zero if
        no quantity have been ordered.
        """
        query = AND(PurchaseItem.q.sellableID == sellable.id,
                    PurchaseOrder.q.id == PurchaseItem.q.orderID,
                    PurchaseOrder.q.status == PurchaseOrder.ORDER_CONFIRMED)
        ordered_items = PurchaseItem.select(query, connection=conn)
        return ordered_items.sum('quantity') or Decimal(0)


class PurchaseOrder(Domain):
    """Purchase and order definition."""

    implements(IContainer)

    (ORDER_CANCELLED,
     ORDER_QUOTING,
     ORDER_PENDING,
     ORDER_CONFIRMED,
     ORDER_CLOSED,
     ORDER_CONSIGNED) = range(6)

    statuses = {ORDER_CANCELLED: _(u'Cancelled'),
                ORDER_QUOTING: _(u'Quoting'),
                ORDER_PENDING: _(u'Pending'),
                ORDER_CONFIRMED: _(u'Confirmed'),
                ORDER_CLOSED: _(u'Closed'),
                ORDER_CONSIGNED: _(u'Consigned')}

    (FREIGHT_FOB,
     FREIGHT_CIF) = range(2)

    freight_types = {FREIGHT_FOB: _(u'FOB'),
                     FREIGHT_CIF: _(u'CIF')}

    status = IntCol(default=ORDER_QUOTING)
    open_date = DateTimeCol(default=datetime.datetime.now)
    quote_deadline = DateTimeCol(default=None)
    expected_receival_date = DateTimeCol(default=datetime.datetime.now)
    expected_pay_date = DateTimeCol(default=datetime.datetime.now)
    receival_date = DateTimeCol(default=None)
    confirm_date = DateTimeCol(default=None)
    notes = UnicodeCol(default='')
    salesperson_name = UnicodeCol(default='')
    freight_type = IntCol(default=FREIGHT_FOB)
    expected_freight = PriceCol(default=0)
    surcharge_value = PriceCol(default=0)
    discount_value = PriceCol(default=0)
    consigned = BoolCol(default=False)
    supplier = ForeignKey('PersonAdaptToSupplier')
    branch = ForeignKey('PersonAdaptToBranch')
    transporter = ForeignKey('PersonAdaptToTransporter', default=None)
    responsible = ForeignKey('PersonAdaptToUser')
    group = ForeignKey('PaymentGroup')

    #
    # IContainer Implementation
    #

    def get_items(self):
        return PurchaseItem.selectBy(order=self,
                                     connection=self.get_connection())

    @argcheck(PurchaseItem)
    def remove_item(self, item):
        conn = self.get_connection()
        if item.order is not self:
            raise ValueError(_('Argument item must have an order attribute '
                               'associated with the current purchase instance'))
        PurchaseItem.delete(item.id, connection=conn)

    def add_item(self, sellable, quantity=Decimal(1)):
        conn = self.get_connection()
        return PurchaseItem(connection=conn, order=self,
                            sellable=sellable, quantity=quantity)

    #
    # Properties
    #

    def _set_discount_by_percentage(self, value):
        """Sets a discount by percentage.
        Note that percentage must be added as an absolute value not as a
        factor like 1.05 = 5 % of surcharge
        The correct form is 'percentage = 3' for a discount of 3 %"""
        self.discount_value = self._get_percentage_value(value)

    def _get_discount_by_percentage(self):
        discount_value = self.discount_value
        if not discount_value:
            return currency(0)
        subtotal = self.get_purchase_subtotal()
        assert subtotal > 0, ('the subtotal should not be zero '
                              'at this point')
        total = subtotal - discount_value
        percentage = (1 - total / subtotal) * 100
        return quantize(percentage)

    discount_percentage = property(_get_discount_by_percentage,
                                   _set_discount_by_percentage)

    def _set_surcharge_by_percentage(self, value):
        """Sets a surcharge by percentage.
        Note that surcharge must be added as an absolute value not as a
        factor like 0.97 = 3 % of discount.
        The correct form is 'percentage = 3' for a surcharge of 3 %"""
        self.surcharge_value = self._get_percentage_value(value)

    def _get_surcharge_by_percentage(self):
        surcharge_value = self.surcharge_value
        if not surcharge_value:
            return currency(0)
        subtotal = self.get_purchase_subtotal()
        assert subtotal > 0, ('the subtotal should not be zero '
                              'at this point')
        total = subtotal + surcharge_value
        percentage = ((total / subtotal) - 1) * 100
        return quantize(percentage)

    surcharge_percentage = property(_get_surcharge_by_percentage,
                                    _set_surcharge_by_percentage)

    @property
    def order_number(self):
        return self.id

    @property
    def payments(self):
        return Payment.selectBy(group=self.group,
                                connection=self.get_connection())

    #
    # Private
    #

    def _get_percentage_value(self, percentage):
        if not percentage:
            return currency(0)
        subtotal = self.get_purchase_subtotal()
        percentage = Decimal(percentage)
        return subtotal * (percentage / 100)

    #
    # Public API
    #

    def is_paid(self):
        for payment in self.group.get_items():
            if not payment.is_paid():
                return False
        return True

    def can_cancel(self):
        """Find out if it's possible to cancel the order
        @returns: True if it's possible to cancel the order, otherwise False
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
        @returns: True if it's possible to close the order, otherwise False
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

        @param confirm_data: optional, datetime
        """
        if confirm_date is None:
            confirm_date = const.NOW()

        if self.status not in [PurchaseOrder.ORDER_PENDING,
                               PurchaseOrder.ORDER_CONSIGNED]:
            raise ValueError(
                _('Invalid order status, it should be '
                  'ORDER_PENDING or ORDER_CONSIGNED, got %s') % (
                self.get_status_str(), ))

        transaction = IPaymentTransaction(self)
        transaction.confirm()

        if self.supplier:
            self.group.recipient = self.supplier.person

        self.responsible = get_current_user(self.get_connection())
        self.status = PurchaseOrder.ORDER_CONFIRMED
        self.confirm_date = confirm_date

        Event.log(Event.TYPE_ORDER,
                _("Order %d, total value %2.2f, supplier '%s' "
                  "is now confirmed") % (
                    self.order_number,
                    self.get_purchase_total(),
                    self.supplier.person.name))

    def set_consigned(self):
        if self.status != PurchaseOrder.ORDER_PENDING:
            raise ValueError(
                _('Invalid order status, it should be '
                  'ORDER_PENDING, got %s') % (self.get_status_str(), ))

        self.responsible = get_current_user(self.get_connection())
        self.status = PurchaseOrder.ORDER_CONSIGNED

    def close(self):
        """Closes the purchase order
        """
        if self.status != PurchaseOrder.ORDER_CONFIRMED:
            raise ValueError(_('Invalid status, it should be confirmed '
                               'got %s instead') % self.get_status_str())
        self.status = self.ORDER_CLOSED

        Event.log(Event.TYPE_ORDER,
                _("Order %d, total value %2.2f, supplier '%s' "
                  "is now closed") % (
                    self.order_number,
                    self.get_purchase_total(),
                    self.supplier.person.name))

    def cancel(self):
        """Cancels the purchase order
        """
        assert self.can_cancel()

        # we have to cancel the payments too
        transaction = IPaymentTransaction(self)
        transaction.cancel()

        self.status = self.ORDER_CANCELLED

    def receive_item(self, item, quantity_to_receive):
        if not item in self.get_pending_items():
            raise StoqlibError(_('This item is not pending, hence '
                                 'cannot be received'))
        quantity = item.quantity - item.quantity_received
        if quantity < quantity_to_receive:
            raise StoqlibError(_('The quantity that you want to receive '
                                 'is greater than the total quantity of '
                                 'this item %r') % item)
        self.increase_quantity_received(item, quantity_to_receive)

    def increase_quantity_received(self, purchase_item, quantity_received):
        sellable = purchase_item.sellable
        items = [item for item in self.get_items()
                    if item.sellable.id == sellable.id]
        qty = len(items)
        if not qty:
            raise ValueError(_('There is no purchase item for '
                               'sellable %r') % sellable)

        purchase_item.quantity_received += quantity_received

    def get_status_str(self):
        return PurchaseOrder.translate_status(self.status)

    def get_freight_type_name(self):
        if not self.freight_type in self.freight_types.keys():
            raise DatabaseInconsistency(_('Invalid freight_type, got %d')
                                          % self.freight_type)
        return self.freight_types[self.freight_type]

    def get_branch_name(self):
        return self.branch.get_description()

    def get_supplier_name(self):
        return self.supplier.get_description()

    def get_transporter_name(self):
        if not self.transporter:
            return u""
        return self.transporter.get_description()

    def get_responsible_name(self):
        return self.responsible.get_description()

    def get_order_number_str(self):
        return u'%05d' % self.id

    def get_purchase_subtotal(self):
        """Get the subtotal of the purchase.
        The sum of all the items cost * items quantity
        """
        return currency(self.get_items().sum(
            PurchaseItem.q.cost * PurchaseItem.q.quantity) or 0)

    def get_purchase_total(self):
        subtotal = self.get_purchase_subtotal()
        total = subtotal - self.discount_value + self.surcharge_value
        if total < 0:
            raise ValueError(_('Purchase total can not be lesser than zero'))
        #XXX: Since the purchase_total value must have two digits
        # (at the moment) we need to format the value to a 2-digit number and
        # then convert it to currency data type, because the subtotal value
        # may return a 3-or-more-digit value, depending on COST_PRECISION_DIGITS
        # parameters.
        return currency(get_formatted_price(total))

    def get_received_total(self):
        """Like {get_purchase_subtotal} but only takes into account the
        received items
        """
        return currency(self.get_items().sum(
            PurchaseItem.q.cost *
            PurchaseItem.q.quantity_received) or 0)

    def get_remaining_total(self):
        """The total value to be paid for the items not received yet
        """
        return self.get_purchase_total() - self.get_received_total()

    def get_pending_items(self):
        """
        Returns a sequence of all items which we haven't received yet.
        """
        return self.get_items().filter(
            PurchaseItem.q.quantity_received < PurchaseItem.q.quantity)

    def get_partially_received_items(self):
        """
        Returns a sequence of all items which are partially received.
        """
        return self.get_items().filter(
            PurchaseItem.q.quantity_received > 0)

    def get_open_date_as_string(self):
        return self.open_date and self.open_date.strftime("%x") or ""

    def get_quote_deadline_as_string(self):
        return self.quote_deadline and self.quote_deadline.strftime("%x") or ""

    def get_receiving_orders(self):
        """Returns all ReceivingOrder related to this purchase order
        """
        from stoqlib.domain.receiving import ReceivingOrder
        return ReceivingOrder.selectBy(purchase=self,
                                       connection=self.get_connection())

    #
    # Classmethods
    #

    @classmethod
    def translate_status(cls, status):
        if not status in cls.statuses:
            raise DatabaseInconsistency(_('Got an unexpected status value: '
                                          '%s') % status)
        return cls.statuses[status]


class Quotation(Domain):
    group = ForeignKey('QuoteGroup')
    purchase = ForeignKey('PurchaseOrder')

    implements(IDescribable)

    def get_description(self):
        supplier = self.purchase.supplier.person.name
        return "Group %04d - %s" % (self.group.id, supplier)

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

        @returns: True if the quotation is closed, False otherwise.
        """
        return self.purchase.status == PurchaseOrder.ORDER_CANCELLED


class QuoteGroup(Domain):

    implements(IContainer, IDescribable)

    #
    # IContainer
    #

    def get_items(self):
        return Quotation.selectBy(group=self, connection=self.get_connection())

    @argcheck(Quotation)
    def remove_item(self, item):
        conn = self.get_connection()
        if item.group is not self:
            raise ValueError(_('You can not remove an item which does not '
                               'belong to this group.'))

        order = item.purchase
        Quotation.delete(item.id, connection=conn)
        for order_item in order.get_items():
            order.remove_item(order_item)
        PurchaseOrder.delete(order.id, connection=conn)

    @argcheck(PurchaseOrder)
    def add_item(self, item):
        conn = self.get_connection()
        return Quotation(purchase=item, group=self, connection=conn)

    #
    # IDescribable
    #

    def get_description(self):
        return _(u"quote number %04d" % self.id)

    #
    # Public API
    #

    def cancel(self):
        """Cancel a quote group."""
        conn = self.get_connection()
        for quote in self.get_items():
            quote.close()
            Quotation.delete(quote.id, connection=conn)


class PurchaseOrderAdaptToPaymentTransaction(object):
    implements(IPaymentTransaction)

    def __init__(self, purchase):
        self.purchase = purchase

    #
    # IPaymentTransaction implementation
    #

    def confirm(self):
        # In consigned purchases there is no payments at this point.
        if self.purchase.status == PurchaseOrder.ORDER_CONSIGNED:
            return

        for payment in self.purchase.payments:
            payment.set_pending()

    def pay(self):
        for payment in self.purchase.payments:
            payment.pay()

    def cancel(self):
        assert self.purchase.group.can_cancel()

        self._payback_paid_payments()
        self.purchase.group.cancel()

    def return_(self, renegotiation):
        pass

    #
    # Private API
    #

    def _payback_paid_payments(self):
        paid_value = self.purchase.group.get_total_paid()

        # If we didn't pay anything yet, there is no need to create a payback.
        if not paid_value:
            return

        money = PaymentMethod.get_by_name(self.purchase.get_connection(), 'money')
        in_payment = money.create_inpayment(
            self.purchase.group, paid_value,
            description=_('%s Money Returned for Purchase %d') % (
            '1/1', self.purchase.id))
        payment = in_payment.get_adapted()
        payment.set_pending()
        payment.pay()


PurchaseOrder.registerFacet(PurchaseOrderAdaptToPaymentTransaction, IPaymentTransaction)


class PurchaseItemView(Viewable):
    """This is a view which you can use to fetch purchase items within
    a specific purchase. It's used by the PurchaseDetails dialog
    to display all the purchase items within a purchase

    @param id: id of the purchase item
    @param purchase_id: id of the purchase order the item belongs to
    @param sellable: sellable of the item
    @param cost: cost of the item
    @param quantity: quantity ordered
    @param quantity_received: quantity received
    @param total: total value of the items purchased
    @param total_received: total value of the items received
    @param description: description of the sellable
    @param unit: unit as a string or None if the product has no unit
    """
    columns = dict(
        id=PurchaseItem.q.id,
        purchase_id=PurchaseOrder.q.id,
        sellable=Sellable.q.id,
        code=Sellable.q.code,
        cost=PurchaseItem.q.cost,
        quantity=PurchaseItem.q.quantity,
        quantity_received=PurchaseItem.q.quantity_received,
        quantity_sold=PurchaseItem.q.quantity_sold,
        quantity_returned=PurchaseItem.q.quantity_returned,
        total=PurchaseItem.q.cost * PurchaseItem.q.quantity,
        total_received=PurchaseItem.q.cost * PurchaseItem.q.quantity_received,
        total_sold=PurchaseItem.q.cost * PurchaseItem.q.quantity_sold,
        description=Sellable.q.description,
        unit=SellableUnit.q.description,
        )

    clause = AND(
        PurchaseOrder.q.id == PurchaseItem.q.orderID,
        )

    joins = [
        INNERJOINOn(None, Sellable,
                    Sellable.q.id == PurchaseItem.q.sellableID),
        LEFTJOINOn(None, SellableUnit,
                   SellableUnit.q.id == Sellable.q.unitID),
        ]

    def get_quantity_as_string(self):
        return "%s %s" % (format_quantity(self.quantity),
                          self.unit or u"")

    def get_quantity_received_as_string(self):
        return "%s %s" % (format_quantity(self.quantity_received),
                          self.unit or u"")

    @classmethod
    def select_by_purchase(cls, purchase, connection):
        return PurchaseItemView.select(PurchaseOrder.q.id == purchase.id,
                                       connection=connection)

    @property
    def purchase_item(self):
        return PurchaseItem.get(self.id)


#
# Views
#


class PurchaseOrderView(Viewable):
    """General information about purchase orders

    @cvar id: the id of purchase_order table
    @cvar status: the purchase order status
    @cvar open_date: the date when the order was started
    @cvar quote_deadline: the date when the quotation expires
    @cvar expected_receival_date: expected date to receive products
    @cvar expected_pay_date: expected date to pay the products
    @cvar receival_date: the date when the products were received
    @cvar confirm_date: the date when the order was confirmed
    @cvar salesperson_name: the name of supplier's salesperson
    @cvar expected_freight: the expected freight value
    @cvar surcharge_value: the surcharge value for the order total
    @cvar discount_value: the discount_value for the order total
    @cvar supplier_name: the supplier name
    @cvar transporter_name: the transporter name
    @cvar branch_name: the branch company name
    @cvar ordered_quantity: the total quantity ordered
    @cvar received_quantity: the total quantity received
    @cvar subtotal: the order subtotal (sum of product values)
    @cvar total: subtotal - discount_value + surcharge_value
    """

    Person_Supplier = Alias(Person, 'person_supplier')
    Person_Transporter = Alias(Person, 'person_transporter')
    Person_Branch = Alias(Person, 'person_branch')
    Person_Responsible = Alias(Person, 'person_responsible')

    columns = dict(
        id=PurchaseOrder.q.id,
        status=PurchaseOrder.q.status,
        open_date=PurchaseOrder.q.open_date,
        quote_deadline=PurchaseOrder.q.quote_deadline,
        expected_receival_date=PurchaseOrder.q.expected_receival_date,
        expected_pay_date=PurchaseOrder.q.expected_pay_date,
        receival_date=PurchaseOrder.q.receival_date,
        confirm_date=PurchaseOrder.q.confirm_date,
        salesperson_name=PurchaseOrder.q.salesperson_name,
        expected_freight=PurchaseOrder.q.expected_freight,
        surcharge_value=PurchaseOrder.q.surcharge_value,
        discount_value=PurchaseOrder.q.discount_value,

        supplier_name=Person_Supplier.q.name,
        transporter_name=Person_Transporter.q.name,
        branch_name=Person_Branch.q.name,
        responsible_name=Person_Responsible.q.name,

        ordered_quantity=const.SUM(PurchaseItem.q.quantity),
        received_quantity=const.SUM(PurchaseItem.q.quantity_received),
        subtotal=const.SUM(PurchaseItem.q.cost * PurchaseItem.q.quantity),
        total=const.SUM(PurchaseItem.q.cost * PurchaseItem.q.quantity) - \
            PurchaseOrder.q.discount_value + PurchaseOrder.q.surcharge_value
    )

    joins = [
        INNERJOINOn(None, PurchaseItem,
                    PurchaseOrder.q.id == PurchaseItem.q.orderID),

        LEFTJOINOn(None, PersonAdaptToSupplier,
                   PurchaseOrder.q.supplierID == PersonAdaptToSupplier.q.id),
        LEFTJOINOn(None, PersonAdaptToTransporter,
                   PurchaseOrder.q.transporterID == PersonAdaptToTransporter.q.id),
        LEFTJOINOn(None, PersonAdaptToBranch,
                   PurchaseOrder.q.branchID == PersonAdaptToBranch.q.id),
        LEFTJOINOn(None, PersonAdaptToUser,
                   PurchaseOrder.q.responsibleID == PersonAdaptToUser.q.id),

        LEFTJOINOn(None, Person_Supplier,
                   PersonAdaptToSupplier.q.originalID == Person_Supplier.q.id),
        LEFTJOINOn(None, Person_Transporter,
                   PersonAdaptToTransporter.q.originalID == Person_Transporter.q.id),
        LEFTJOINOn(None, Person_Branch,
                   PersonAdaptToBranch.q.originalID == Person_Branch.q.id),
       LEFTJOINOn(None, Person_Responsible,
                   PersonAdaptToUser.q.originalID == Person_Responsible.q.id),
    ]

    #
    # Properties
    #

    @property
    def purchase(self):
        return PurchaseOrder.get(self.id)

    #
    # Public API
    #

    def get_total(self):
        return currency(self.total)

    def get_subtotal(self):
        return currency(self.subtotal)

    def get_branch_name(self):
        return unicode(self.branch_name or "")

    def get_supplier_name(self):
        return unicode(self.supplier_name or "")

    def get_transporter_name(self):
        return unicode(self.transporter_name or "")

    def get_open_date_as_string(self):
        return self.open_date.strftime("%x")

    def get_status_str(self):
        return PurchaseOrder.translate_status(self.status)

    @classmethod
    def select_confirmed(cls, due_date=None, connection=None):
        query = cls.q.status == PurchaseOrder.ORDER_CONFIRMED

        if due_date:
            if isinstance(due_date, tuple):
                date_query = AND(const.DATE(cls.q.expected_receival_date) >= due_date[0],
                                 const.DATE(cls.q.expected_receival_date) <= due_date[1])
            else:
                date_query = const.DATE(cls.q.expected_receival_date) == due_date

            query = AND(query, date_query)

        return cls.select(query, connection=connection)
