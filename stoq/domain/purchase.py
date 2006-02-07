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
import datetime

from kiwi.argcheck import argcheck
from kiwi.datatypes import format_price
from stoqlib.exceptions import DatabaseInconsistency
from sqlobject import ForeignKey, IntCol, DateTimeCol, FloatCol, StringCol
from zope.interface import implements

from stoq.domain.base import Domain
from stoq.domain.payment.base import AbstractPaymentGroup
from stoq.domain.columns import PriceCol
from stoq.domain.interfaces import (ICheckPM, IBillPM, IMoneyPM,
                                    IPaymentGroup)
from stoq.lib.parameters import sysparam

_ = gettext.gettext


class PurchaseItem(Domain):
    """This class stores information of the purchased items.
    
    B{Importante attributes}
        - I{base_cost}: the cost which helps the purchaser to define the 
                        main cost of a certain product.
    """
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
        if not 'order' in kw:
            raise TypeError('You must provide a order argument')

        kw['base_cost'] = kw['sellable'].cost
        
        if kw['sellable'].id in [item.sellable.id 
                                   for item in kw['order'].get_items()]:
            raise ValueError('This product was already added to the order')
        Domain._create(self, id, **kw)

    #
    # Accessors
    #

    def get_total(self):
        return self.quantity * self.cost

    def get_received_total(self):
        return self.quantity_received * self.cost

    def has_been_received(self):
        return self.quantity_received >= self.quantity

    def get_pending_quantity(self):
        if not self.has_been_received:
            return 0.0
        return self.quantity - self.quantity_received


