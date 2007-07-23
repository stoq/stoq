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
##              Henrique Romano             <henrique@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
""" Sale object and related objects implementation """

import datetime
from decimal import Decimal

from kiwi.argcheck import argcheck
from kiwi.datatypes import currency
from sqlobject.col import ForeignKey, UnicodeCol, DateTimeCol, IntCol
from sqlobject.main import SQLObject
from sqlobject.sqlbuilder import AND
from stoqdrivers.enum import TaxType
from zope.interface import implements

from stoqlib.database.columns import PriceCol, DecimalCol
from stoqlib.database.runtime import (get_current_user,
                                      get_current_branch)
from stoqlib.domain.base import (Domain, ValidatableDomain, BaseSQLView,
                                 ModelAdapter)
from stoqlib.domain.commissions import Commission
from stoqlib.domain.events import SaleConfirmEvent
from stoqlib.domain.fiscal import FiscalBookEntry
from stoqlib.domain.giftcertificate import GiftCertificate
from stoqlib.domain.interfaces import (IContainer, IClient,
                                       IPaymentGroup, ISellable,
                                       IIndividual, ICompany,
                                       IDelivery, IStorable)
from stoqlib.domain.payment.group import AbstractPaymentGroup
from stoqlib.domain.payment.methods import MoneyPM
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.product import (Product, ProductAdaptToSellable,
                                    ProductHistory)
from stoqlib.domain.renegotiation import RenegotiationData
from stoqlib.domain.sellable import ASellable
from stoqlib.domain.service import Service, ServiceAdaptToSellable
from stoqlib.domain.till import Till
from stoqlib.exceptions import (SellError, DatabaseInconsistency,
                                StoqlibError)
from stoqlib.lib.defaults import quantize
from stoqlib.lib.validators import get_formatted_price
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam


_ = stoqlib_gettext

#
# Base Domain Classes
#

