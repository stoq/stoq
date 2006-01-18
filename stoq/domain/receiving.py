# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
stoq/domain/receiving.py:
    
    Receiving management
"""

import datetime

from sqlobject import ForeignKey, IntCol, DateTimeCol, FloatCol, StringCol
from zope.interface import implements
from kiwi.argcheck import argcheck

from stoq.domain.base import Domain
from stoq.domain.interfaces import IContainer
from stoq.domain.purchase import PurchaseOrder


class ReceivingOrderItem(Domain):
    """This class stores information of the purchased items.
    
    B{Importante attributes}
        - I{quantity_received}: the total quantity received for a certain
          product
        - I{cost}: the cost for each product received

    """
    quantity_received = FloatCol()
    cost = FloatCol()
    sellable = ForeignKey('AbstractSellable')
    receiving_order = ForeignKey('ReceivingOrder')

    #
    # Accessors
    #

    def get_total(self):
        return self.quantity_received * self.cost


class ReceivingOrder(Domain):
    """Receiving order definition."""

    implements(IContainer)

    (STATUS_PENDING,
     STATUS_CLOSED) = range(2)
        
    status = IntCol(default=STATUS_PENDING)
    receival_date = DateTimeCol(default=datetime.datetime.now)
    confirm_date = DateTimeCol(default=None)
    invoice_number = StringCol(default=None)
    invoice_total = FloatCol(default=0.0)
    notes = StringCol(default='')
    freight_total = FloatCol(default=0.0)

    # This is Brazil-specific information
    icms_total = FloatCol(default=0.0)
    ipi_total = FloatCol(default=0.0)

    responsible = ForeignKey('PersonAdaptToUser')
    supplier = ForeignKey('PersonAdaptToSupplier')
    branch = ForeignKey('PersonAdaptToBranch')
    purchase = ForeignKey('PurchaseOrder', default=None)
    transporter = ForeignKey('PersonAdaptToTransporter', default=None)

    def _create(self, id, **kw):
        # ReceiveOrder objects must be set as valid explicitly
        kw['_is_valid_model'] = False
        Domain._create(self, id, **kw)

    def confirm(self):
        # Update all the items of the purchaseorder, updating its quantity
        # attribute
        pass


@argcheck(PurchaseOrder, ReceivingOrder)
def get_receiving_items_by_purchase_order(purchase_order, receiving_order):
    """Returns a list of receiving items based on a list of purchase items
    that weren't received yet.
    
    @param purchase_order: a PurchaseOrder instance that holds one or more
                           purchase items
    @param receiving_order: a ReceivingOrder instance tied with the
                            receiving_items that will be created
    """
    conn = purchase_order.get_connection()
    receiving_items = []
    for item in purchase_order.get_pending_items():
        quantity = item.get_pending_quantity()
        cost = item.cost
        sellable = item.sellable
        rec_item = ReceivingOrderItem(connection=conn,
                                      quantity_received=quantity, cost=cost,
                                      sellable=sellable, 
                                      receiving_order=receiving_order)
        receiving_items.append(rec_item)
    return receiving_items

