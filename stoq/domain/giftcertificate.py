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

import datetime

from sqlobject import StringCol, FloatCol, ForeignKey, DateCol, IntCol
from sqlobject.sqlbuilder import AND
from stoqlib.exceptions import DatabaseInconsistency

from stoq.domain.sellable import AbstractSellable, AbstractSellableItem
from stoq.domain.base import Domain
from stoq.lib.runtime import get_connection
from stoq.lib.validators import compare_float_numbers



#
# Base Domain Classes
#


class GiftCertificateItem(AbstractSellableItem):
    """A gift certificate item represent a sale item with a special
    property: it can be used as a payment method for another sale.
    """
    
    (STATUS_PREVIEW,
     STATUS_AVAILABLE,
     STATUS_SOLD) = range(3)

    # this field should be unique, waiting for bug 2214
    certificate_number = IntCol(default=None)
    amount_paid = FloatCol(default=0.0)
    status = IntCol(default=STATUS_PREVIEW)
    expire_date = DateCol(default=None)
    owner = ForeignKey('PersonAdaptToClient')

    def _add_gift_certificate(self, status=STATUS_AVAILABLE):
        price = self.price - self.amount_paid
        conn = self.get_connection()
        kwargs = dict(owner=self.owner, amount_paid=0.0, price=price,
                      expire_date=self.expire_date, sellable=self.sellable,
                      sale=self.sale, quantity=self.quantity,
                      status=status, connection=conn)
        GiftCertificateItem(**kwargs)

    def sell(self):
        if self.amount_paid > self.price:
            raise DatabaseInconsistency('The amount_paid attribute can not '
                                        'be greater than the price attribute')
        self.status = self.STATUS_SOLD
        if self.price > self.amount_paid:
            self._add_gift_certificate()
        
    def get_available_amount(self):
        return self.price - self.amount_paid

    def confirm(self):
        if self.status != self.STATUS_PREVIEW:
            raise ValueError('Invalid status for confirm operation')
        self.status = self.STATUS_AVAILABLE

    def _set_certificate_number(self, value):
        conn = get_connection()
        query = GiftCertificateItem.q.certificate_number == value
        # FIXME We should raise a proper stoqlib exception here if we find
        # an existing GiftCertificate. Waiting for kiwi support 
        if not GiftCertificateItem.select(query, connection=conn).count():
            self._SO_set_certificate_number(value)


class GiftCertificate(Domain):
    """This is the base class for gift certificates representation. A gift
    certificate is a paper which will be used in the future as a payment 
    method in a certain sale. 
    """
    notes = StringCol(default=None)


class GiftCertificateAdaptToSellable(AbstractSellable):
    """A gift certificate can also be used as a sellable that can be sold
    normally through POS application
    """
    sellableitem_table = GiftCertificateItem

GiftCertificate.registerFacet(GiftCertificateAdaptToSellable)


#
# Auxiliar functions
#


def _get_gift_certificates_query(client, status):
    """Returns a base query for gift certificates table"""
    q1 = GiftCertificateItem.q.ownerID == client.id
    q2 = GiftCertificateItem.q.status == status
    return AND(q1, q2)

def get_gift_certificates_by_client(conn, client):
    """Returns available gift certificates for a certain client"""
    status = GiftCertificateItem.STATUS_AVAILABLE
    query = _get_gift_certificates_query(client, status)
    certificates = GiftCertificateItem.select(query, connection=conn)
    filtered = []
    today = datetime.date.today()
    for certificate in certificates:
        if (not certificate.expire_date 
            or certificate.expire_date <= today):
            filtered.append(certificate)
    return filtered

def get_client_gift_certificates_total(conn, client):
    """Returns the total amount of gift certificates for a certain client"""
    certificates = get_gift_certificates_by_client(conn, client)
    return sum([c.get_available_amount() for c in certificates], 0.0)
