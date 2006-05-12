# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005,2006 Async Open Source <http://www.async.com.br>
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
##
""" Sale object and related objects implementation """

from decimal import Decimal
from datetime import datetime

from sqlobject import UnicodeCol, DateTimeCol, ForeignKey, IntCol, SQLObject
from stoqdrivers.constants import TAX_ICMS, TAX_NONE, TAX_SUBSTITUTION
from zope.interface import implements
from kiwi.argcheck import argcheck
from kiwi.datatypes import currency

from stoqlib.lib.validators import get_formatted_price
from stoqlib.lib.defaults import METHOD_GIFT_CERTIFICATE
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.domain.columns import PriceCol, DecimalCol, AutoIncCol
from stoqlib.domain.base import Domain, BaseSQLView
from stoqlib.domain.sellable import AbstractSellableItem
from stoqlib.domain.payment.base import AbstractPaymentGroup
from stoqlib.domain.product import ProductSellableItem
from stoqlib.domain.service import ServiceSellableItem
from stoqlib.domain.renegotiation import RenegotiationData
from stoqlib.domain.giftcertificate import (GiftCertificateItem,
                                            GiftCertificate)
from stoqlib.exceptions import SellError, DatabaseInconsistency
from stoqlib.domain.interfaces import (IContainer, IClient,
                                       IPaymentGroup, ISellable,
                                       IRenegotiationSaleReturnMoney,
                                       IRenegotiationGiftCertificate,
                                       IRenegotiationOutstandingValue,
                                       IIndividual, ICompany)

_ = stoqlib_gettext

#
# Base Domain Classes
#

