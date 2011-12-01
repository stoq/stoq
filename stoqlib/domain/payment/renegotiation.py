# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Domain classes for renegotiation management """

import datetime
from zope.interface import implements

from kiwi.datatypes import currency

from stoqlib.database.orm import PriceCol, const
from stoqlib.database.orm import ForeignKey, UnicodeCol, IntCol, DateTimeCol
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IContainer
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


#
# Base Domain Classes
#

class PaymentRenegotiation(Domain):
    """Class for payments renegotiations
    """
    implements(IContainer)

    (STATUS_CONFIRMED,
     STATUS_PAID,
     STATUS_RENEGOTIATED) = range(3)

    statuses = {STATUS_CONFIRMED: _(u'Confirmed'),
                STATUS_PAID: _(u'Paid'),
                STATUS_RENEGOTIATED: _(u'Renegotiated')}

    status = IntCol(default=STATUS_CONFIRMED)
    notes = UnicodeCol(default=None)
    open_date = DateTimeCol(default=datetime.datetime.now)
    close_date = DateTimeCol(default=None)
    discount_value = PriceCol(default=0)
    surcharge_value = PriceCol(default=0)
    total = PriceCol(default=0)
    responsible = ForeignKey('PersonAdaptToUser')
    client = ForeignKey('PersonAdaptToClient', default=None)
    branch = ForeignKey('PersonAdaptToBranch', default=None)
    group = ForeignKey('PaymentGroup')

    #
    # Public API
    #

    def can_set_renegotiated(self):
        """Only sales with status confirmed can be renegotiated.
        @returns: True if the sale can be renegotiated, False otherwise.
        """
        # This should be as simple as:
        # return self.status == Sale.STATUS_CONFIRMED
        # But due to bug 3890 we have to check every payment.
        return any([payment.status == Payment.STATUS_PENDING
                    for payment in self.payments])

    def get_client_name(self):
        return self.client.person.name

    def get_responsible_name(self):
        return self.responsible.person.name

    def get_status_name(self):
        return self.statuses[self.status]

    def get_subtotal(self):
        return currency(self.total + self.discount_value
                        - self.surcharge_value)

    def set_renegotiated(self):
        """Set the sale as renegotiated. The sale payments have been
        renegotiated and the operations will be done in other payment group."""
        assert self.can_set_renegotiated()

        self.close_date = const.NOW()
        self.status = PaymentRenegotiation.STATUS_RENEGOTIATED

    @property
    def payments(self):
        return self.group.get_items()

    #
    #   IContainer Implementation
    #

    def add_item(self, payment):
        #TODO:
        pass

    def remove_item(self, payment):
        #TODO:
        pass

    def get_items(self):
        return PaymentGroup.selectBy(renegotiation=self,
                                     connection=self.get_connection())
