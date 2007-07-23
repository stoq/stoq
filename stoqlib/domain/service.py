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


from sqlobject import BLOBCol
from sqlobject.sqlbuilder import INNERJOINOn, LEFTJOINOn
from sqlobject.viewable import Viewable

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.domain.base import Domain
from stoqlib.domain.sellable import (ASellable,
                                     BaseSellableInfo, SellableUnit)
from stoqlib.domain.interfaces import ISellable


_ = stoqlib_gettext

#
# Base Domain Classes
#


class Service(Domain):
    """Class responsible to store basic service informations."""

    image = BLOBCol(default='')


class ServiceAdaptToSellable(ASellable):
    """A service implementation as a sellable facet."""

    _inheritable = False

    def _create(self, id, **kw):
        if 'status' not in kw:
            kw['status'] = ASellable.STATUS_AVAILABLE
        ASellable._create(self, id, **kw)

Service.registerFacet(ServiceAdaptToSellable, ISellable)



#
# Views
#


class ServiceView(Viewable):
    """
    Stores information about services
    Available fields are:
        id                 - the id of the asellable table
        barcode            - the sellable barcode
        status             - the sellable status
        cost               - the sellable cost
        price              - the sellable price
        description        - the sellable description
        unit               - the unit in case the sellable is not a gift
                             certificate
        service_id         - the id of the service table
    """

    columns = dict(
        id=ASellable.q.id,
        barcode=ASellable.q.barcode,
        status=ASellable.q.status,
        cost=ASellable.q.cost,
        price=BaseSellableInfo.q.price,
        description=BaseSellableInfo.q.description,
        unit=SellableUnit.q.description,
        service_id=Service.q.id
        )

    joins = [
        INNERJOINOn(None, ServiceAdaptToSellable,
                    ServiceAdaptToSellable.q._originalID == Service.q.id),
        INNERJOINOn(None, ASellable,
                    ServiceAdaptToSellable.q.id == ASellable.q.id),
        INNERJOINOn(None, BaseSellableInfo,
                    ASellable.q.base_sellable_infoID == BaseSellableInfo.q.id),
        LEFTJOINOn(None, SellableUnit,
                   ASellable.q.unitID == SellableUnit.q.id),
        ]

    def get_unit(self):
        return self.unit or u""