class Sale(Domain):
    """Sale object implementation.
    Nested imports are needed here because domain/sallable.py imports the
    current one.

    B{Important attributes}:
        - I{order_number}: an optional identifier for this sale defined by
                           the store.
        - I{open_date}: The day when we started this sale.
        - I{close_date}: The day when we confirmed this sale.
        - I{notes}: Some optional additional information related to this
                    sale.
        - I{till}: The Till operation where this sale lives. Note that every
                   sale and payment generated are always in a till operation
                   which defines a financial history of a store.
        - I{client_role}: This field indicates what client role is tied with
                          the sale order. This is important since a client
                          can have two roles associated, i.e, Individual and/or
                          Company. This is useful when printing the sale
                          invoice.
    """

    implements(IContainer)

    (STATUS_OPENED,
     STATUS_CONFIRMED,
     STATUS_CLOSED,
     STATUS_CANCELLED,
     STATUS_ORDER) = range(5)

    (CLIENT_INDIVIDUAL,
     CLIENT_COMPANY) = range(2)

    statuses = {STATUS_OPENED:      _(u"Opened"),
                STATUS_CONFIRMED:   _(u"Confirmed"),
                STATUS_CLOSED:      _(u"Closed"),
                STATUS_CANCELLED:   _(u"Cancelled"),
                STATUS_ORDER:       _(u"Order")}

    coupon_id = IntCol()
    order_number = AutoIncCol('stoqlib_sale_ordernumber_seq')
    open_date = DateTimeCol(default=datetime.now)
    close_date = DateTimeCol(default=None)
    confirm_date = DateTimeCol(default=None)
    cancel_date = DateTimeCol(default=None)
    status = IntCol(default=STATUS_OPENED)
    discount_value = PriceCol(default=0)
    charge_value = PriceCol(default=0)
    notes = UnicodeCol(default='')
    client_role = IntCol(default=None)

    client = ForeignKey('PersonAdaptToClient', default=None)
    cfop = ForeignKey("CfopData")
    till = ForeignKey('Till')
    salesperson = ForeignKey('PersonAdaptToSalesPerson')

    #
    # SQLObject hooks
    #

    def _create(self, id, **kw):
        # Sales objects must be set as valid explicitly
        kw['_is_valid_model'] = False
        Domain._create(self, id, **kw)

    #
    # IContainer methods
    #

    def add_item(self, item):
        raise NotImplementedError("You should call add_selabble_item "
                                  "SellableItem method instead.")

    def get_items(self):
        conn = self.get_connection()
        return AbstractSellableItem.selectBy(connection=conn, saleID=self.id)

    def remove_item(self, item):
        if not isinstance(item, AbstractSellableItem):
            raise TypeError("Item should be of type AbstractSellableItem "
                            "got %s instead" % item)
        conn = self.get_connection()
        table = type(item)
        table.delete(item.id, connection=conn)

    #
    # Classmethods
    #

    @classmethod
    def get_available_sales(cls, conn, till):
        """Returns a list of all available sales for a given
        till operation

        @param conn: a Transaction sqlobject instance
        @param till: a Till instance
        """
        query = cls.q.tillID == till.id
        return cls.select(query, connection=conn)

    @classmethod
    def get_status_name(cls, status):
        if not status in cls.statuses:
            raise DatabaseInconsistency("Invalid status %d" % status)
        return cls.statuses[status]

    #
    # Sale methods
    #

    def update_client(self, person):
        # Do not change the name of this method to set_client: this is a
        # callback in SQLObject
        conn = self.get_connection()
        client = IClient(person, connection=conn)
        if not client:
            raise TypeError("%s cannot be adapted to IClient." % person)
        self.client = client

    def reset_discount_and_charge(self):
        self.discount_value = self.charge_value = currency(0)

    def _get_percentage_value(self, percentage):
        if not percentage:
            return currency(0)
        subtotal = self.get_sale_subtotal()
        percentage = Decimal(str(percentage))
        perc_value = subtotal * (percentage / Decimal('100.0'))
        return currency(perc_value)

    def _set_discount_by_percentage(self, value):
        """Sets a discount by percentage.
        Note that percentage must be added as an absolute value not as a
        factor like 1.05 = 5 % of charge
        The correct form is 'percentage = 3' for a discount of 3 %"""
        self.discount_value = self._get_percentage_value(value)

    def _get_discount_by_percentage(self):
        discount_value = self.discount_value
        if not discount_value:
            return Decimal('0.0')
        subtotal = self.get_sale_subtotal()
        assert subtotal > 0, ('the sale subtotal should not be zero '
                              'at this point')
        total = subtotal - discount_value
        percentage = (1 - total / subtotal) * 100
        return percentage

    discount_percentage = property(_get_discount_by_percentage,
                                   _set_discount_by_percentage)

    def _set_charge_by_percentage(self, value):
        """Sets a charge by percentage.
        Note that charge must be added as an absolute value not as a
        factor like 0.97 = 3 % of discount.
        The correct form is 'percentage = 3' for a charge of 3 %"""
        self.charge_value = self._get_percentage_value(value)

    def _get_charge_by_percentage(self):
        charge_value = self.charge_value
        if not charge_value:
            return Decimal('0.0')
        subtotal = self.get_sale_subtotal()
        assert subtotal > 0, ('the sale subtotal should not be zero '
                              'at this point')
        total = subtotal + charge_value
        percentage = ((total / subtotal) - 1) * 100
        return percentage

    charge_percentage = property(_get_charge_by_percentage,
                                 _set_charge_by_percentage)

    def update_items(self):
        conn = self.get_connection()
        branch = self.get_till_branch()
        for item in self.get_items():
            if isinstance(item, ProductSellableItem):
                # TODO add support for ordering products, bug #2469
                item.sell(branch)
                continue
            item.sell()

    def check_close(self):
        conn = self.get_connection()
        group = IPaymentGroup(self, connection=conn)
        if not group.check_close():
            return
        self.close_date = datetime.now()

    def validate(self):
        if not self.get_items().count():
            raise SellError('The sale must have sellable items')
        if self.client and not self.client.is_active:
            raise SellError('Unable to make sales for clients with status '
                            '%s' % self.client.get_status_string())
        if not self.status == self.STATUS_OPENED:
            raise SellError('The sale must have STATUS_OPENED for this '
                            'operation, got status %s instead'
                            % self.get_status_name(self.status))
        conn = self.get_connection()
        group = IPaymentGroup(self, connection=conn)
        if not group:
            raise ValueError("Sale %s doesn't have an IPaymentGroup "
                             "facet at this point" % self)
        if not self.get_valid():
            self.set_valid()

    def confirm_sale(self):
        self.validate()
        conn = self.get_connection()
        self.update_items()
        group = IPaymentGroup(self, connection=conn)
        group.confirm()
        self.status = self.STATUS_CONFIRMED
        self.confirm_date = datetime.now()
        self.check_close()


    #
    # Accessors
    #

    def get_order_number_str(self):
        return u'%05d' % self.order_number

    def get_salesperson_name(self):
        return self.salesperson.get_adapted().name

    def get_client_name(self):
        if not self.client:
            return _(u'Not Specified')
        return self.client.get_name()

    # Warning: "get_client_role" would be a Kiwi accessor here and this is not
    # what we want.
    def get_sale_client_role(self):
        if not self.client:
            return None
        conn = self.get_connection()
        person = self.client.get_adapted()
        if self.client_role is None:
            raise DatabaseInconsistency("The sale %r have a client but no "
                                        "client_role defined." % self)
        elif self.client_role == Sale.CLIENT_INDIVIDUAL:
            individual = IIndividual(person, connection=conn)
            if not individual:
                raise DatabaseInconsistency("The client_role for sale %r says "
                                            "that the client is an individual,"
                                            " but it doesn't have an Individual"
                                            " facet" % self)
            return individual
        elif self.client_role == Sale.CLIENT_COMPANY:
            company = ICompany(person, connection=conn)
            if not company:
                raise DatabaseInconsistency("The client_role for sale %r says "
                                            "that the client is a company but "
                                            "it doesn't have a Company facet"
                                            % self)
            return company
        else:
            raise DatabaseInconsistency("Invalid client_role for sale %r, "
                                        "got %r" % (self, self.client_role))

    def get_till_branch(self):
        return self.till.branch

    def get_sale_subtotal(self):
        subtotal = sum([item.get_total() for item in self.get_items()],
                       currency(0))
        return currency(subtotal)

    def get_total_sale_amount(self):
        """Return the total value paid by the client. This can be
        calculated by:.
        Sale total = Sum(product and service prices) + charge +
                     interest - discount"""
        charge_value = self.charge_value or Decimal('0.0')
        discount_value = self.discount_value or Decimal('0.0')
        subtotal = self.get_sale_subtotal()
        total_amount = subtotal + charge_value - discount_value
        return currency(total_amount)

    def get_total_amount_as_string(self):
        return get_formatted_price(self.get_total_sale_amount())

    def get_total_interest(self):
        raise NotImplementedError

    def get_services(self):
        return [item for item in self.get_items()
                    if isinstance(item, ServiceSellableItem)]

    def get_products(self):
        return [item for item in self.get_items()
                    if isinstance(item, ProductSellableItem)]

    def get_gift_certificates(self):
        """Returns a list of gift certificates tied to the current sale"""
        return [item for item in self.get_items()
                    if isinstance(item, GiftCertificateItem)]

    def get_items_total_quantity(self):
        return sum([item.quantity for item in self.get_items()],
                   Decimal("0.0"))

    def get_items_total_value(self):
        total = sum([item.get_total() for item in self.get_items()],
                   currency(0))
        return currency(total)



