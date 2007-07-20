# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## Author(s): George Kussumoto  <george@async.com.br>
##
"""
Commission management
"""

from decimal import Decimal
from sqlobject import ForeignKey, IntCol

from stoqlib.database.columns import DecimalCol
from stoqlib.domain.base import Domain
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

class CommissionSource(Domain):
    """Commission Source object implementation

    @cvar direct_value: the commission value to be used in
      one-installment sales
    @cvar installments_value: the commission value to be used in
      more than one installments sales
    @ivar category: the sellable category
    @ivar asellable: the sellable

    The category and the sellable should not exist when asellable exists
      and the opposite is true.
    """

    direct_value = DecimalCol()
    installments_value = DecimalCol()
    category = ForeignKey('SellableCategory', default=None)
    asellable = ForeignKey('ASellable', default=None)

class Commission(Domain):
    """Commission object implementation

    @cvar DIRECT: use direct commission to calculate the commission
        amount
    @cvar INSTALLMENTS: use installments commission to calculate the
        commission amount
    @cvar value: The commission amount
    @ivar salesperson: who sold the sale
    @ivar sale: the sale
    @ivar payment
    """

    (DIRECT,
     INSTALLMENTS) = range(2)

    commission_type = IntCol(default=DIRECT)
    value = DecimalCol(default=0)
    salesperson = ForeignKey('PersonAdaptToSalesPerson')
    sale = ForeignKey('Sale')
    payment = ForeignKey('Payment')

    def __init__(self, *args, **kwargs):
        Domain.__init__(self, *args, **kwargs)
        self._calculate_value()

    def _calculate_value(self):
        """Calculates the commission amount to be paid"""

        relative_percentage = self._get_payment_percentage()
        value = 0
        for item in self.sale.get_items():
            commission = self._get_commission(item.sellable)
            if commission:
                item_commission = commission * item.get_total()
                value += relative_percentage * item_commission

        self.value = value

    def _get_payment_percentage(self):
        """Return the payment percentage of sale"""

        total = self.sale.get_total_sale_amount()
        return self.payment.value / total

    def _get_commission(self, asellable):
        """Return the properly commission percentage to be used to
            calculate the commission amount, for a given sellable.
        """

        conn = self.get_connection()
        source = CommissionSource.selectOneBy(asellable=asellable,
                                              connection=conn)
        if not source and asellable.category:
           source = self._get_category_commission(asellable.category)

        if source == None:
            return

        if self.commission_type == self.DIRECT:
            return source.direct_value / Decimal(100)
        else:
            return source.installments_value / Decimal(100)

    def _get_category_commission(self, category):
        if category:
            source =  CommissionSource.selectOneBy(category=category,
                                    connection=self.get_connection())
            if not source:
                return self._get_category_commission(category.category)
            return source
