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
##              Fabio Morbec <fabio@async.com.br>
##

from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.person import Person, PersonAdaptToSupplier
from stoqlib.domain.purchase import PurchaseOrder, PurchaseOrderAdaptToPaymentGroup

from sqlobject.sqlbuilder import LEFTJOINOn, INNERJOINOn
from sqlobject.viewable import Viewable

class PayableView(Viewable):
    columns = dict(
        id=Payment.q.id,
        identifier=Payment.q.identifier,
        description=Payment.q.description,
        supplier_name=Person.q.name,
        due_date=Payment.q.due_date,
        status=Payment.q.status,
        value=Payment.q.value,
        purchase_id=PurchaseOrder.q.id,
        )

    joins = [
        INNERJOINOn(None, PurchaseOrderAdaptToPaymentGroup,
                    PurchaseOrderAdaptToPaymentGroup.q.id == Payment.q.groupID),
        INNERJOINOn(None, PurchaseOrder,
                    PurchaseOrder.q.id == PurchaseOrderAdaptToPaymentGroup.q._originalID),
        LEFTJOINOn(None, PersonAdaptToSupplier,
                    PersonAdaptToSupplier.q.id == PurchaseOrder.q.supplierID),
        LEFTJOINOn(None, Person,
                   Person.q.id == PersonAdaptToSupplier.q._originalID),
        ]

    def get_status_str(self):
        return Payment.statuses[self.status]

    @property
    def purchase(self):
        return PurchaseOrder.get(self.purchase_id)
