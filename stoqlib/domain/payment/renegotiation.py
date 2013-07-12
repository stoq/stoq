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

# pylint: enable=E1101

from kiwi.currency import currency
from storm.references import Reference
from zope.interface import implementer

from stoqlib.database.expr import TransactionTimestamp
from stoqlib.database.properties import (PriceCol, UnicodeCol, IdentifierCol,
                                         IntCol, DateTimeCol, IdCol)
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IContainer
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.lib.dateutils import localnow
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


#
# Base Domain Classes
#

@implementer(IContainer)
class PaymentRenegotiation(Domain):
    """Class for payments renegotiations
    """

    __storm_table__ = 'payment_renegotiation'

    (STATUS_CONFIRMED,
     STATUS_PAID,
     STATUS_RENEGOTIATED) = range(3)

    statuses = {STATUS_CONFIRMED: _(u'Confirmed'),
                STATUS_PAID: _(u'Paid'),
                STATUS_RENEGOTIATED: _(u'Renegotiated')}

    #: A numeric identifier for this object. This value should be used instead of
    #: :obj:`Domain.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IdentifierCol()

    status = IntCol(default=STATUS_CONFIRMED)
    notes = UnicodeCol(default=None)
    open_date = DateTimeCol(default_factory=localnow)
    close_date = DateTimeCol(default=None)
    discount_value = PriceCol(default=0)
    surcharge_value = PriceCol(default=0)
    total = PriceCol(default=0)
    responsible_id = IdCol()
    responsible = Reference(responsible_id, 'LoginUser.id')
    client_id = IdCol(default=None)
    client = Reference(client_id, 'Client.id')
    branch_id = IdCol(default=None)
    branch = Reference(branch_id, 'Branch.id')
    group_id = IdCol()
    group = Reference(group_id, 'PaymentGroup.id')

    #
    # Public API
    #

    def can_set_renegotiated(self):
        """Only sales with status confirmed can be renegotiated.
        :returns: True if the sale can be renegotiated, False otherwise.
        """
        # This should be as simple as:
        # return self.status == Sale.STATUS_CONFIRMED
        # But due to bug 3890 we have to check every payment.
        return any([payment.status == Payment.STATUS_PENDING
                    for payment in self.payments])

    def get_client_name(self):
        if not self.client:
            return u""
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

        self.close_date = TransactionTimestamp()
        self.status = PaymentRenegotiation.STATUS_RENEGOTIATED

    @property
    def payments(self):
        return self.group.get_valid_payments()

    #
    #   IContainer Implementation
    #

    def add_item(self, payment):
        # TODO:
        pass

    def remove_item(self, payment):
        # TODO:
        pass

    def get_items(self):
        return self.store.find(PaymentGroup, renegotiation=self)
