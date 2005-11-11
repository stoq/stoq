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
##  Author(s):  Evandro Vale Miquelito      <evandro@async.com.br>
##
"""
stoq/domain/purchase.py:
    
    Purchase management
"""

import gettext
from datetime import datetime

from kiwi.argcheck import argcheck
from stoqlib.exceptions import DatabaseInconsistency
from sqlobject import ForeignKey, IntCol, DateTimeCol, FloatCol, StringCol
from zope.interface import implements

from stoq.domain.base import Domain
from stoq.domain.interfaces import IContainer

_ = gettext.gettext


class PurchaseItem(Domain):
    quantity = FloatCol(default=1.0)
    quantity_received = FloatCol(default=0.0)
    base_cost = FloatCol()
    cost = FloatCol()
    sellable = ForeignKey('AbstractSellable')
    order = ForeignKey('PurchaseOrder')

    def _create(self, id, **kw):
        if 'base_cost' in kw:
            raise TypeError('You should not provide a base_cost'
                            'argument since it is set automatically')
        if not 'sellable' in kw:
            raise TypeError('You must provide a sellable argument')
        kw['base_cost'] = kw['sellable'].cost
        Domain._create(self, id, **kw)

    #
    # Accessors
    #

    def get_total(self):
        return self.quantity * self.cost

    #
    # SQLObject callbacks
    #

    def _set_quantity_received(self, value):
        # When adding a new PurchaseItem instance we need this check since 
        # we don't have this attribute before calling this method 
        if hasattr(self, 'quantity_received'):
            total = value + self.quantity_received
            if total > self.quantity:
                raise ValueError('Attribute quantity_received can not be '
                                 'greater than quantity attribute') 
        self._SO_set_quantity_received(value)


class PurchaseOrder(Domain):
    """Purchase and order definition"""

    implements(IContainer)

    (ORDER_CANCELLED,
     ORDER_QUOTING,
     ORDER_PENDING,
     ORDER_CONFIRMED,
     ORDER_CLOSED) = range(5)
        
    statuses = {ORDER_CANCELLED     : _('Cancelled'),
                ORDER_QUOTING       : _('Quoting'),
                ORDER_PENDING       : _('Pending'),
                ORDER_CONFIRMED     : _('Confirmed'),
                ORDER_CLOSED        : _('Closed')}

    (FREIGHT_FOB,
     FREIGHT_CIF) = range(2)

    freight_types = {FREIGHT_FOB    : _('FOB'),
                     FREIGHT_CIF    : _('CIF')}
    
    status = IntCol(default=ORDER_QUOTING)
    # Field order_number must be unique. Waiting for bug 2214
    order_number = IntCol(default=None)
    open_date = DateTimeCol(default=datetime.now())
    quote_deadline = DateTimeCol(default=None)
    expected_receival_date = DateTimeCol(default=None)
    expected_pay_date = DateTimeCol(default=None)
    receival_date = DateTimeCol(default=None)
    confirm_date = DateTimeCol(default=None)
    notes = StringCol(default='')
    salesperson_name = StringCol(default='')
    freight_type = IntCol(default=FREIGHT_FOB)
    freight = FloatCol(default=0.0)
    charge_value = FloatCol(default=0.0)
    discount_value = FloatCol(default=0.0)
    supplier = ForeignKey('PersonAdaptToSupplier')
    branch = ForeignKey('PersonAdaptToBranch')
    transporter = ForeignKey('PersonAdaptToTransporter', default=None)

    #
    # SQLObject hooks
    #

    def _create(self, id, **kw):
        # Purchase objects must be set as valid explicitly
        kw['_is_valid_model'] = False
        Domain._create(self, id, **kw)

    #
    # Auxiliar methods
    #

    def get_purchase_total(self):
        return sum([item.cost for item in self.get_items()])

    def get_received_total(self):
        return sum([item.cost * item.quantity_received 
                        for item in self.get_items()])

    def get_remaining_total(self):
        return self.get_purchase_total() - self.get_received_total()
        
    def get_status_str(self):
        if not self.statuses.has_key(self.status):
            raise DatabaseInconsistency('Got an unexpected status value: '
                                        '%s' % self.status)
        return self.statuses[self.status]

    def validate(self):
        if not self.get_active():
            self.set_valid()

    #
    # IContainer implementation
    #

    def get_items(self):
        return PurchaseItem.selectBy(order=self,
                                     connection=self.get_connection())

    @argcheck(PurchaseItem)
    def add_item(self, item):
        item.order = self
        return item

    @argcheck(PurchaseItem)
    def remove_item(self, item):
        conn = self.get_connection()
        if item.order is not self:
            raise ValueError('Argument item must have an order attribute '
                             'associated with the current purchase instance')
        PurchaseItem.delete(item.id, connection=conn)
