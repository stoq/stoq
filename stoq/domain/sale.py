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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##
"""
stoq/domain/sale.py:

    Sale object and related objects implementation.
"""

import gettext
from datetime import datetime

from sqlobject import StringCol, DateTimeCol, ForeignKey, IntCol, FloatCol
from stoqlib.exceptions import SellError

from stoq.domain.base import Domain
from stoq.domain.sellable import AbstractSellableItem
from stoq.domain.payment.base import AbstractPaymentGroup
from stoq.domain.product import ProductSellableItem
from stoq.domain.service import ServiceSellableItem
from stoq.domain.interfaces import (IContainer, IClient, IStorable, 
                                    IPaymentGroup)


_ = gettext.gettext



#
# Base Domain Classes
#



class Sale(Domain):
    """Sale object implementation.
    Nested imports are needed here because domain/sallable.py imports the
    current one.

    Information about some attributes: 
        order_number    =   an optional identifier for this sale defined 
                            by the store
        open_date       =   The day when we started this sale
        close_date      =   The day when we confirmed this sale
        notes           =   Some optional additional information related to 
                            this sale
        till            =   The Till operation where this sale lives. Note
                            that every sale and payment generated are always
                            in a till operation which defines a financial
                            history of a store.
    """

    __implements__ = IContainer

    (STATUS_OPENED, 
     STATUS_CONFIRMED, 
     STATUS_CLOSED, 
     STATUS_CANCELLED,
     STATUS_REVIEWING) = range(5)

    statuses = {STATUS_OPENED:          _("Opened"),
                STATUS_CONFIRMED:       _("Confirmed"),
                STATUS_CLOSED:          _("Closed"),
                STATUS_CANCELLED:       _("Cancelled"),
                STATUS_REVIEWING:       _("Reviewing")}

    order_number = StringCol(default='')
    open_date = DateTimeCol(default=datetime.now())
    close_date = DateTimeCol(default=None)
    status = IntCol(default=STATUS_OPENED)
    discount_value = FloatCol(default=0.0)
    charge_value = FloatCol(default=0.0)
    notes = StringCol(default='')
    
    client = ForeignKey('PersonAdaptToClient', default=None)
    till = ForeignKey('Till')
    salesperson = ForeignKey('PersonAdaptToSalesPerson', default=None)


    def get_status_name(self):
        return self.statuses[self.status]

    def update_client(self, person):
        # Do not change the name of this method to set_client: this is a
        # callback in SQLObject
        conn = self.get_connection()
        client = IClient(person, connection=conn)
        if not client:
            raise TypeError("%s cannot be adapted to IClient." % person)
        self.client = client

    def reset_discount_charge(self):
        self.discount_value = self.charge_value = 0.0

    def _get_percentage_value(self, percentage):
        if not percentage:
            return 0.0
        subtotal = self.get_sale_subtotal()
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
        subtotal = self.get_sale_subtotal()
        assert subtotal > 0, ('the sale subtotal should not be zero '
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
        subtotal = self.get_sale_subtotal()
        assert subtotal > 0, ('the sale subtotal should not be zero '
                              'at this point')
        total = subtotal + charge_value
        percentage = ((total / float(subtotal)) - 1) * 100
        return percentage

    charge_percentage = property(_get_charge_by_percentage,
                                 _set_charge_by_percentage)



    #
    # IContainer methods
    #



    def add_item(self, item):
        raise NotImplementedError("You should call add_selabble_item "
                                  "SellableItem method instead.")

    def get_items(self):
        conn = self.get_connection()
        return AbstractSellableItem.selectBy(connection=conn, saleID=self.id)

    def remove_item(self, item):
        if not isinstance(item, AbstractSellableItem):
            raise TypeError("Item should be of type AbstractSellableItem "
                            "got %s instead" % item)
        conn = self.get_connection()
        table = type(item)
        table.delete(item.id, connection=conn)



    #
    # Auxiliar methods
    #



    def get_till_branch(self):
        return self.till.branch

    def get_sale_subtotal(self):
        return sum([item.price for item in self.get_items()]) or 0.0

    def get_total_sale_amount(self):
        """Return the total value paid by the client. This can be 
        calculated by:.
        Sale total = Sum(product and service prices) + charge + 
                     interest - discount"""
        self.charge_value = self.charge_value or 0.0
        self.discount_value = self.discount_value or 0.0
        return (self.get_sale_subtotal() + self.charge_value - 
                self.discount_value)
        
    def get_total_interest(self):
        raise NotImplementedError
        
    def get_services(self):
        return [item for item in self.get_items() 
                    if isinstance(item, ServiceSellableItem)]

    def get_products(self):
        return [item for item in self.get_items() 
                    if isinstance(item, ProductSellableItem)]

    def update_stocks(self):
        conn = self.get_connection()
        branch = self.get_till_branch()
        for product in self.get_products():
            storable = IStorable(product.sellable.get_adapted(),
                                 connection=conn)
            storable.decrease_stock(product.quantity, branch)

    def confirm(self):
        if not self.status == self.STATUS_OPENED:
            raise SellError('The sale must have STATUS_OPENED for this '
                            'operation, got status %s instead' %
                            self.statuses[self.status])
        if self.client and not self.client.is_active:
            raise SellError('Unable to make sales for clients with status '
                            '%s' % self.client.get_status_string())
        conn = self.get_connection()
        group = IPaymentGroup(self, connection=conn)
        if not group:
            raise ValueError("Sale %s doesn't have an IPaymentGroup "
                             "facet at this point" % self)
        group.setup_payments()
        self.update_stocks()
        self.status = self.STATUS_CONFIRMED
        self.close_date = datetime.now()
        


#
# Adapters
#



class SaleAdaptToPaymentGroup(AbstractPaymentGroup):


    #
    # IPaymentGroup implementation
    #



    def get_thirdparty(self):
        sale = self.get_adapted()
        return sale.client

    def update_thirdparty_status(self):
        raise NotImplementedError



    #
    # Auxiliar methods
    #



    def get_pm_commission_total(self):
        """Return the payment method comission total. Usually credit 
        card payment method is the most common method which uses 
        commission
        """
        return 0.0
        
    def get_total_received(self):
        """Return the total amount paid by the client (sale total)
        deducted of payment method commissions"""
        sale = self.get_adapted()
        return sale.get_total_sale_amount() - self.get_pm_commission_total()

Sale.registerFacet(SaleAdaptToPaymentGroup)
