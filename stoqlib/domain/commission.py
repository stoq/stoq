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
from sqlobject.sqlbuilder import INNERJOINOn
from sqlobject.viewable import Viewable

from stoqlib.database.columns import DecimalCol
from stoqlib.domain.base import Domain
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.person import Person, PersonAdaptToSalesPerson
from stoqlib.domain.sale import Sale

from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class CommissionSource(Domain):
    """Commission Source object implementation

    A CommissionSource is tied to a Category or ASellable,
    it's used to determine the value of a commission for a certain
    item which is sold.
    There are two different commission values defined here, one
    which is used when the item is sold directly, eg one installment
    and another one which is used when the item is sold in installments.

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

    A Commission is the commission received by a SalesPerson
    for a specific payment made by a Sale.
    One instance of this is created for each payment for each sale.

    @cvar DIRECT: use direct commission to calculate the commission
        amount
    @cvar INSTALLMENTS: use installments commission to calculate the
        commission amount
    @cvar value: The commission amount
    @ivar salesperson: who sold the sale
    @ivar sale: the sale
    @ivar payment:
    """

    (DIRECT,
     INSTALLMENTS) = range(2)

    commission_type = IntCol(default=DIRECT)
    value = DecimalCol(default=0)
    salesperson = ForeignKey('PersonAdaptToSalesPerson')
    sale = ForeignKey('Sale')
    payment = ForeignKey('Payment')

    def _init(self, *args, **kwargs):
        Domain._init(self, *args, **kwargs)
        self._calculate_value()

    def _calculate_value(self):
        """Calculates the commission amount to be paid"""

        relative_percentage = self._get_payment_percentage()

        # The commission is calculated for all sellable items
        # in sale; a relative percentage is given for each payment
        # of the sale.
        # Eg:
        #   If a customer decides to pay a sale in two installments,
        #   Let's say divided in 20%, and 80% of the total value of the items
        #   which was bought in the sale. Then the commission received by the
        #   sales person is also going to be 20% and 80% of the complete
        #   commission amount for the sale when that specific payment is payed.
        value = 0
        for sellable_item in self.sale.get_items():
            value += (self._get_commission(sellable_item.sellable) *
                      sellable_item.get_total() *
                      relative_percentage)

        self.value = value

    def _get_payment_percentage(self):
        """Return the payment percentage of sale"""
        return self.payment.value / self.sale.get_sale_subtotal()

    def _get_commission(self, asellable):
        """Return the properly commission percentage to be used to
            calculate the commission amount, for a given sellable.
        """

        conn = self.get_connection()
        source = CommissionSource.selectOneBy(asellable=asellable,
                                              connection=conn)
        if not source and asellable.category:
           source = self._get_category_commission(asellable.category)

        value = 0
        if source:
            if self.commission_type == self.DIRECT:
                value = source.direct_value
            else:
                value = source.installments_value
            value /= Decimal(100)

        return value

    def _get_category_commission(self, category):
        if category:
            source =  CommissionSource.selectOneBy(
                category=category,
                connection=self.get_connection())
            if not source:
                return self._get_category_commission(category.category)
            return source

#
# Views
#

class CommissionView(Viewable):
    """ Stores information about commissions and it's related
            sale and payment.
    """

    columns = dict(
        id=Sale.q.id,
        code=Commission.q.id,
        commission_value=Commission.q.value,
        commission_percentage=Commission.q.value/Sale.q.total_amount*100,
        salesperson_name=Person.q.name,
        payment_amount=Payment.q.value,
        total_amount=Sale.q.total_amount,
        open_date=Sale.q.open_date,
       )

    joins = [
        # commission
        INNERJOINOn(None, Commission,
            Commission.q.saleID == Sale.q.id),

        # person
        INNERJOINOn(None, PersonAdaptToSalesPerson,
            PersonAdaptToSalesPerson.q.id == Commission.q.salespersonID),

        INNERJOINOn(None, Person,
            Person.q.id == PersonAdaptToSalesPerson.q._originalID),

        # payment
        INNERJOINOn(None, Payment,
            Payment.q.id == Commission.q.paymentID),
       ]
