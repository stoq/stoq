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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Base classes to manage services informations """

# pylint: enable=E1101

from storm.expr import Join, LeftJoin
from storm.references import Reference
from zope.interface import implementer

from stoqlib.database.viewable import Viewable
from stoqlib.domain.base import Domain
from stoqlib.domain.events import (ServiceCreateEvent, ServiceEditEvent,
                                   ServiceRemoveEvent)
from stoqlib.domain.interfaces import IDescribable
from stoqlib.domain.sellable import (Sellable,
                                     SellableUnit, SellableCategory)
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

#
# Base Domain Classes
#


@implementer(IDescribable)
class Service(Domain):
    """Class responsible to store basic service informations."""
    __storm_table__ = 'service'

    #: The |sellable| for this service
    sellable = Reference('id', 'Sellable.id')

    def __init__(self, **kwargs):
        assert 'sellable' in kwargs
        kwargs['id'] = kwargs['sellable'].id

        super(Service, self).__init__(**kwargs)

    def remove(self):
        """Removes this service from the database."""
        self.store.remove(self)

    def close(self):
        # We don't have to do anything special when closing a service.
        pass

    #
    # Sellable helpers
    #

    def can_remove(self):
        if sysparam.compare_object('DELIVERY_SERVICE', self):
            # The delivery item cannot be deleted as it's important
            # for creating deliveries.
            return False

        return super(Service, self).can_remove()

    def can_close(self):
        # The delivery item cannot be closed as it will be
        # used for deliveries.
        return not sysparam.compare_object('DELIVERY_SERVICE', self)

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.sellable.get_description()

    #
    # Domain hooks
    #

    def on_create(self):
        ServiceCreateEvent.emit(self)

    def on_delete(self):
        ServiceRemoveEvent.emit(self)

    def on_update(self):
        store = self.store
        emitted_store_list = getattr(self, u'_emitted_store_list', set())

        # Since other classes can propagate this event (like Sellable),
        # emit the event only once for each store.
        if not store in emitted_store_list:
            ServiceEditEvent.emit(self)
            emitted_store_list.add(store)

        self._emitted_store_list = emitted_store_list


#
# Views
#


class ServiceView(Viewable):
    """Stores information about services

    :attribute id: the id of the asellable table
    :attribute barcode: the sellable barcode
    :attribute status:  the sellable status
    :attribute cost: the sellable cost
    :attribute price: the sellable price
    :attribute description: the sellable description
    :attribute unit: the unit in case the sellable is not a product
    :attribute service_id: the id of the service table
    """

    sellable = Sellable

    id = Sellable.id
    code = Sellable.code
    barcode = Sellable.barcode
    status = Sellable.status
    cost = Sellable.cost
    price = Sellable.base_price
    description = Sellable.description
    category_description = SellableCategory.description
    unit = SellableUnit.description
    service_id = Service.id

    tables = [
        Sellable,
        Join(Service, Service.id == Sellable.id),
        LeftJoin(SellableUnit, Sellable.unit_id == SellableUnit.id),
        LeftJoin(SellableCategory, SellableCategory.id == Sellable.category_id),
    ]

    def get_unit(self):
        return self.unit or u""