class PurchaseOrder(Domain):
    """Purchase and order definition."""

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
    open_date = DateTimeCol(default=datetime.datetime.now)
    quote_deadline = DateTimeCol(default=None)
    expected_receival_date = DateTimeCol(default=None)
    expected_pay_date = DateTimeCol(default=None)
    receival_date = DateTimeCol(default=None)
    confirm_date = DateTimeCol(default=None)
    notes = StringCol(default='')
    salesperson_name = StringCol(default='')
    freight_type = IntCol(default=FREIGHT_FOB)
    freight = FloatCol(default=0.0)
    charge_value = PriceCol(default=0.0)
    discount_value = PriceCol(default=0.0)
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
    # General methods
    #

    def confirm_order(self, confirm_date=datetime.datetime.now()):
        if self.status != self.ORDER_PENDING:
            raise ValueError('Invalid order status, it should be '
                             'ORDER_PENDING, got %s' 
                             % self.get_status_str())
        conn = self.get_connection()
        if sysparam(conn).USE_PURCHASE_PREVIEW_PAYMENTS:
            group = IPaymentGroup(self, connection=conn)
            if not group:
                raise ValueError('You must have a IPaymentGroup facet '
                                 'defined at this point') 
            group.create_preview_outpayments()
        self.status = self.ORDER_CONFIRMED
        self.confirm_date = confirm_date

    def _get_percentage_value(self, percentage):
        if not percentage:
            return 0.0
        subtotal = self.get_purchase_subtotal()
        return subtotal * (percentage/100.0)

    def _set_discount_by_percentage(self, value):
        """Sets a discount by percentage.
        Note that percentage must be added as an absolute value not as a 
        factor like 1.05 = 5 % of charge
        The correct form is 'percentage = 3' for a discount of 3 %"""
        self.discount_value = self._get_percentage_value(value)

    def _get_discount_by_percentage(self):
        discount_value = self.discount_value
        if not discount_value:
            return 0.0
        subtotal = self.get_purchase_subtotal()
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
        The correct form is 'percentage = 3' for a charge of 3 %"""
        self.charge_value = self._get_percentage_value(value)

    def _get_charge_by_percentage(self):
        charge_value = self.charge_value
        if not charge_value:
            return 0.0
        subtotal = self.get_purchase_subtotal()
        assert subtotal > 0, ('the subtotal should not be zero '
                              'at this point')
        total = subtotal + charge_value
        percentage = ((total / float(subtotal)) - 1) * 100
        return percentage

    charge_percentage = property(_get_charge_by_percentage,
                                 _set_charge_by_percentage)
    def reset_discount_and_charge(self):
        self.discount_value = self.charge_value = 0.0

    def can_close(self):
        for item in self.get_items():
            if not item.has_been_received():
                return False
        return True

    def close(self):
        if not self.status == self.ORDER_CONFIRMED:
            raise ValueError('Invalid status, it should be confirmed'
                             'got %s instead' % self.get_status_str())
        self.status = self.ORDER_CLOSED

    def increase_quantity_received(self, sellable, 
                                   quantity_received):
        items = [item for item in self.get_items()
                    if item.sellable.id == sellable.id]
        qty = len(items)
        if not qty:
            raise ValueError('There is no purchase item for '
                             'sellable %r' % sellable)
        if qty > 1:
            raise DatabaseInconsistency('It should have only one item for '
                                        'this sellable, got %d instead'
                                        % qty)
        item = items[0]
        item.quantity_received += quantity_received

    #
    # Accessors
    #

    def get_freight_type_name(self):
        if not self.freight_type in self.freight_types.keys():
            raise DatabaseInconsistency('Invalid freight_type, got %d'
                                        % self.freight_type)
        return self.freight_types[self.freight_type]

    def get_branch_name(self):
        return self.branch.get_adapted().name

    def get_supplier_name(self):
        return self.supplier.get_adapted().name

    def get_transporter_name(self):
        if not self.transporter:
            return ""
        return self.transporter.get_adapted().name

    def get_order_number_str(self):
        if self.order_number:
            return '%03d' % self.order_number
        return ""

    def get_status_str(self):
        if not self.statuses.has_key(self.status):
            raise DatabaseInconsistency('Got an unexpected status value: '
                                        '%s' % self.status)
        return self.statuses[self.status]

    def get_purchase_subtotal(self):
        return sum([item.get_total() for item in self.get_items()], 0.0)

    def get_purchase_subtotal_str(self):
        return format_price(self.get_purchase_subtotal())

    def get_purchase_total(self):
        subtotal = self.get_purchase_subtotal()
        total = subtotal - self.discount_value + self.charge_value
        if total < 0:
            raise ValueError('Purchase total can not be lesser than zero')
        return total

    def get_purchase_total_str(self):
        return format_price(self.get_purchase_total())

    def get_received_total(self):
        return sum([item.cost * item.quantity_received 
                        for item in self.get_items()])

    def get_remaining_total(self):
        return self.get_purchase_total() - self.get_received_total()

    def get_pending_items(self):
        return [item for item in self.get_items() 
                        if not item.has_been_received()]

    def get_items(self):
        return PurchaseItem.selectBy(order=self,
                                     connection=self.get_connection())

    @argcheck(PurchaseItem)
    def remove_item(self, item):
        conn = self.get_connection()
        if item.order is not self:
            raise ValueError('Argument item must have an order attribute '
                             'associated with the current purchase instance')
        PurchaseItem.delete(item.id, connection=conn)
    

class PurchaseOrderAdaptToPaymentGroup(AbstractPaymentGroup):

    #
    # IPaymentGroup implementation
    #

    def get_thirdparty(self):
        order = self.get_adapted()
        if not order.supplier:
            raise DatabaseInconsistency('An order must have a supplier')
        return order.supplier.get_adapted()

    def set_thirdparty(self):
        raise NotImplementedError

    def get_group_description(self):
        order = self.get_adapted()
        return _('order %s') % order.order_number

    #
    # Auxiliar methods
    #

    def create_preview_outpayments(self):
        conn = self.get_connection()
        base_method = sysparam(conn).BASE_PAYMENT_METHOD
        order = self.get_adapted()
        total = order.get_purchase_total()
        first_due_date = order.expected_receival_date
        if self.default_method == self.METHOD_MONEY:
            method = IMoneyPM(base_method, connection=conn)
            method.setup_outpayments(total, self, self.installments_number)
            return
        elif self.default_method == self.METHOD_CHECK:
            method = ICheckPM(base_method, connection=conn)
        elif self.default_method == self.METHOD_BILL:
            method = IBillPM(base_method, connection=conn)
        else:
            raise ValueError('Invalid payment method, got %d' %
                             self.default_method)
        method.setup_outpayments(self, self.installments_number,
                                 first_due_date, self.interval_type,
                                 self.intervals, total)

        
PurchaseOrder.registerFacet(PurchaseOrderAdaptToPaymentGroup, IPaymentGroup)
