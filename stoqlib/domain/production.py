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

from stoqlib.database.orm import UnicodeCol, ForeignKey, DateTimeCol, IntCol
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IContainer, IDescribable
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
    close_date = DateTimeCol(default=None)
    description = UnicodeCol(default='')
    responsible = ForeignKey('PersonAdaptToEmployee')
    branch = ForeignKey('PersonAdaptToBranch')

    #
    # IContainer implmentation
    #

    #TODO: when implement ProductionItem.

    def get_items(self):
        return []

    def add_item(self, sellable, quantity=Decimal(1)):
        return

    def remove_item(self, item):
        return

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.description
