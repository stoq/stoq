# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
## Author(s): Henrique Romano           <henrique@async.com.br>
##            Evandro Vale Miquelito    <evandro@async.com.br>
##            Johan Dahlin              <jdahlin@async.com.br>
##
""" Base classes to manage services informations """


from stoqlib.database.orm import BLOBCol
from stoqlib.database.orm import ForeignKey
from stoqlib.database.orm import AND, INNERJOINOn, LEFTJOINOn
from stoqlib.database.orm import Viewable
from stoqlib.domain.base import Domain
from stoqlib.domain.sellable import (BaseSellableInfo, Sellable,
                                     SellableUnit)
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

#
# Base Domain Classes
#


class Service(Domain):
    """Class responsible to store basic service informations."""

    image = BLOBCol(default='')
    sellable = ForeignKey('Sellable')

    def remove(self):
        """Removes this service from the database."""
        self.delete(self.id, self.get_connection())

    def can_remove(self):
        from stoqlib.domain.sale import SaleItem
        return SaleItem.selectBy(sellable=self.sellable,
                             connection=self.get_connection()).count() == 0


#
# Views
#


class ServiceView(Viewable):
    """Stores information about services
    Available fields are::
        id                 - the id of the asellable table
        barcode            - the sellable barcode
        status             - the sellable status
        cost               - the sellable cost
        price              - the sellable price
        description        - the sellable description
        unit               - the unit in case the sellable is not a product
        service_id         - the id of the service table
    """

    columns = dict(
        id=Sellable.q.id,
        code=Sellable.q.code,
        barcode=Sellable.q.barcode,
        status=Sellable.q.status,
        cost=Sellable.q.cost,
        price=BaseSellableInfo.q.price,
        description=BaseSellableInfo.q.description,
        unit=SellableUnit.q.description,
        service_id=Service.q.id
        )

    joins = [
        INNERJOINOn(None, Service,
                    Service.q.sellableID == Sellable.q.id),
        LEFTJOINOn(None, SellableUnit,
                   Sellable.q.unitID == SellableUnit.q.id),
        ]

    clause = AND(
        BaseSellableInfo.q.id == Sellable.q.base_sellable_infoID,
    )

    def get_unit(self):
        return self.unit or u""

    @property
    def sellable(self):
        return Sellable.get(self.id, connection=self.get_connection())
