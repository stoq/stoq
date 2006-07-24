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
##
""" Gift Certificate implementation """


from sqlobject import UnicodeCol, ForeignKey, BoolCol, SQLObject, IntCol
from kiwi.python import Settable
from zope.interface import implements

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.domain.columns import PriceCol
from stoqlib.domain.base import Domain, BaseSQLView
from stoqlib.domain.sellable import (AbstractSellable, AbstractSellableItem,
                                     OnSaleInfo)
from stoqlib.domain.interfaces import (ISellable, IDescribable,
                                       IGiftCertificatePM)

_ = stoqlib_gettext

#
# Base Domain Classes
#

class GiftCertificateType(Domain):
    """
    A gift certificate item represents a sale item with a special
    property: it can be used as a payment method for another sale.
    """
    implements(IDescribable)

    is_active = BoolCol(default=True)
    base_sellable_info = ForeignKey('BaseSellableInfo')
    on_sale_info = ForeignKey('OnSaleInfo')

    def _create(self, id, **kw):
        if not 'kw' in kw:
            conn = self.get_connection()
            if not 'on_sale_info' in kw:
                kw['on_sale_info'] = OnSaleInfo(connection=conn)
        Domain._create(self, id, **kw)

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.base_sellable_info.get_description()

    def get_status_string(self):
        if self.is_active:
            return _(u'Active')
        return _(u'Inactive')

    @classmethod
    def get_active_gift_certificates(cls, conn):
        return cls.select(cls.q.is_active == True, connection=conn)


class GiftCertificateItem(AbstractSellableItem):
    """A gift certificate item represent a sale item with a special
    property: it can be used as a payment method for another sale.
    """


class GiftCertificate(Domain):
    """This is the base class for gift certificates representation. A gift
    certificate is a paper which will be used in the future as a payment
    method in a certain sale.
    """

#
# Adapters
#

class GiftCertificateAdaptToSellable(AbstractSellable):
    """A gift certificate can also be used as a sellable that can be sold
    normally through POS application
    """
    sellableitem_table = GiftCertificateItem
    # This is used by the payment group to find the gift certificates
    # used as a payment method
    group = ForeignKey('AbstractPaymentGroup', default=None)

    def apply_as_payment_method(self):
        if self.status != self.STATUS_SOLD:
            raise ValueError('This gift certificate must be sold to '
                             'be used as a payment method.')
        conn = self.get_connection()
        base_method = sysparam(conn).BASE_PAYMENT_METHOD
        adapter = IGiftCertificatePM(base_method, connection=conn)
        payment = adapter.setup_inpayments(self.price, self.group)
        payment.set_to_pay()
        self.status = self.STATUS_CLOSED


GiftCertificate.registerFacet(GiftCertificateAdaptToSellable, ISellable)

#
# General methods
#

def get_volatile_gift_certificate():
    return Settable(number=None, first_number=None, last_number=None,
                    gift_certificate_type=None)


#
# Views
#


class GiftCertificateView(SQLObject, BaseSQLView):
    """Stores general gift certificate informations"""
    code = IntCol()
    barcode = UnicodeCol()
    status = IntCol()
    cost = PriceCol()
    price = PriceCol()
    on_sale_price = PriceCol()
    description = UnicodeCol()
    giftcertificate_id = IntCol()
