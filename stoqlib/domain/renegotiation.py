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
##      Author(s):  Evandro Vale Miquelito      <evandro@async.com.br>
##
""" Domain classes for renegotiation management """

from sqlobject import IntCol, ForeignKey, UnicodeCol
from zope.interface import implements

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.domain.base import Domain, ModelAdapter
from stoqlib.domain.columns import PriceCol
from stoqlib.domain.interfaces import (IRenegotiationGiftCertificate,
                                       ISellable,
                                       IRenegotiationSaleReturnMoney,
                                       IRenegotiationOutstandingValue)
from stoqlib.domain.giftcertificate import GiftCertificate
from stoqlib.lib.parameters import sysparam

_ = stoqlib_gettext


#
# Base Domain Classes
#

class RenegotiationData(Domain):
    responsible = ForeignKey('Person')
    reason = UnicodeCol(default=None)

#
# Adapters
#

class RenegotiationAdaptToGiftCertificate(ModelAdapter):
    """This class is used when paying a sale with gift certificate payment
    method and the total amount of gift certificates is greater them the
    sale total amount. In this case the overpaid value will be paid through
    creating a new gift certificate. This class stores information about
    this new object which will created.
    """

    implements(IRenegotiationGiftCertificate)

    (STATUS_PENDING,
     STATUS_CLOSED) = range(2)

    new_gift_certificate_number = UnicodeCol()
    overpaid_value = PriceCol()
    status = IntCol(default=STATUS_PENDING)
    payment_group = ForeignKey('AbstractPaymentGroup')

    def confirm(self):
        """Confirm the renegotiation and creates the new gift
        certificate
        """
        if self.status != self.STATUS_PENDING:
            raise ValueError('Invalid status for renegotiation data, '
                             'it should be pending at this point.'
                             '\n Got status: %d' % self.status)
        conn = self.get_connection()
        cert_type = sysparam(conn).DEFAULT_GIFT_CERTIFICATE_TYPE
        sellable_info = cert_type.base_sellable_info.clone()
        sellable_info.price = self.overpaid_value
        if not sellable_info:
            raise ValueError('A valid gift certificate type must be '
                             'provided at this point')
        certificate = GiftCertificate(connection=conn)
        cert_number = self.new_gift_certificate_number
        sellable_cert = certificate.addFacet(ISellable, connection=conn,
                                             barcode=cert_number,
                                             base_sellable_info=
                                             sellable_info)
        # The new gift certificate which has been created is actually an
        # item of our sale order
        sale = self.payment_group.get_adapted()
        sellable_cert.add_sellable_item(sale)

        sellable_cert.sell()
        self.status = self.STATUS_CLOSED

RenegotiationData.registerFacet(RenegotiationAdaptToGiftCertificate,
                                IRenegotiationGiftCertificate)


class RenegotiationAdaptToSaleReturnMoney(ModelAdapter):
    """This class is used when paying a sale with gift certificate payment
    method and the total amount of gift certificates is greater them the
    sale total amount. In this case the overpaid value will be paid by
    money. This class stores information about the total amount to be paid
    in money and if the payment was already created or not.
    """

    implements(IRenegotiationSaleReturnMoney)

    (STATUS_PENDING,
     STATUS_CLOSED) = range(2)

    overpaid_value = PriceCol()
    status = IntCol(default=STATUS_PENDING)
    payment_group = ForeignKey('AbstractPaymentGroup')

    def confirm(self):
        """Confirm the renegotiation and create the payment."""
        if self.status != self.STATUS_PENDING:
            raise ValueError('Invalid status for renegotiation data, '
                             'it should be pending at this point.'
                             '\n Got status: %d' % self.status)
        order_number = self.payment_group.get_adapted().order_number
        reason = _(u'1/1 Money returned for gift certificate acquittance on '
                    'sale %04d' % order_number)
        payment = self.payment_group.create_debit(self.overpaid_value,
                                                  reason)
        payment.pay()
        self.status = self.STATUS_CLOSED

RenegotiationData.registerFacet(RenegotiationAdaptToSaleReturnMoney,
                                IRenegotiationSaleReturnMoney)


class RenegotiationAdaptToOutstandingValue(ModelAdapter):
    """When paying by gift certificate it's possible to have an outstanding
    value if the sale total is greater than the sum of the gift
    certificates. In this case the customer must pay the remaining value.
    This adapter stores information about this process.
    """

    implements(IRenegotiationOutstandingValue)

    (STATUS_PENDING,
     STATUS_CLOSED) = range(2)

    outstanding_value = PriceCol()
    status = IntCol(default=STATUS_PENDING)
    preview_payment_method = IntCol()
    payment_method = IntCol(default=None)

    def confirm(self):
        """Confirm the renegotiation and create the payments """
        if self.status != self.STATUS_PENDING:
            raise ValueError('Invalid status for renegotiation data, '
                             'it should be pending at this point.'
                             '\n Got status: %d' % self.status)
        conn = self.get_connection()
        self.status = self.STATUS_CLOSED

RenegotiationData.registerFacet(RenegotiationAdaptToOutstandingValue,
                                IRenegotiationOutstandingValue)