class SaleItem(Domain):
    """
    An item in a sale.

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
    sellable = ForeignKey('ASellable')

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

        # FIXME: Don't use sellable.get_adapted()
        adapted = self.sellable.get_adapted()
        storable = IStorable(adapted, None)
        if storable:
            # Update the stock
            storable.decrease_stock(self.quantity, branch)

            # The function get_full_balance returns the current amount of items
            # in the stock. If get_full_balance == 0 we have no more stock for
            # this product and we need to set it as sold.
            logic_qty = storable.get_logic_balance()
            balance = storable.get_full_balance() - logic_qty
            if balance:
                # This marks the sellable as not available, eg out of stock
                # FIXME: rename
                self.sellable.sell()

    def cancel(self, branch):
        # FIXME: Don't use sellable.get_adapted()
        adapted = self.sellable.get_adapted()
        storable = IStorable(adapted)
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



class DeliveryItem(Domain):
    """Class responsible to store all the products for a certain delivery"""

    quantity = DecimalCol()
    sellable = ForeignKey('ASellable')
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
        if not isinstance(sale_item.sellable.get_adapted(), Product):
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

    @argcheck(ASellable)
    def get_item_by_sellable(self, sellable):
        return DeliveryItem.selectOneBy(connection=self.get_connection(),
                                        delivery=self,
                                        sellable=sellable)

SaleItem.registerFacet(SaleItemAdaptToDelivery, IDelivery)



class Sale(ValidatableDomain):
    """
    Sale object implementation.

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
    @ivar notes: Some optional additional information related to this sale.
    @ivar client_role: This field indicates what client role is tied with
       the sale order. This is important since a client can have two roles
       associated, i.e, Individual and/or Company. This is useful when
       printing the sale invoice. One of Sale.CLIENT_INDIVIDUAL or
       Sale.CLIENT_COMPANY.
    @ivar coupon_id:
    @ivar service_invoice_number:
    @ivar cfop:
    @ivar renegotiation_data:
    """

    implements(IContainer)

    (STATUS_INITIAL,
     STATUS_CONFIRMED,
     STATUS_PAID,
     STATUS_CANCELLED,
     STATUS_ORDERED,
     STATUS_RETURNED) = range(6)

    (CLIENT_INDIVIDUAL,
     CLIENT_COMPANY) = range(2)

    statuses = {STATUS_INITIAL:     _(u"Opened"),
                STATUS_CONFIRMED:   _(u"Confirmed"),
                STATUS_PAID:        _(u"Paid"),
                STATUS_CANCELLED:   _(u"Cancelled"),
                STATUS_ORDERED:     _(u"Ordered"),
                STATUS_RETURNED:    _(u"Returned")}

    status = IntCol(default=STATUS_INITIAL)
    client = ForeignKey('PersonAdaptToClient', default=None)
    salesperson = ForeignKey('PersonAdaptToSalesPerson')
    branch = ForeignKey('PersonAdaptToBranch', default=None)
    open_date = DateTimeCol(default=datetime.datetime.now)
    confirm_date = DateTimeCol(default=None)
    close_date = DateTimeCol(default=None)
    cancel_date = DateTimeCol(default=None)
    return_date = DateTimeCol(default=None)
    discount_value = PriceCol(default=0)
    surcharge_value = PriceCol(default=0)
    notes = UnicodeCol(default='')
    coupon_id = IntCol()
    service_invoice_number = IntCol(default=None)
    client_role = IntCol(default=None)
    cfop = ForeignKey("CfopData")

    #
    # SQLObject hooks
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
        """
        Fetch the last confirmed sale
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

    # New API

    def can_order(self):
        """
        @returns: True if the sale can be ordered, otherwise False
        """
        return self.status == Sale.STATUS_INITIAL

    def can_confirm(self):
        """
        @returns: True if the sale can be confirmed, otherwise False
        """
        return self.status == Sale.STATUS_ORDERED

    def can_set_paid(self):
        """
        @returns: True if the sale can be set as paid, otherwise False
        """
        return self.status == Sale.STATUS_CONFIRMED

    def can_cancel(self):
        """
        @returns: True if the sale can be cancelled, otherwise False
        """
        return self.status == Sale.STATUS_ORDERED

    def can_return(self):
        """
        @returns: True if the sale can be returned, otherwise False
        """
        return (self.status == Sale.STATUS_CONFIRMED or
                self.status == Sale.STATUS_PAID)

    def order(self):
        assert self.can_order()

        if not self.get_items():
            raise SellError('The sale must have sellable items')
        if self.client and not self.client.is_active:
            raise SellError('Unable to make sales for clients with status '
                            '%s' % self.client.get_status_string())

        self.set_valid()

        self.status = Sale.STATUS_ORDERED

    def confirm(self):
        assert self.can_confirm()
        assert self.branch

        conn = self.get_connection()

        # FIXME: We should use self.branch, but it's not supported yet
        branch = get_current_branch(conn)
        for item in self.get_items():
            if isinstance(item.sellable.get_adapted(), Product):
                ProductHistory.add_sold_item(conn, branch, item)
            item.sell(branch)

        group = IPaymentGroup(self)
        group.confirm()

        SaleConfirmEvent.emit(self)
        self.confirm_date = datetime.datetime.now()
        self.status = Sale.STATUS_CONFIRMED

    def set_paid(self):
        assert self.can_set_paid()

        group = IPaymentGroup(self)
        for payment in group.get_items():
            if not payment.is_paid():
                raise StoqlibError(
                    "You cannot close a sale without paying all the payment")

        self.close_date = datetime.datetime.now()
        self.status = Sale.STATUS_PAID

    def cancel(self):
        assert self.can_cancel()

        conn = self.get_connection()
        # FIXME: We should use self.branch, but it's not supported yet
        branch = get_current_branch(conn)
        for item in self.get_items():
            item.cancel(branch)

        self.cancel_date = datetime.datetime.now()
        self.status = Sale.STATUS_CANCELLED

    @argcheck(RenegotiationData)
    def return_(self, renegotiation):
        """
        Return an sold item, needs to supply a renegotiation object which
        contains the invoice number and the eventual penalty
        @param renegotiation: renegotiation information
        @type renegotiation: L{RenegotiationData}
        """
        assert self.can_return()

        group = IPaymentGroup(self)
        group.cancel(renegotiation)

        self.return_date = datetime.datetime.now()
        self.status = Sale.STATUS_RETURNED

    def paid_with_money(self):
        from stoqlib.domain.payment.methods import MoneyPM
        group = IPaymentGroup(self, None)
        assert group
        for payment in group.get_items():
            if not isinstance(payment.method, MoneyPM):
                return False
        return True

    def add_sellable(self, obj, quantity=1, price=None):
        """
        Adds a new sellable item to a sale
        @param obj: the sellable
        @param quantity: quantity to add, defaults to 1
        @param price: optional, the price, it not set the price
          from the sellable will be used
        """
        sellable = ISellable(obj)
        price = price or sellable.price
        return SaleItem(connection=self.get_connection(),
                        quantity=quantity,
                        sale=self,
                        sellable=sellable,
                        price=price)


    def get_items_total_quantity(self):
        return self.get_items().sum('quantity') or Decimal(0)

    def create_sale_return_adapter(self):
        conn = self.get_connection()
        current_user = get_current_user(conn)
        assert current_user
        group = IPaymentGroup(self)
        paid_total = group.get_total_paid()
        return RenegotiationData(connection=conn,
                                     paid_total=paid_total,
                                     invoice_number=None,
                                     responsible=current_user.person,
                                     sale=self)

    #
    # MOVE away!
    #


    @argcheck(Decimal, unicode)
    def add_custom_gift_certificate(self, certificate_value,
                                    certificate_number):
        """This method adds a new custom gift certificate to the current
        sale order.

        @returns: a GiftCertificateAdaptToSellable instance
        """
        conn = self.get_connection()
        cert_type = sysparam(conn).DEFAULT_GIFT_CERTIFICATE_TYPE
        sellable_info = cert_type.base_sellable_info.clone()
        if not sellable_info:
            raise ValueError('A valid gift certificate type must be '
                             'provided at this point')
        sellable_info.price = certificate_value
        certificate = GiftCertificate(connection=conn)
        sellable_cert = certificate.addFacet(ISellable, connection=conn,
                                             barcode=certificate_number,
                                             base_sellable_info=
                                             sellable_info)
        # The new gift certificate which has been created is actually an
        # item of our sale order
        self.add_sellable(sellable_cert)
        return sellable_cert

    def get_clone(self):
        conn = self.get_connection()
        return Sale(client_role=self.client_role, client=self.client,
                    cfop=self.cfop, coupon_id=None, branch=self.branch,
                    salesperson=self.salesperson, connection=conn)

    #
    # Accessors
    #

    def get_order_number_str(self):
        return u'%05d' % self.id

    def get_salesperson_name(self):
        return self.salesperson.get_description()

    def get_client_name(self):
        if not self.client:
            return _(u'Not Specified')
        return self.client.get_name()

    # Warning: "get_client_role" would be a Kiwi accessor here and this is not
    # what we want.
    def get_sale_client_role(self):
        if not self.client:
            return None
        person = self.client.person
        if self.client_role is None:
            raise DatabaseInconsistency("The sale %r have a client but no "
                                        "client_role defined." % self)
        elif self.client_role == Sale.CLIENT_INDIVIDUAL:
            return IIndividual(person)
        elif self.client_role == Sale.CLIENT_COMPANY:
            return ICompany(person)
        else:
            raise DatabaseInconsistency("Invalid client_role for sale %r, "
                                        "got %r" % (self, self.client_role))

    # XXX: depends on bug #2893
