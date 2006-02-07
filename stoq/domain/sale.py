# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##
"""
stoq/domain/sale.py:

    Sale object and related objects implementation.
"""

import gettext
from datetime import datetime

from sqlobject import StringCol, DateTimeCol, ForeignKey, IntCol, FloatCol
from stoqlib.exceptions import SellError, DatabaseInconsistency
from zope.interface import implements
from kiwi.argcheck import argcheck

from stoq.domain.base import Domain
from stoq.domain.sellable import AbstractSellableItem
from stoq.domain.payment.base import AbstractPaymentGroup
from stoq.domain.product import ProductSellableItem
from stoq.domain.service import ServiceSellableItem
from stoq.domain.renegotiation import RenegotiationData
from stoq.domain.giftcertificate import (GiftCertificateItem,
                                         GiftCertificate)
from stoq.domain.interfaces import (IContainer, IClient, IStorable,
                                    IPaymentGroup, ISellable,
                                    IRenegotiationSaleReturnMoney,
                                    IRenegotiationGiftCertificate,
                                    IRenegotiationOutstandingValue)


_ = gettext.gettext


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
    """

    implements(IContainer)

    (STATUS_OPENED,
     STATUS_CONFIRMED,
     STATUS_CLOSED,
     STATUS_CANCELLED,
     STATUS_REVIEWING) = range(5)

    statuses = {STATUS_OPENED:          _("Opened"),
                STATUS_CONFIRMED:       _("Confirmed"),
                STATUS_CLOSED:          _("Closed"),
                STATUS_CANCELLED:       _("Cancelled"),
                STATUS_REVIEWING:       _("Reviewing")}

    coupon_id = IntCol(default=None)
    order_number = StringCol(default='')
    open_date = DateTimeCol(default=datetime.now)
    close_date = DateTimeCol(default=None)
    status = IntCol(default=STATUS_OPENED)
    discount_value = FloatCol(default=0.0)
    charge_value = FloatCol(default=0.0)
    notes = StringCol(default='')

    client = ForeignKey('PersonAdaptToClient', default=None)
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
    # Auxiliar methods
    #

    def get_client_name(self):
        if not self.client:
            return _('Anonymous')
        return self.client.get_name()

    def get_status_name(self):
        if not self.status in self.statuses:
            raise DatabaseInconsistency("Invalid status for sale %s: %d"
                                        % (self.order_number, self.status))
        return self.statuses[self.status]

    def update_client(self, person):
        # Do not change the name of this method to set_client: this is a
        # callback in SQLObject
        conn = self.get_connection()
        client = IClient(person, connection=conn)
        if not client:
            raise TypeError("%s cannot be adapted to IClient." % person)
        self.client = client

    def reset_discount_and_charge(self):
        self.discount_value = self.charge_value = 0.0

    def _get_percentage_value(self, percentage):
        if not percentage:
            return 0.0
        subtotal = self.get_sale_subtotal()
        return subtotal * (percentage/100.0)

    def _set_discount_by_percentage(self, value):
        """Sets a discount by percentage.
        Note that percentage must be added as an absolute value not as a
        factor like 1.05 = 5 % of charge
        The correct form is 'percentage = 3' for a discount of 3 %"""
        self.discount_value = self._get_percentage_value(value)

    def _get_discount_by_percentage(self):
        discount_value = self.discount_value
        if not discount_value:
            return 0.0
        subtotal = self.get_sale_subtotal()
        assert subtotal > 0, ('the sale subtotal should not be zero '
                              'at this point')
        total = subtotal - discount_value
        percentage = (1 - total / float(subtotal)) * 100
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
            return 0.0
        subtotal = self.get_sale_subtotal()
        assert subtotal > 0, ('the sale subtotal should not be zero '
                              'at this point')
        total = subtotal + charge_value
        percentage = ((total / float(subtotal)) - 1) * 100
        return percentage

    charge_percentage = property(_get_charge_by_percentage,
                                 _set_charge_by_percentage)

    def get_till_branch(self):
        return self.till.branch

    def get_sale_subtotal(self):
        return sum([item.get_total() for item in self.get_items()], 0.0)

    def get_total_sale_amount(self):
        """Return the total value paid by the client. This can be
        calculated by:.
        Sale total = Sum(product and service prices) + charge +
                     interest - discount"""
        charge_value = self.charge_value or 0.0
        discount_value = self.discount_value or 0.0
        return self.get_sale_subtotal() + charge_value - discount_value

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
        return sum([item.quantity for item in self.get_items()], 0.0)

    def get_items_total_value(self):
        return sum([item.get_total() for item in self.get_items()], 0.0)

    def update_stocks(self):
        conn = self.get_connection()
        branch = self.get_till_branch()
        for product in self.get_products():
            storable = IStorable(product.sellable.get_adapted(),
                                 connection=conn)
            storable.decrease_stock(product.quantity, branch)

    def validate(self):
        if not self.get_items().count():
            raise SellError('The sale must have sellable items')
        if self.client and not self.client.is_active:
            raise SellError('Unable to make sales for clients with status '
                            '%s' % self.client.get_status_string())
        if not self.status == self.STATUS_OPENED:
            raise SellError('The sale must have STATUS_OPENED for this '
                            'operation, got status %s instead'
                            % self.get_status_name())
        conn = self.get_connection()
        group = IPaymentGroup(self, connection=conn)
        if not group:
            raise ValueError("Sale %s doesn't have an IPaymentGroup "
                             "facet at this point" % self)
        if not self.get_valid():
            self.set_valid()

    def update_gift_certificates(self):
        """Update the status of all gift certificates as sold"""
        for item in self.get_gift_certificates():
            item.sellable.sell()

    def confirm_sale(self):
        self.validate()
        conn = self.get_connection()
        self.update_stocks()
        group = IPaymentGroup(self, connection=conn)
        group.confirm()
        self.update_gift_certificates()
        self.status = self.STATUS_CONFIRMED
        self.close_date = datetime.now()

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
        return _('sale %s') % sale.order_number

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

    @argcheck(float)
    def create_renegotiation_return_data(self, overpaid_value):
        renegotiation = self._get_stored_renegotiation()
        reneg_type = self.RENEGOTIATION_RETURN
        self.renegotiation_type = reneg_type
        conn = self.get_connection()
        renegotiation.addFacet(IRenegotiationSaleReturnMoney,
                               connection=conn,
                               payment_group=self,
                               overpaid_value=overpaid_value)

    @argcheck(str, float)
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

    @argcheck(float, int)
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
        if (self.default_method == self.METHOD_GIFT_CERTIFICATE
            and not self.renegotiation_type == reneg_type):
            return
        AbstractPaymentGroup.setup_inpayments(self)

    def get_pm_commission_total(self):
        """Return the payment method commission total. Usually credit
        card payment method is the most common method which uses
        commission
        """
        return 0.0

    def get_total_received(self):
        """Return the total amount paid by the client (sale total)
        deducted of payment method commissions"""
        sale = self.get_adapted()
        return sale.get_total_sale_amount() - self.get_pm_commission_total()

    def confirm(self):
        """Validate the current payment group, create payments and setup the
        associated gift certificates properly.
        """
        self.setup_inpayments()
        if (self.default_method ==
            AbstractPaymentGroup.METHOD_GIFT_CERTIFICATE):
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
