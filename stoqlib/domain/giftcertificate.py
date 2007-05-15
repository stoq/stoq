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
from zope.interface import implements

from stoqlib.database.columns import PriceCol
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.domain.base import Domain, BaseSQLView
from stoqlib.domain.interfaces import (ISellable, IDescribable, IActive)
from stoqlib.domain.sellable import (ASellable, ASellableItem,
                                     OnSaleInfo)
from stoqlib.exceptions import InvalidStatus

_ = stoqlib_gettext

#
# Base Domain Classes
#

class GiftCertificateType(Domain):
    """ A gift certificate type is like a template for creation of gift
    certificate items which can be sold or used as payment method in a
    sale.
    """
    implements(IDescribable, IActive)

    is_active = BoolCol(default=True)
    base_sellable_info = ForeignKey('BaseSellableInfo')
    on_sale_info = ForeignKey('OnSaleInfo')

    def _create(self, id, **kw):
        if not 'kw' in kw:
            conn = self.get_connection()
            if not 'on_sale_info' in kw:
                kw['on_sale_info'] = OnSaleInfo(connection=conn)
        Domain._create(self, id, **kw)

    def get_status_string(self):
        if self.is_active:
            return _(u'Active')
        return _(u'Inactive')

    @classmethod
    def get_active_gift_certificates(cls, conn):
        return cls.select(cls.q.is_active == True, connection=conn)

    #
    # IActive implementation
    #

    def activate(self):
        self.is_active = True

    def inactivate(self):
        self.is_active = False

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.base_sellable_info.get_description()

    #
    # Accessors
    #

    def _set_price(self, price):
        self.base_sellable_info.price = price

    def _get_price(self):
        return self.base_sellable_info.price

    price = property(_get_price, _set_price)

    def _get_commission(self):
        return self.base_sellable_info.get_commission()

    def _set_commission(self, commission):
        self.base_sellable_info.commission = commission

    commission = property(_get_commission, _set_commission)

    def _set_description(self, description):
        self.base_sellable_info.description = description

    description = property(get_description, _set_description)

    def _set_max_discount(self, value):
        self.base_sellable_info.max_discount = value

    def _get_max_discount(self):
        return self.base_sellable_info.max_discount

    max_discount = property(_get_max_discount, _set_max_discount)


class GiftCertificateItem(ASellableItem):
    """A gift certificate item represent a sale item with a special
    property: it can be used as a payment method for another sale.
    """
    _inheritable = False

class GiftCertificate(Domain):
    """This is the base class for gift certificates representation. A gift
    certificate is a paper which will be used in the future as a payment
    method in a certain sale.
    """

#
# Adapters
#

class GiftCertificateAdaptToSellable(ASellable):
    """A gift certificate can also be used as a sellable that can be sold
    normally through POS application
    """
    sellableitem_table = GiftCertificateItem

    _inheritable = False
    # This is used by the payment group to find the gift certificates
    # used as a payment method
    group = ForeignKey('AbstractPaymentGroup', default=None)

    def _create(self, id, **kw):
        if 'status' not in kw:
            kw['status'] = ASellable.STATUS_AVAILABLE
        ASellable._create(self, id, **kw)

    def apply_as_payment_method(self):
        from stoqlib.domain.payment.methods import GiftCertificatePM
        if self.status != self.STATUS_SOLD:
            raise InvalidStatus('This gift certificate must be sold to be used '
                                'as a payment method.')
        conn = self.get_connection()
        method = GiftCertificatePM.selectOne(connection=conn)
        payment = method.create_inpayment(self.group, self.price)
        payment.get_adapted().set_pending()
        self.status = self.STATUS_CLOSED


GiftCertificate.registerFacet(GiftCertificateAdaptToSellable, ISellable)


#
# Views
#


class GiftCertificateView(SQLObject, BaseSQLView):
    """Stores general gift certificate informations"""
    barcode = UnicodeCol()
    status = IntCol()
    cost = PriceCol()
    price = PriceCol()
    on_sale_price = PriceCol()
    description = UnicodeCol()
    giftcertificate_id = IntCol()
