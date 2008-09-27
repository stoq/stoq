# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2008 Async Open Source <http://www.async.com.br>
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
##              Henrique Romano             <henrique@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
""" Sale object and related objects implementation """

import datetime
from decimal import Decimal

from kiwi.argcheck import argcheck
from kiwi.datatypes import currency
from stoqdrivers.enum import TaxType
from zope.interface import implements

from stoqlib.database.orm import ORMObject
from stoqlib.database.orm import ForeignKey, UnicodeCol, DateTimeCol, IntCol
from stoqlib.database.orm import AND, const
from stoqlib.database.columns import PriceCol, DecimalCol
from stoqlib.database.runtime import (get_current_user,
                                      get_current_branch)
from stoqlib.domain.base import (Domain, ValidatableDomain, BaseSQLView,
                                 ModelAdapter)
from stoqlib.domain.events import SaleConfirmEvent
from stoqlib.domain.fiscal import FiscalBookEntry
from stoqlib.domain.interfaces import (IContainer, IOutPayment,
                                       IPaymentTransaction,
                                       IDelivery, IStorable,
                                       IInPayment)
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.product import Product, ProductHistory
from stoqlib.domain.renegotiation import RenegotiationData
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.service import Service
from stoqlib.domain.till import Till
from stoqlib.exceptions import (SellError, DatabaseInconsistency,
                                StoqlibError)
from stoqlib.lib.defaults import quantize
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext

#
# Base Domain Classes
#

class SaleItem(Domain):
    """An item in a sale.

    @param sellable: the kind of item
    @param sale: the same
    @param quantity: the quantity of the of sold item in this sale
    @param price: the price of each individual item
    @param base_price:
    @param notes:
    @param estimated_fix_date:
    @param completion_date:
    """
    quantity = DecimalCol()
    base_price = PriceCol()
    price = PriceCol()
    sale = ForeignKey('Sale')
    sellable = ForeignKey('Sellable')

    # This is currently only used by services
    notes = UnicodeCol(default=None)
    estimated_fix_date = DateTimeCol(default=datetime.datetime.now)
    completion_date = DateTimeCol(default=None)

    def _create(self, id, **kw):
        if not 'kw' in kw:
            if not 'sellable' in kw:
                raise TypeError('You must provide a sellable argument')
            base_price = kw['sellable'].price
            kw['base_price'] = base_price
        Domain._create(self, id, **kw)

    def sell(self, branch):
        conn = self.get_connection()
        sparam = sysparam(conn)
        if not (branch and
                branch.id == get_current_branch(conn).id):
            raise SellError("Stock still doesn't support sales for "
                            "branch companies different than the "
                            "current one")

        if not self.sellable.can_be_sold():
            raise SellError('%r is already sold' % self.sellable)

        storable = IStorable(self.sellable.product, None)
        if storable:
            storable.decrease_stock(self.quantity, branch)

    def cancel(self, branch):
        storable = IStorable(self.sellable.product, None)
        if storable:
            storable.increase_stock(self.quantity, branch)

    #
    # Accessors
    #

    def get_total(self):
        return currency(self.price * self.quantity)

    def get_quantity_unit_string(self):
        return "%s %s" % (self.quantity, self.sellable.get_unit_description())

    def get_quantity_delivered(self):
        delivered = Decimal(0)
        for service in self.sale.services:
            delivery = IDelivery(service, None)
            if not delivery:
                continue
            item = delivery.get_item_by_sellable(self.sellable)
            if not item:
                continue
            delivered += item.quantity

        return delivered

    def has_been_totally_delivered(self):
        return self.get_quantity_delivered() == self.quantity

    def get_description(self):
        return self.sellable.base_sellable_info.get_description()