#     def _set_client_role(self, value):
#         if value not in (Sale.CLIENT_INDIVIDUAL,
#                          Sale.CLIENT_COMPANY):
#             raise TypeError("The client role should be one of constantes "
#                             "CLIENT_INDIVIDUAL or CLIENT_COMPANY")
#         self._SO_set_client_role(value)


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

    #
    # Re-evaluate
    #

    def check_payment_group(self):
        return IPaymentGroup(self, None)

    def update_client(self, person):
        # Do not change the name of this method to set_client: this is a
        # callback in SQLObject
        self.client = IClient(person)

    def reset_discount_and_surcharge(self):
        self.discount_value = self.surcharge_value = currency(0)

    def get_total_interest(self):
        raise NotImplementedError

    def has_items(self):
        return self.get_items().count() > 0

    def get_total_amount_as_string(self):
        return get_formatted_price(self.get_total_sale_amount())

    def get_sale_subtotal(self):
        # FIXME: Use SQL
        subtotal = sum([item.get_total() for item in self.get_items()],
                       currency(0))
        return currency(subtotal)

    def get_items_total_value(self):
        # FIXME: Use SQL
        total = sum([item.get_total() for item in self.get_items()],
                   currency(0))
        return currency(total)

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
                SaleItem.q.sellableID == ProductAdaptToSellable.q.id,
                ProductAdaptToSellable.q._originalID == Product.q.id),
            connection=self.get_connection())

    @property
    def services(self):
        return SaleItem.select(
            AND(SaleItem.q.saleID == self.id,
                SaleItem.q.sellableID == ServiceAdaptToSellable.q.id,
                ServiceAdaptToSellable.q._originalID == Service.q.id),
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


class SaleAdaptToPaymentGroup(AbstractPaymentGroup):

    _inheritable = False

    #
    # Properties
    #

    @property
    def sale(self):
        return self.get_adapted()

    #
    # IPaymentGroup implementation
    #

    def get_thirdparty(self):
        client = self.sale.client
        return client and client.person or None

    def get_group_description(self):
        return _(u'sale %s') % self.sale.get_order_number_str()

    def get_total_received(self):
        return (self.sale.get_total_sale_amount() -
                self._get_pm_commission_total())

    def get_default_payment_method(self):
        return self.default_method

    def confirm(self):
        self.add_inpayments()
        self._create_fiscal_entries()

        if self._pay_commission_at_confirm():
            conn = self.get_connection()
            type = self._get_commission_type()
            for item in self.get_items():
                Commission(commission_type=type,
                           sale=self.sale, payment=item,
                           salesperson=self.sale.salesperson,
                           connection=conn)

    def _pay_commission_at_confirm(self):
        conn = self.get_connection()
        return sysparam(conn).SALE_PAY_COMMISSION_WHEN_CONFIRMED

    def _get_commission_type(self):
        items = self.get_items()
        if items.count() == 1:
            return Commission.DIRECT
        return Commission.INSTALLMENTS

    def pay(self, payment):
        if not self._pay_commission_at_confirm():
            Commission(commission_type=self._get_commission_type(),
                       sale=self.sale, payment=payment,
                       salesperson=self.sale.salesperson,
                       connection=self.get_connection())

    def cancel(self, renegotiation):
        assert self.can_cancel()

        self._cancel_pending_payments()
        self._payback_paid_payments()
        self._revert_fiscal_entry(renegotiation.invoice_number)

        AbstractPaymentGroup.cancel(self, renegotiation)


    # Private API
    #

    def _cancel_pending_payments(self):
        for payment in Payment.selectBy(group=self,
                                        status=Payment.STATUS_PENDING,
                                        connection=self.get_connection()):
            payment.cancel()

    def _payback_paid_payments(self):
        paid_value = self.get_total_paid()
        if not paid_value:
            return

        conn = self.get_connection()
        till = Till.get_current(conn)
        money = MoneyPM.selectOne(connection=conn)
        out_payment = money.create_outpayment(
            self, paid_value,
            description=_('%s Money Returned for Sale %d') % (
            '1/1', self.sale.id), till=till)
        payment = out_payment.get_adapted()
        payment.set_pending()
        payment.pay()

        till.add_entry(payment)

    def _revert_fiscal_entry(self, invoice_number):
        entry = FiscalBookEntry.selectOneBy(
            payment_group=self,
            connection=self.get_connection())
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
        conn = self.get_connection()
        for item in self.sale.products:
            price = item.price + av_difference
            sellable = item.sellable
            if sellable.tax_constant.tax_type != TaxType.CUSTOM:
                continue
            tax_constant = sellable.get_tax_constant()
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
        conn = self.get_connection()
        iss_tax = sysparam(conn).ISS_TAX / Decimal(100)
        for item in self.sale.services:
            price = item.price + av_difference
            iss_total += iss_tax * (price * item.quantity)
        return iss_total

    def _has_iss_entry(self):
        return FiscalBookEntry.has_entry_by_payment_group(
            self.get_connection(),
            self,
            type=FiscalBookEntry.TYPE_SERVICE)

    def _has_icms_entry(self):
        return FiscalBookEntry.has_entry_by_payment_group(
            self.get_connection(),
            self,
            type=FiscalBookEntry.TYPE_PRODUCT)

    def _get_average_difference(self):
        sale = self.sale
        if not sale.get_items():
            raise DatabaseInconsistency(
                "Sale orders must have items, which means products or "
                "services or gift certificates")
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
            self.get_connection(), self,
            FiscalBookEntry.TYPE_SERVICE)

    def _create_fiscal_entries(self):
        """A Brazil-specific method
        Create new ICMS and ISS entries in the fiscal book
        for a given sale.

        Important: freight and interest are not part of the base value for
        ICMS. Only product values and surcharge which applies increasing the
        product totals are considered here.

        Note that we are not calculating ICMS or ISS for gift certificates since
        it will be calculated for the products sold when using gift
        certificates as payment methods.
        """
        sale = self.sale
        av_difference = self._get_average_difference()

        if sale.products:
            icms_total = self._get_icms_total(av_difference)
            self.create_icmsipi_book_entry(sale.cfop, sale.coupon_id,
                                           icms_total)

        if sale.services and sale.service_invoice_number:
            iss_total = self._get_iss_total(av_difference)
            self.create_iss_book_entry(sale.cfop,
                                       sale.service_invoice_number,
                                       iss_total)

#     def update_iss_entries(self):
#         """Update iss entries after printing a service invoice"""
#         av_difference = self._get_average_difference()
#         sale = self.sale
#         if not self._has_iss_entry():
#             iss_total = self._get_iss_total(av_difference)
#             self.create_iss_book_entry(sale.cfop,
#                                        sale.service_invoice_number,
#                                        iss_total)
#             return

#         conn = self.get_connection()
#         iss_entry = IssBookEntry.get_entry_by_payment_group(conn, self)
#         if iss_entry.invoice_number == sale.service_invoice_number:
#             return

#         # User just cancelled the old invoice and would like to print a
#         # new one -> reverse old entry and create a new one
#         iss_entry.reverse_entry(iss_entry.invoice_number)

#         # create the new iss entry
#         iss_total = self._get_iss_total(av_difference)
#         self.create_iss_book_entry(sale.cfop,
#                                    sale.service_invoice_number,
#                                    iss_total)


Sale.registerFacet(SaleAdaptToPaymentGroup, IPaymentGroup)


#
# Views
#


class SaleView(SQLObject, BaseSQLView):
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

