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
## Author(s):   George Y. Kussumoto         <george@async.com.br>
##
""" Base classes to manage production informations """

import datetime
from decimal import Decimal

from zope.interface import implements

from stoqlib.database.orm import (UnicodeCol, ForeignKey, DateTimeCol, IntCol,
                                  DecimalCol)
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IContainer, IDescribable, IStorable
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ProductionOrder(Domain):
    """Production Order object implementation.

    @cvar ORDER_OPENED: The production order is opened, production items might
                        have been added.
    @cvar ORDER_WAITING: The production order is waiting some conditions to
                         start the manufacturing process.
    @cvar ORDER_PRODUCTION: The production order have already started.
    @cvar ORDER_CLOSED: The production have finished.

    @ivar status: the production order status
    @ivar open_date: the date when the production order was created
    @ivar close_date: the date when the production order have been closed
    @ivar description: the production order description
    @ivar responsible: the person responsible for the production order
    """
    implements(IContainer, IDescribable)

    (ORDER_OPENED,
     ORDER_WAITING,
     ORDER_PRODUCING,
     ORDER_CLOSED) = range(4)

    statuses = {ORDER_OPENED:         _(u'Opened'),
                ORDER_WAITING:        _(u'Waiting'),
                ORDER_PRODUCING:      _(u'Producing'),
                ORDER_CLOSED:         _(u'Closed')}

    status = IntCol(default=ORDER_OPENED)
    open_date = DateTimeCol(default=datetime.datetime.now)
    expected_start_date = DateTimeCol(default=None)
    start_date = DateTimeCol(default=None)
    close_date = DateTimeCol(default=None)
    description = UnicodeCol(default='')
    responsible = ForeignKey('PersonAdaptToEmployee', default=None)
    branch = ForeignKey('PersonAdaptToBranch')

    #
    # IContainer implmentation
    #

    def get_items(self):
        return ProductionItem.selectBy(order=self,
                                       connection=self.get_connection())

    def add_item(self, sellable, quantity=Decimal(1)):
        return ProductionItem(order=self, product=sellable.product,
                              quantity=quantity,
                              connection=self.get_connection())

    def remove_item(self, item):
        if item.order is not self:
            raise ValueError('Argument item must have an order attribute '
                             'associated with the current production '
                             'order instance.')
        ProductionItem.delete(item.id, connection=self.get_connection())

    #
    # Public API
    #

    def get_service_items(self):
        """Returns all the services needed by this production.

        @returns: a sequence of L{ProductionService} instances.
        """
        return ProductionService.selectBy(order=self,
                                          connection=self.get_connection())

    def get_material_items(self):
        """Returns all the material needed by this production.

        @returns: a sequence of L{ProductionMaterial} instances.
        """
        return ProductionMaterial.selectBy(order=self,
                                           connection=self.get_connection())

    def start_production(self):
        """Start the production by allocating all the material needed.
        """
        assert self.status in [ProductionOrder.ORDER_OPENED,
                               ProductionOrder.ORDER_WAITING]

        for material in self.get_material_items():
            material.allocate()

        self.start_date = datetime.date.today()
        self.status = ProductionOrder.ORDER_PRODUCING

    def set_production_waiting(self):
        assert self.status == ProductionOrder.ORDER_OPENED

        self.status = ProductionOrder.ORDER_WAITING

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.description


class ProductionItem(Domain):
    """Production Item object implementation.

    @ivar order: The L{ProductionOrder} of this item.
    @ivar product: The product that will be manufactured.
    @ivar quantity: The product's quantity that will be manufactured.
    @ivar produced: The product's quantity that was manufactured.
    @ivar lost: The product's quantity that was lost.
    """
    implements(IDescribable)

    quantity = DecimalCol(default=1)
    produced = DecimalCol(default=0)
    lost = DecimalCol(default=0)
    order = ForeignKey('ProductionOrder')
    product = ForeignKey('Product')

    #
    # IDescribable Implementation
    #

    def get_description(self):
        return self.product.sellable.get_description()

    #
    # Public API
    #

    def get_unit_description(self):
        return self.product.sellable.get_unit_description()

    def get_components(self):
        return self.product.get_components()

    def can_produce(self, quantity):
        """Sets a quantity to be produced. We can set a quantity to be
        produced until we reach the total quantity that will be manufactured
        minus the quantity that was lost.

        @param quantity: the quantity that will be produced.
        """
        return self.produced + quantity - self.lost <= self.quantity

    def produce(self, quantity):
        assert self.can_produce(quantity)

        storable = IStorable(self.product, None)
        assert storable is not None

        storable.increase_stock(quantity, self.order.branch)
        self.produced += quantity

    def set_lost(self, quantity):
        """Sets a quantity that was lost. The maximum quantity that can be
        lost is the total quantity minus the quantity already produced.

        @param quantity: the quantity that was lost.
        """
        if self.lost + quantity > self.quantity - self.produced:
            raise ValueError(
                u'Can not lost more items than the total production quantity.')

        self.lost += quantity


class ProductionMaterial(Domain):
    """Production Material object implementation.

    @ivar order: The L{ProductionOrder} that will consume this material.
    @ivar product: The product that will be consumed.
    @ivar needed: The quantity needed of this material.
    @ivar consumed: The quantity already used of this material.
    @ivar lost: The quantity lost of this material.
    @ivar to_purchase: The quantity to purchase of this material.
    @ivar to_make: The quantity to manufacture of this material.
    """
    implements(IDescribable)

    needed = DecimalCol(default=1)
    allocated = DecimalCol(default=0)
    consumed = DecimalCol(default=0)
    lost = DecimalCol(default=0)
    to_purchase = DecimalCol(default=0)
    to_make = DecimalCol(default=0)
    order = ForeignKey('ProductionOrder')
    product = ForeignKey('Product')

    #
    # Public API
    #

    def allocate(self):
        """Allocates the needed quantity of this material by decreasing the
        stock quantity. If the available quantity is not enough, then it will
        allocate all the stock available.
        """
        stock = self.get_stock_quantity()
        storable = IStorable(self.product, None)
        assert storable is not None

        if stock > self.needed:
            quantity = self.needed
        else:
            quantity = stock

        if quantity > 0:
            self.allocated = quantity
            storable.decrease_stock(quantity, self.order.branch)

    #
    # IDescribable Implementation
    #

    def get_description(self):
        return self.product.sellable.get_description()

    # Accessors

    def get_unit_description(self):
        return self.product.sellable.get_unit_description()

    def get_stock_quantity(self):
        storable = IStorable(self.product, None)
        assert storable is not None
        return storable.get_full_balance(self.order.branch)


class ProductionService(Domain):
    """Production Service object implementation.

    @ivar order: The L{ProductionOrder} of this service.
    @ivar service: The service that will be used by the production.
    @ivar quantity: The service's quantity.
    """
    implements(IDescribable)

    quantity = DecimalCol(default=1)
    order = ForeignKey('ProductionOrder')
    service = ForeignKey('Service')

    #
    # IDescribable Implementation
    #

    def get_description(self):
        return self.service.sellable.get_description()

    # Accessors

    def get_unit_description(self):
        return self.service.sellable.get_unit_description()
