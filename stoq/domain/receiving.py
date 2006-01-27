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
import gettext

from sqlobject import ForeignKey, IntCol, DateTimeCol, FloatCol, StringCol
from stoqlib.exceptions import DatabaseInconsistency
from zope.interface import implements
from kiwi.argcheck import argcheck

from stoq.domain.base import Domain
from stoq.domain.interfaces import IStorable
from stoq.domain.purchase import PurchaseOrder
from stoq.lib.validators import get_formatted_price
from stoq.lib.columns import PriceCol

_ = gettext.gettext


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

    (STATUS_PENDING,
     STATUS_CLOSED) = range(2)
        
    status = IntCol(default=STATUS_PENDING)
    receival_date = DateTimeCol(default=datetime.datetime.now)
    confirm_date = DateTimeCol(default=None)
    invoice_number = StringCol(default='')
    invoice_total = PriceCol(default=0.0)
    notes = StringCol(default='')
    freight_total = PriceCol(default=0.0)
    charge_value = FloatCol(default=0.0)
    discount_value = FloatCol(default=0.0)

    # This is Brazil-specific information
    icms_total = PriceCol(default=0.0)
    ipi_total = PriceCol(default=0.0)

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
        conn = self.get_connection()
        for item in self.get_items():
            sellable = item.sellable
            adapted = item.sellable.get_adapted()
            storable = IStorable(adapted, connection=conn)
            if not storable:
                raise DatabaseInconsistency('Sellable %r must have a '
                                            'storable facet at this point'
                                            % sellable)
            quantity = item.quantity_received
            storable.increase_stock(quantity, self.branch)
            if self.purchase:
                self.purchase.increase_quantity_received(sellable, quantity)
        if self.purchase and self.purchase.can_close():
            self.purchase.close()

    def get_items(self):
        conn = self.get_connection()
        return ReceivingOrderItem.selectBy(receiving_order=self,
                                           connection=conn)

    #
    # Accessors
    #
    
    def get_products_total(self):
        return sum([item.get_total() for item in self.get_items()], 0.0)

    def get_products_total_str(self):
        return get_formatted_price(self.get_products_total())

    def get_order_total(self):
        products_total = self.get_products_total()
        order_total = (products_total + self.charge_value -
                       self.discount_value + self.icms_total +
                       self.ipi_total + self.freight_total)
        if order_total < 0:
            raise DatabaseInconsistency('Order total must be greater '
                                        'than zero')
        return order_total

    def get_order_total_str(self):
        return get_formatted_price(self.get_order_total())

    def get_order_number(self):
        if not self.purchase:
            return _('No order set')
        return self.purchase.get_order_number_str()
        
    #
    # General methods
    #

    def reset_discount_and_charge(self):
        self.discount_value = self.charge_value = 0.0

    def _get_percentage_value(self, percentage):
        if not percentage:
            return 0.0
        subtotal = self.get_products_total()
        return subtotal * (percentage/100.0)

    def _set_discount_by_percentage(self, value):
        """Sets a discount by percentage.
        Note that percentage must be added as an absolute value not as a 
        factor like 1.05 = 5 % of charge
        The correct form is 'percentage = 3' for a discount of 3 %
        """
        self.discount_value = self._get_percentage_value(value)

    def _get_discount_by_percentage(self):
        discount_value = self.discount_value
        if not discount_value:
            return 0.0
        subtotal = self.get_products_total()
        assert subtotal > 0, ('the subtotal should not be zero '
                              'at this point')
        total = subtotal - discount_value
        percentage = (1 - total / float(subtotal)) * 100
        return percentage

    discount_percentage = property(_get_discount_by_percentage,
                                   _set_discount_by_percentage)

    def _set_charge_by_percentage(self, value):
        """Sets a charge by percentage.
        Note that charge must be added as an absolute value not as a 
        factor like 0.97 = 3 % of discount.
        The correct form is 'percentage = 3' for a charge of 3 %
        """
        self.charge_value = self._get_percentage_value(value)

    def _get_charge_by_percentage(self):
        charge_value = self.charge_value
        if not charge_value:
            return 0.0
        subtotal = self.get_products_total()
        assert subtotal > 0, ('the subtotal should not be zero '
                              'at this point')
        total = subtotal + charge_value
        percentage = ((total / float(subtotal)) - 1) * 100
        return percentage

    charge_percentage = property(_get_charge_by_percentage,
                                 _set_charge_by_percentage)


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
    return [ReceivingOrderItem(connection=conn,
                               quantity_received=item.get_pending_quantity(),
                               cost=item.cost,
                               sellable=item.sellable, 
                               receiving_order=receiving_order)
            for item in purchase_order.get_pending_items()]
