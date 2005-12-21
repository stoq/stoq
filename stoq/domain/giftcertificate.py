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
##
"""
stoq/domain/giftcertificate.py:

    Gift Certificate implementation
"""

import gettext

from sqlobject import StringCol, ForeignKey, BoolCol

from stoq.domain.sellable import (AbstractSellable, AbstractSellableItem,
                                  OnSaleInfo)
from stoq.domain.base import Domain
from stoq.domain.interfaces import ISellable


_ = gettext.gettext

#
# Base Domain Classes
#

class FancyGiftCertificate:
    """This class must be used when creating a single gift certificate or a
    range of multiple gift certificates 
    """
    first_number = None
    last_number = None
    gift_certificate_type = None

    def __init__(self, number=None):
        self.number = number


class GiftCertificateType(Domain):
    """A gift certificate item represent a sale item with a special
    property: it can be used as a payment method for another sale.
    """
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
            return _('Active')
        return _('Inactive')

    @classmethod
    def get_active_gift_certificates(cls, conn):
        query = cls.q.is_active == True
        return cls.select(query, connection=conn)


class GiftCertificateItem(AbstractSellableItem):
    """A gift certificate item represent a sale item with a special
    property: it can be used as a payment method for another sale.
    """
    
    
class GiftCertificate(Domain):
    """This is the base class for gift certificates representation. A gift
    certificate is a paper which will be used in the future as a payment 
    method in a certain sale. 
    """
    notes = StringCol(default=None)

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
        self.status = self.STATUS_CLOSED

GiftCertificate.registerFacet(GiftCertificateAdaptToSellable, ISellable)