#
# Adapters
#


class SaleAdaptToPaymentGroup(AbstractPaymentGroup):

    (RENEGOTIATION_GIFT_CERTIFICATE,
     RENEGOTIATION_RETURN,
     RENEGOTIATION_OUTSTANDING) = range(3)

    ifaces = {RENEGOTIATION_GIFT_CERTIFICATE: IRenegotiationGiftCertificate,
              RENEGOTIATION_RETURN: IRenegotiationSaleReturnMoney,
              RENEGOTIATION_OUTSTANDING:IRenegotiationOutstandingValue}

    renegotiation_type = IntCol(default=None)

    #
    # IPaymentGroup implementation
    #

    def get_thirdparty(self):
        sale = self.get_adapted()
        client = sale.client
        return client and client.get_adapted() or None

    def set_thirdparty(self):
        raise NotImplementedError

    def get_group_description(self):
        sale = self.get_adapted()
        return _(u'sale %s') % sale.order_number

    #
    # Auxiliar methods
    #


    def _get_stored_renegotiation(self, reason=None):
        if self.renegotiation_data is not None:
            return ValueError('You already have a renegotiation data '
                              'defined')
        sale = self.get_adapted()
        responsible = sale.salesperson.get_adapted()
        conn = self.get_connection()
        reason = reason or _('Overpaid value of sale using gift certificates')
        reneg_data = RenegotiationData(connection=conn,
                                       responsible=responsible,
                                       reason=reason)
        self.renegotiation_data = reneg_data
        return reneg_data

    @argcheck(Decimal)
    def create_renegotiation_return_data(self, overpaid_value):
        renegotiation = self._get_stored_renegotiation()
        reneg_type = self.RENEGOTIATION_RETURN
        self.renegotiation_type = reneg_type
        conn = self.get_connection()
        renegotiation.addFacet(IRenegotiationSaleReturnMoney,
                               connection=conn,
                               payment_group=self,
                               overpaid_value=overpaid_value)

    @argcheck(unicode, Decimal)
    def create_renegotiation_giftcertificate_data(self, certificate_number,
                                                  overpaid_value):
        if not certificate_number:
            raise ValueError('You must provide a valid certificate number')
        table = type(self)
        reneg_type = table.RENEGOTIATION_GIFT_CERTIFICATE
        self.renegotiation_type = reneg_type
        conn = self.get_connection()
        number = certificate_number
        renegotiation = self._get_stored_renegotiation()
        renegotiation.addFacet(IRenegotiationGiftCertificate,
                               connection=conn,
                               new_gift_certificate_number=number,
                               overpaid_value=overpaid_value)

    @argcheck(Decimal, int)
    def create_renegotiation_outstanding_data(self, outstanding_value,
                                              preview_payment_method):
        reneg_type = self.RENEGOTIATION_OUTSTANDING
        self.renegotiation_type = reneg_type
        conn = self.get_connection()
        reason = _('Outstanding value of sale using gift certificates')
        renegotiation = self._get_stored_renegotiation(reason)
        renegotiation.addFacet(IRenegotiationOutstandingValue,
                               connection=conn,
                               preview_payment_method=preview_payment_method,
                               payment_method=preview_payment_method,
                               outstanding_value=outstanding_value)

    def get_gift_certificates(self):
        conn = self.get_connection()
        table = GiftCertificate.getAdapterClass(ISellable)
        return table.selectBy(groupID=self.id, connection=conn)

    def confirm_gift_certificates(self):
        """Update gift certificates of the current sale, setting their
        status properly.
        """
        certificates = self.get_gift_certificates()
        for item in certificates:
            item.apply_as_payment_method()

    def get_renegotiation_adapter(self):
        if self.renegotiation_type is None:
            raise ValueError('You should have a renegotiation_type defined '
                             'at this point')
        if self.renegotiation_type not in self.ifaces.keys():
            raise ValueError('Invalid renegotiation_type, got %d'
                             % self.renegotiation_type)
        iface = self.ifaces[self.renegotiation_type]
        conn = self.get_connection()
        return iface(self.renegotiation_data, connection=conn)

    def setup_inpayments(self):
        reneg_type = self.RENEGOTIATION_OUTSTANDING
        if (self.default_method == METHOD_GIFT_CERTIFICATE
            and not self.renegotiation_type == reneg_type):
            return
        AbstractPaymentGroup.setup_inpayments(self)

    def get_pm_commission_total(self):
        """Return the payment method commission total. Usually credit
        card payment method is the most common method which uses
        commission
        """
        return currency(0)

    def get_total_received(self):
        """Return the total amount paid by the client (sale total)
        deducted of payment method commissions"""
        sale = self.get_adapted()
        return sale.get_total_sale_amount() - self.get_pm_commission_total()

    @argcheck(Decimal)
    def _get_icms_total(self, av_difference):
        """A Brazil-specific method
        Calculates the icms total value

        @param av_difference: the average difference for the sale items.
                              it means the average discount or surcharge
                              applied over all sale items
        """
        icms_total = Decimal("0.0")
        conn = self.get_connection()
        icms_tax = sysparam(conn).ICMS_TAX / Decimal("100.0")
        sale = self.get_adapted()
        for item in sale.get_products():
            price = item.price + av_difference
            sellable = item.sellable
            if (sellable.tax_type == TAX_SUBSTITUTION or
                sellable.tax_type == TAX_NONE):
                continue
            elif sellable.tax_type == TAX_ICMS:
                icms_total += icms_tax * (price * item.quantity)
            else:
                raise ValueError("Invalid tax type for product %s. "
                                 "Got %d" % (sellable, sellable.tax_type))
        return icms_total

    @argcheck(Decimal)
    def _get_iss_total(self, av_difference):
        """A Brazil-specific method
        Calculates the iss total value

        @param av_difference: the average difference for the sale items.
                              it means the average discount or surcharge
                              applied over all sale items
        """
        iss_total = Decimal('0.0')
        conn = self.get_connection()
        iss_tax = sysparam(conn).ISS_TAX / Decimal("100.0")
        sale = self.get_adapted()
        for item in sale.get_services():
            price = item.price + av_difference
            iss_total += iss_tax * (price * item.quantity)
        return iss_total

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
        sale = self.get_adapted()
        total = (sale.get_total_sale_amount() -
                 self.get_pm_commission_total())
        total_quantity = sale.get_items_total_quantity()
        if not total_quantity:
            raise DatabaseInconsistency("Sale total quantity should never "
                                        "be zero")
        # If there is a discount or a surcharge applied in the whole total
        # sale amount, we must share it between all the item values
        # otherwise the icms and iss won't be calculated properly
        subtotal = sale.get_sale_subtotal()
        av_difference = (total - subtotal) / total_quantity

        icms_total = self._get_icms_total(av_difference)
        self.create_icmsipi_book_entry(sale.cfop, sale.coupon_id, icms_total)

        iss_total = self._get_iss_total(av_difference)
        self.create_iss_book_entry(sale.cfop, sale.coupon_id, iss_total)

    def confirm(self):
        """Validate the current payment group, create payments and setup the
        associated gift certificates properly.
        """
        self.setup_inpayments()
        self._create_fiscal_entries()
        if self.default_method == METHOD_GIFT_CERTIFICATE:
            self.confirm_gift_certificates()
        if self.renegotiation_type is None:
            return
        # Here we have the payment method set as gift certificate but there
        # is an outstanding or overpaid values to deal with.
        adapter = self.get_renegotiation_adapter()
        adapter.confirm()

    #
    # AbstractPaymentGroup hooks
    #

    def get_default_payment_method(self):
        if self.renegotiation_data is None:
            return self.default_method
        adapter = self.get_renegotiation_adapter()
        if IRenegotiationOutstandingValue.providedBy(adapter):
            return adapter.payment_method
        else:
            return self.default_method

Sale.registerFacet(SaleAdaptToPaymentGroup, IPaymentGroup)


#
# Views
#


class SaleView(SQLObject, BaseSQLView):
    """Stores general informatios about sales"""
    coupon_id = IntCol()
    order_number = IntCol()
    open_date = DateTimeCol()
    close_date = DateTimeCol()
    confirm_date = DateTimeCol()
    cancel_date = DateTimeCol()
    status = IntCol()
    salesperson_name = UnicodeCol()
    client_name = UnicodeCol()
    client_id = IntCol()
    charge_value = PriceCol()
    discount_value = PriceCol()
    subtotal = PriceCol()
    total = PriceCol()
    total_quantity = DecimalCol()

    def get_client_name(self):
        return self.client_name or u""

    def get_open_date_as_string(self):
        return self.open_date.strftime("%x")

    def get_status_name(self):
        return Sale.get_status_name(self.status)