class DeliveryItem(Domain):
    """Class responsible to store all the products for a certain delivery"""

    quantity = DecimalCol()
    sellable = ForeignKey('Sellable')
    delivery = ForeignKey('SaleItem', default=None)

    #
    # Accessors
    #

    def get_price(self):
        return self.sellable.price

    def get_total(self):
        return currency(self.get_price() * self.quantity)

    @classmethod
    def create_from_sellable_item(cls, sale_item):
        if not sale_item.sellable.product:
            raise SellError(
                "It's only possible to deliver products, not %r" % (
                type(sale_item),))

        quantity = sale_item.quantity - sale_item.get_quantity_delivered()
        return cls(connection=sale_item.get_connection(),
                   sellable=sale_item.sellable,
                   quantity=quantity)


class SaleItemAdaptToDelivery(ModelAdapter):
    """A service implementation as a delivery facet."""

    implements(IDelivery, IContainer)

    address = UnicodeCol(default='')

    #
    # IContainer implementation
    #

    @argcheck(DeliveryItem)
    def add_item(self, item):
        item.delivery = self

    def get_items(self):
        return DeliveryItem.selectBy(connection=self.get_connection(),
                                     delivery=self)

    @argcheck(DeliveryItem)
    def remove_item(self, item):
        DeliveryItem.delete(item.id, connection=item.get_connection())


    #
    # General methods
    #

    @argcheck(Sellable)
    def get_item_by_sellable(self, sellable):
        return DeliveryItem.selectOneBy(connection=self.get_connection(),
                                        delivery=self,
                                        sellable=sellable)

SaleItem.registerFacet(SaleItemAdaptToDelivery, IDelivery)



