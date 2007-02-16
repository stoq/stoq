# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Johan Dahlin <jdahlin@async.com.br>
##

from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.person import Person, PersonAdaptToClient
from stoqlib.domain.sale import Sale, SaleAdaptToPaymentGroup

from sqlobject.sqlbuilder import LEFTJOINOn, INNERJOINOn
from sqlobject.viewable import Viewable

class ReceivableView(Viewable):
    columns = dict(
        id=Payment.q.id,
        identifier=Payment.q.identifier,
        description=Payment.q.description,
        thirdparty_name=Person.q.name,
        due_date=Payment.q.due_date,
        status=Payment.q.status,
        value=Payment.q.value,
        sale_id=Sale.q.id,
        )

    joins = [
        INNERJOINOn(None, SaleAdaptToPaymentGroup,
                    SaleAdaptToPaymentGroup.q.id == Payment.q.groupID),
        INNERJOINOn(None, Sale,
                    Sale.q.id == SaleAdaptToPaymentGroup.q._originalID),
        LEFTJOINOn(None, PersonAdaptToClient,
                    PersonAdaptToClient.q.id == Sale.q.id),
        LEFTJOINOn(None, Person,
                   Person.q.id == PersonAdaptToClient.q._originalID),
        ]

    def get_status_str(self):
        return Payment.statuses[self.status]

    @property
    def sale(self):
        return Sale.get(self.sale_id)

    @property
    def payment(self):
        return Payment.get(self.id)
