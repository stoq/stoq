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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""
Commission management
"""

from decimal import Decimal

from stoqlib.database.orm import PercentCol, PriceCol
from stoqlib.database.orm import ForeignKey, IntCol
from stoqlib.database.orm import INNERJOINOn
from stoqlib.database.orm import Viewable
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IOutPayment
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.person import Person, PersonAdaptToSalesPerson
from stoqlib.domain.sale import Sale

from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class CommissionSource(Domain):
    """Commission Source object implementation

    A CommissionSource is tied to a Category or Sellable,
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
    @ivar sellable: the sellable

    The category and the sellable should not exist when sellable exists
    and the opposite is true.
    """

    direct_value = PercentCol()
    installments_value = PercentCol()
    category = ForeignKey('SellableCategory', default=None)
    sellable = ForeignKey('Sellable', default=None)


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
    value = PriceCol(default=0)
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
        total = self.sale.get_sale_subtotal()
        if total == 0:
            return 0
        else:
            return self.payment.value / total

    def _get_commission(self, sellable):
        """Return the properly commission percentage to be used to
        calculate the commission amount, for a given sellable.
        """

        conn = self.get_connection()
        source = CommissionSource.selectOneBy(sellable=sellable,
                                              connection=conn)
        if not source and sellable.category:
            source = self._get_category_commission(sellable.category)

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
            source = CommissionSource.selectOneBy(
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
        commission_percentage=Commission.q.value / Sale.q.total_amount * 100,
        salesperson_name=Person.q.name,
        payment_id=Payment.q.id,
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
            Person.q.id == PersonAdaptToSalesPerson.q.originalID),

        # payment
        INNERJOINOn(None, Payment,
            Payment.q.id == Commission.q.paymentID),
       ]

    @property
    def sale(self):
        return Sale.get(self.id, connection=self.get_connection())

    @property
    def payment(self):
        return Payment.get(self.payment_id, connection=self.get_connection())

    def quantity_sold(self):
        if self.sale_returned():
            # zero means 'this sale does not changed our stock'
            return Decimal(0)

        return self.sale.get_items_total_quantity()

    def get_payment_amount(self):
        # the returning payment should be shown as negative one
        if IOutPayment(self.payment, None) is not None:
            return -self.payment.value
        return self.payment.value

    def get_total_amount(self):
        # XXX: No, the sale amount does not change. But I return different
        # values based in type of the payment to guess how I might show the
        # total sale amount.
        negative = IOutPayment(self.payment, None) is not None
        if negative:
            return -self.sale.total_amount
        return self.sale.total_amount

    def sale_returned(self):
        return self.sale.status == Sale.STATUS_RETURNED