class Sale(ValidatableDomain):
    """Sale object implementation.

    @cvar STATUS_INITIAL: The sale is opened, products or other sellable items
      might have been added.
    @cvar STATUS_ORDERED: The sale is orded, it has sellable items but not any
      payments yet. This state is mainly used when the parameter
      CONFIRM_SALES_AT_TILL is enabled.
    @cvar STATUS_CONFIRMED: The sale has been confirmed and all payments
      have been registered, but not necessarily paid.
    @cvar STATUS_CLOSED: All the payments of the sale has been confirmed
      and the client does not owe anything to us.
    @cvar STATUS_CANCELLED: The sale has been canceled, this can only happen
      to an sale which has not yet reached the SALE_CONFIRMED status.
    @cvar STATUS_RETURNED: The sale has been returned, all the payments made
      have been canceled and the client has been compensated for
      everything already paid.
    @cvar CLIENT_INDIVIDUAL: The sale was done by an individual
    @cvar CLIENT_COMPANY: The sale was done by a company
    @ivar status: status of the sale
    @ivar client: who we sold the sale to
    @ivar salesperson: who sold the sale
    @ivar branch: branch where the sale was done
    @ivar till: The Till operation where this sale lives. Note that every
       sale and payment generated are always in a till operation
       which defines a financial history of a store.
    @ivar open_date: the date sale was created
    @ivar close_date: the date sale was closed
    @ivar confirm_date: the date sale was confirmed
    @ivar cancel_date: the date sale was cancelled
    @ivar return_date: the date sale was returned
    @ivar discount_value:
    @ivar surcharge_value:
    @ivar total_amount: the total value of all the items in the same
    @ivar notes: Some optional additional information related to this sale.
    @ivar coupon_id:
    @ivar service_invoice_number:
    @ivar cfop:
    """

    implements(IContainer)

    (STATUS_INITIAL,
     STATUS_CONFIRMED,
     STATUS_PAID,
     STATUS_CANCELLED,
     STATUS_ORDERED,
     STATUS_RETURNED) = range(6)

    statuses = {STATUS_INITIAL:     _(u"Opened"),
                STATUS_CONFIRMED:   _(u"Confirmed"),
                STATUS_PAID:        _(u"Paid"),
                STATUS_CANCELLED:   _(u"Cancelled"),
                STATUS_ORDERED:     _(u"Ordered"),
                STATUS_RETURNED:    _(u"Returned")}

    status = IntCol(default=STATUS_INITIAL)
    coupon_id = IntCol()
    service_invoice_number = IntCol(default=None)
    notes = UnicodeCol(default='')
    open_date = DateTimeCol(default=datetime.datetime.now)
    confirm_date = DateTimeCol(default=None)
    close_date = DateTimeCol(default=None)
    cancel_date = DateTimeCol(default=None)
    return_date = DateTimeCol(default=None)
    discount_value = PriceCol(default=0)
    surcharge_value = PriceCol(default=0)
    total_amount = PriceCol(default=0)
    cfop = ForeignKey("CfopData")
    client = ForeignKey('PersonAdaptToClient', default=None)
    salesperson = ForeignKey('PersonAdaptToSalesPerson')
    branch = ForeignKey('PersonAdaptToBranch', default=None)
    group = ForeignKey('PaymentGroup')

    #
    # ORMObject hooks
    #

    def _create(self, id, **kw):
        conn = self.get_connection()
        if not 'cfop' in kw:
            kw['cfop'] = sysparam(conn).DEFAULT_SALES_CFOP
        Domain._create(self, id, **kw)

    #
    # Classmethods
    #

    @classmethod
    def get_status_name(cls, status):
        if not status in cls.statuses:
            raise DatabaseInconsistency("Invalid status %d" % status)
        return cls.statuses[status]

    @classmethod
    def get_last_confirmed(cls, conn):
        """Fetch the last confirmed sale
        @param conn: a database connection
        """
        results = cls.select(AND(cls.q.status == cls.STATUS_CONFIRMED,
                                 cls.q.confirm_date != None),
                             orderBy='-confirm_date',
                             connection=conn).limit(1)
        if results:
            return results[0]

    #
    # IContainer implementation
    #

    @argcheck(SaleItem)
    def add_item(self, sale_item):
        assert not sale_item.sale
        sale_item.sale = self

    def get_items(self):
        return SaleItem.selectBy(sale=self, connection=self.get_connection())

    @argcheck(SaleItem)
    def remove_item(self, sale_item):
        SaleItem.delete(sale_item.id, connection=self.get_connection())

    # Status

    def can_order(self):
        """Only newly created sales can be ordered
        @returns: True if the sale can be ordered, otherwise False
        """
        return self.status == Sale.STATUS_INITIAL

    def can_confirm(self):
        """Only ordered sales can be confirmed
        @returns: True if the sale can be confirmed, otherwise False
        """
        return self.status == Sale.STATUS_ORDERED

    def can_set_paid(self):
        """Only confirmed sales can be paid
        @returns: True if the sale can be set as paid, otherwise False
        """
        return self.status == Sale.STATUS_CONFIRMED

    def can_cancel(self):
        """Only ordered, confirmed and paid sales can be cancelled.
        @returns: True if the sale can be cancelled, otherwise False
        """
        return self.status in (Sale.STATUS_CONFIRMED, Sale.STATUS_PAID,
                               Sale.STATUS_ORDERED)

    def can_return(self):
        """Only confirmed or paid sales can be returned
        @returns: True if the sale can be returned, otherwise False
        """
        return (self.status == Sale.STATUS_CONFIRMED or
                self.status == Sale.STATUS_PAID)

    def order(self):
        """Orders the sale
        Ordering a sale is the first step done after creating it.
        The state of the sale will change to Sale.STATUS_ORDERED.
        To order a sale you need to add sale items to it.
        A client might also be set for the sale, but it is not necessary.
        """
        assert self.can_order()

        if not self.get_items():
            raise SellError('The sale must have sellable items')
        if self.client and not self.client.is_active:
            raise SellError('Unable to make sales for clients with status '
                            '%s' % self.client.get_status_string())

        self.set_valid()

        self.status = Sale.STATUS_ORDERED

    def confirm(self):
        """Confirms the sale
        Confirming a sale means that the customer has confirmed the sale.
        Sale items containing products are physically received and
        the payments are agreed upon but not necessarily received.
        """
        assert self.can_confirm()
        assert self.branch

        # FIXME: We should use self.branch, but it's not supported yet
        conn = self.get_connection()
        branch = get_current_branch(conn)
        for item in self.get_items():
            if item.sellable.product:
                ProductHistory.add_sold_item(conn, branch, item)
            item.sell(branch)

        self.total_amount = self.get_total_sale_amount()

        transaction = IPaymentTransaction(self)
        transaction.confirm()

        SaleConfirmEvent.emit(self, conn)

        self.confirm_date = const.NOW()
        self.status = Sale.STATUS_CONFIRMED

    def set_paid(self):
        """Mark the sale as paid
        Marking a sale as paid means that all the payments have been received.
        """
        assert self.can_set_paid()

        for payment in self.group.payments:
            if not payment.is_paid():
                raise StoqlibError(
                    "You cannot close a sale without paying all the payment. "
                    "Payment %r is still not paid" % (payment,))

        transaction = IPaymentTransaction(self)
        transaction.pay()

        self.close_date = const.NOW()
        self.status = Sale.STATUS_PAID

    def cancel(self):
        """Cancel the sale
        You can only cancel an ordered sale, it'll un-reserve all sale items.
        and mark the sale as cancelled.
        """
        assert self.can_cancel()

        conn = self.get_connection()
        # FIXME: We should use self.branch, but it's not supported yet
        branch = get_current_branch(conn)
        for item in self.get_items():
            item.cancel(branch)

        self.cancel_date = const.NOW()
        self.status = Sale.STATUS_CANCELLED

    @argcheck(RenegotiationData)
    def return_(self, renegotiation):
        """Returns a sale
        Returning a sale means that all the items are returned to the item.
        A renegotiation object needs to be supplied which
        contains the invoice number and the eventual penalty

        @param renegotiation: renegotiation information
        @type renegotiation: L{RenegotiationData}
        """
        assert self.can_return()

        transaction = IPaymentTransaction(self)
        transaction.return_(renegotiation)

        self.return_date = const.NOW()
        self.status = Sale.STATUS_RETURNED

    #
    # Accessors
    #

    def get_total_sale_amount(self):
        """
        Fetches the total value  paid by the client.
        It can be calculated as::

            Sale total = Sum(product and service prices) + surcharge +
                             interest - discount

        @returns: the total value
        """
        surcharge_value = self.surcharge_value or Decimal(0)
        discount_value = self.discount_value or Decimal(0)
        subtotal = self.get_sale_subtotal()
        total_amount = subtotal + surcharge_value - discount_value
        return currency(total_amount)

    def get_sale_subtotal(self):
        """Fetch the subtotal for the sale, eg the sum of the
        prices for of all items
        @returns: subtotal
        """
        return currency(self.get_items().sum(
            SaleItem.q.price *
            SaleItem.q.quantity) or 0)

    def get_items_total_quantity(self):
        """Fetches the total number of items in the sale
        @returns: number of items
        """
        return self.get_items().sum('quantity') or Decimal(0)

    def get_order_number_str(self):
        return u'%05d' % self.id

    def get_salesperson_name(self):
        return self.salesperson.get_description()

    def get_client_name(self):
        if not self.client:
            return _(u'Not Specified')
        return self.client.get_name()

    def get_client_role(self):
        """Fetches the client role

        @returns: the client role (a PersonAdaptToIndividual or a
        PersonAdaptToCompany) instance or None if the sale haven't a client.
        """
        if not self.client:
            return None
        client_role = self.client.person.has_individual_or_company_facets()
        if client_role is None:
            raise DatabaseInconsistency("The sale %r have a client but no "
                                        "client_role defined." % self)

        return client_role

    # Other methods

    def paid_with_money(self):
        """Find out if the sale is paid using money
        @returns: True if the sale was paid with money, otherwise False
        @rtype: bool
        """
        for payment in self.group.payments:
            if payment.method.method_name != 'money':
                return False
        return True

    def add_sellable(self, sellable, quantity=1, price=None):
        """Adds a new sellable item to a sale
        @param sellable: the sellable
        @param quantity: quantity to add, defaults to 1
        @param price: optional, the price, it not set the price
          from the sellable will be used
        """
        price = price or sellable.price
        return SaleItem(connection=self.get_connection(),
                        quantity=quantity,
                        sale=self,
                        sellable=sellable,
                        price=price)


    def create_sale_return_adapter(self):
        conn = self.get_connection()
        current_user = get_current_user(conn)
        assert current_user
        paid_total = self.group.get_total_paid()
        return RenegotiationData(connection=conn,
                                 paid_total=paid_total,
                                 invoice_number=None,
                                 responsible=current_user.person,
                                 sale=self)

    #
    # Properties
    #

    @property
    def order_number(self):
        return self.id

    @property
    def products(self):
        return SaleItem.select(
            AND(SaleItem.q.saleID == self.id,
                SaleItem.q.sellableID == Product.q.sellableID),
            connection=self.get_connection())

    @property
    def services(self):
        return SaleItem.select(
            AND(SaleItem.q.saleID == self.id,
                SaleItem.q.sellableID == Service.q.sellableID),
            connection=self.get_connection())

    @property
    def payments(self):
        return Payment.selectBy(group=self.group,
                                connection=self.get_connection())

    def _get_discount_by_percentage(self):
        discount_value = self.discount_value
        if not discount_value:
            return Decimal(0)
        subtotal = self.get_sale_subtotal()
        assert subtotal > 0, ('the sale subtotal should not be zero '
                              'at this point')
        total = subtotal - discount_value
        percentage = (1 - total / subtotal) * 100
        return quantize(percentage)

    def _set_discount_by_percentage(self, value):
        self.discount_value = self._get_percentage_value(value)

    discount_percentage = property(_get_discount_by_percentage,
                                   _set_discount_by_percentage,
                                   doc=(
        """Sets a discount by percentage.
        Note that percentage must be added as an absolute value not as a
        factor like 1.05 = 5 % of surcharge
        The correct form is 'percentage = 3' for a discount of 3 %"""
        ))

    def _get_surcharge_by_percentage(self):
        surcharge_value = self.surcharge_value
        if not surcharge_value:
            return Decimal(0)
        subtotal = self.get_sale_subtotal()
        assert subtotal > 0, ('the sale subtotal should not be zero '
                              'at this point')
        total = subtotal + surcharge_value
        percentage = ((total / subtotal) - 1) * 100
        return quantize(percentage)

    def _set_surcharge_by_percentage(self, value):
        self.surcharge_value = self._get_percentage_value(value)

    surcharge_percentage = property(_get_surcharge_by_percentage,
                                    _set_surcharge_by_percentage,
                                    doc=(
        """Sets a surcharge by percentage.
        Note that surcharge must be added as an absolute value not as a
        factor like 0.97 = 3 % of discount.
        The correct form is 'percentage = 3' for a surcharge of 3 %"""
        ))

    #
    # Private API
    #

    def _get_percentage_value(self, percentage):
        if not percentage:
            return currency(0)
        subtotal = self.get_sale_subtotal()
        percentage = Decimal(percentage)
        perc_value = subtotal * (percentage / Decimal(100))
        return currency(perc_value)


#
# Adapters
#


class SaleAdaptToPaymentTransaction(object):
    implements(IPaymentTransaction)

    def __init__(self, sale):
        self.sale = sale

    #
    # IPaymentTransaction
    #

    def confirm(self):
        self.sale.group.confirm()

        self._add_inpayments()
        self._create_fiscal_entries()

        if self._create_commission_at_confirm():
            for payment in self.sale.payments:
                self._create_commission(payment)

    def pay(self):
        create_commission = not self._create_commission_at_confirm()
        if not create_commission:
            return
        for payment in self.sale.payments:
            # FIXME: This shouldn't be needed, something is called
            #        twice where it shouldn't be
            if self._already_have_commission(payment):
                continue
            commission = self._create_commission(payment)
            if IOutPayment(payment, None) is not None:
                commission.value = -commission.value

    def cancel(self):
        pass

    def return_(self, renegotiation):
        assert self.sale.group.can_cancel()

        for sale_item in self.sale.get_items():
            sale_item.cancel(self.sale.branch)
        self._payback_paid_payments(renegotiation.penalty_value)
        self._revert_fiscal_entry(renegotiation.invoice_number)
        self.sale.group.cancel()

    #
    # Private API
    #

    def _create_commission(self, payment):
        from stoqlib.domain.commission import Commission
        return Commission(commission_type=self._get_commission_type(),
                          sale=self.sale,
                          payment=payment,
                          salesperson=self.sale.salesperson,
                          connection=self.sale.get_connection())

    def _add_inpayments(self):
        payments = self.sale.payments
        if not payments.count():
            raise ValueError(
                'You must have at least one payment for each payment group')

        till = Till.get_current(self.sale.get_connection())
        for payment in payments:
            assert payment.is_pending(), payment.get_status_str()
            assert IInPayment(payment, None)
            till.add_entry(payment)

        # FIXME: Move this to a payment method specific hook
        if payments.count() == 1 and payment.method.method_name == 'money':
            self.sale.group.pay()
            self.pay()

    def _create_commission_at_confirm(self):
        conn = self.sale.get_connection()
        return sysparam(conn).SALE_PAY_COMMISSION_WHEN_CONFIRMED

    def _get_commission_type(self):
        from stoqlib.domain.commission import Commission

        nitems = 0
        for item in self.sale.group.payments:
            if IOutPayment(item, None) is None:
                nitems += 1

        if nitems <= 1:
            return Commission.DIRECT
        return Commission.INSTALLMENTS

    def _already_have_commission(self, payment):
        from stoqlib.domain.commission import Commission

        commission = Commission.selectOneBy(
            payment=payment,
            connection=self.sale.get_connection())
        return commission is not None

    def _restore_commission(self, payment):
        from stoqlib.domain.commission import Commission
        old_commission_value = Commission.selectBy(
            sale=self.sale,
            connection=self.sale.get_connection()).sum('value')
        if old_commission_value > 0:
            commission = self._create_commission(payment)
            commission.value = -old_commission_value

    def _payback_paid_payments(self, penalty_value):
        conn = self.sale.get_connection()
        till = Till.get_current(conn)
        paid_value = self.sale.group.get_total_paid()
        till_difference = self.sale.get_total_sale_amount() - paid_value

        if till_difference > 0:
            # The sale was not entirely paid, so we have to payback the
            # till, because the sale amount have already been added in there
            desc = _(u'Debit on Till: Sale %d Returned') % self.sale.id
            till.add_debit_entry(till_difference, desc)
        # Update paid value now, penalty stays on till
        paid_value -= penalty_value
        if not paid_value:
            return

        money = PaymentMethod.get_by_name(conn, 'money')
        out_payment = money.create_outpayment(
            self.sale.group, paid_value,
            description=_('%s Money Returned for Sale %d') % (
            '1/1', self.sale.id), till=till)
        payment = out_payment.get_adapted()
        payment.set_pending()
        payment.pay()
        self._restore_commission(payment)
        till.add_entry(payment)

    def _revert_fiscal_entry(self, invoice_number):
        entry = FiscalBookEntry.selectOneBy(
            payment_group=self.sale.group,
            connection=self.sale.get_connection())
        if entry is not None:
            entry.reverse_entry(invoice_number)

    def _get_pm_commission_total(self):
        """Return the payment method commission total. Usually credit
        card payment method is the most common method which uses
        commission
        """
        return currency(0)

    def _get_icms_total(self, av_difference):
        """A Brazil-specific method
        Calculates the icms total value

        @param av_difference: the average difference for the sale items.
                              it means the average discount or surcharge
                              applied over all sale items
        """
        icms_total = Decimal(0)
        conn = self.sale.get_connection()
        for item in self.sale.products:
            price = item.price + av_difference
            sellable = item.sellable
            tax_constant = sellable.get_tax_constant()
            if tax_constant is None or tax_constant.tax_type != TaxType.CUSTOM:
                continue
            icms_tax = tax_constant.tax_value / Decimal(100)
            icms_total += icms_tax * (price * item.quantity)

        return icms_total

    def _get_iss_total(self, av_difference):
        """A Brazil-specific method
        Calculates the iss total value

        @param av_difference: the average difference for the sale items.
                              it means the average discount or surcharge
                              applied over all sale items
        """
        iss_total = Decimal(0)
        conn = self.sale.get_connection()
        iss_tax = sysparam(conn).ISS_TAX / Decimal(100)
        for item in self.sale.services:
            price = item.price + av_difference
            iss_total += iss_tax * (price * item.quantity)
        return iss_total

    def _has_iss_entry(self):
        return FiscalBookEntry.has_entry_by_payment_group(
            self.sale.get_connection(),
            self.sale.group,
            type=FiscalBookEntry.TYPE_SERVICE)

    def _has_icms_entry(self):
        return FiscalBookEntry.has_entry_by_payment_group(
            self.sale.get_connection(),
            self.sale.group,
            type=FiscalBookEntry.TYPE_PRODUCT)

    def _get_average_difference(self):
        sale = self.sale
        if not sale.get_items().count():
            raise DatabaseInconsistency(
                "Sale orders must have items, which means products or "
                "services")
        total_quantity = sale.get_items_total_quantity()
        if not total_quantity:
            raise DatabaseInconsistency("Sale total quantity should never "
                                        "be zero")
        # If there is a discount or a surcharge applied in the whole total
        # sale amount, we must share it between all the item values
        # otherwise the icms and iss won't be calculated properly
        total = (sale.get_total_sale_amount() -
                 self._get_pm_commission_total())
        subtotal = sale.get_sale_subtotal()
        return (total - subtotal) / total_quantity

    def _get_iss_entry(self):
        return FiscalBookEntry.get_entry_by_payment_group(
            self.sale.get_connection(), self.sale.group,
            FiscalBookEntry.TYPE_SERVICE)

    def _create_fiscal_entries(self):
        """A Brazil-specific method
        Create new ICMS and ISS entries in the fiscal book
        for a given sale.

        Important: freight and interest are not part of the base value for
        ICMS. Only product values and surcharge which applies increasing the
        product totals are considered here.
        """
        sale = self.sale
        av_difference = self._get_average_difference()

        if sale.products:
            FiscalBookEntry.create_product_entry(
                sale.get_connection(),
                sale.group, sale.cfop, sale.coupon_id,
                self._get_icms_total(av_difference))

        if sale.services and sale.service_invoice_number:
            FiscalBookEntry.create_service_entry(
                sale.get_connection(),
                sale.group, sale.cfop, sale.service_invoice_number,
                self._get_iss_total(av_difference))

Sale.registerFacet(SaleAdaptToPaymentTransaction, IPaymentTransaction)


#
# Views
#


class SaleView(ORMObject, BaseSQLView):
    """Stores general informatios about sales"""
    coupon_id = IntCol()
    open_date = DateTimeCol()
    close_date = DateTimeCol()
    confirm_date = DateTimeCol()
    cancel_date = DateTimeCol()
    status = IntCol()
    notes = UnicodeCol()
    salesperson_name = UnicodeCol()
    client_name = UnicodeCol()
    client_id = IntCol()
    surcharge_value = PriceCol()
    discount_value = PriceCol()
    subtotal = PriceCol()
    total = PriceCol()
    total_quantity = DecimalCol()

    #
    # Properties
    #

    @property
    def sale(self):
        return Sale.get(self.id)

    #
    # Public API
    #

    def get_client_name(self):
        return self.client_name or u""

    def get_order_number_str(self):
        return u"%05d" % self.id

    def get_open_date_as_string(self):
        return self.open_date.strftime("%x")

    def get_status_name(self):
        return Sale.get_status_name(self.status)

