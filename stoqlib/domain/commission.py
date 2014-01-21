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

# pylint: enable=E1101

from decimal import Decimal

from storm.expr import Join, Cast
from storm.references import Reference

from stoqlib.database.properties import PercentCol, PriceCol
from stoqlib.database.properties import IntCol, IdCol
from stoqlib.database.viewable import Viewable
from stoqlib.domain.base import Domain
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.person import Person, SalesPerson, Branch
from stoqlib.domain.sale import Sale
from stoqlib.lib.defaults import quantize
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class CommissionSource(Domain):
    """Commission Source object implementation

    A CommissionSource is tied to a |sellablecategory| or |sellable|,
    it's used to determine the value of a commission for a certain
    item which is sold.
    There are two different commission values defined here, one
    which is used when the item is sold directly, eg one installment
    and another one which is used when the item is sold in installments.

    The category and the sellable should not exist when sellable exists
    and the opposite is true.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/commission_source.html>`__,
    """

    __storm_table__ = 'commission_source'

    #: the commission value to be used in a |sale| with one installment
    direct_value = PercentCol()

    #: the commission value to be used in a |sale| with multiple installments
    installments_value = PercentCol()

    category_id = IdCol(default=None)

    #: the |sellablecategory|
    category = Reference(category_id, 'SellableCategory.id')

    sellable_id = IdCol(default=None)

    #: the |sellable|
    sellable = Reference(sellable_id, 'Sellable.id')


class Commission(Domain):
    """Commission object implementation

    A Commission is the commission received by a |salesperson|
    for a specific |payment| made by a |sale|.

    There is one Commission for each |payment| of a |sale|.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/commission.html>`__,
    """

    __storm_table__ = 'commission'

    #: use direct commission to calculate the commission amount
    DIRECT = 0

    #: use installments commission to calculate the commission amount
    INSTALLMENTS = 1

    commission_type = IntCol(default=DIRECT)

    #: The commission amount
    value = PriceCol(default=0)

    sale_id = IdCol()

    #: the |sale| this commission applies to
    sale = Reference(sale_id, 'Sale.id')

    payment_id = IdCol()

    #: the |payment| this commission applies to
    payment = Reference(payment_id, 'Payment.id')

    #
    #  Domain
    #

    def __init__(self, store=None, **kwargs):
        need_calculate_value = not 'value' in kwargs
        super(Commission, self).__init__(store=store, **kwargs)
        if need_calculate_value:
            self._calculate_value()

    #
    #  Private
    #

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
        value = Decimal(0)
        for sellable_item in self.sale.get_items():
            value += (self._get_commission(sellable_item.sellable) *
                      sellable_item.get_total() *
                      relative_percentage)

        # The calculation above may have produced a number with more than two
        # digits. Round it to only two
        self.value = quantize(value)

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

        store = self.store
        source = store.find(CommissionSource, sellable=sellable).one()
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
            store = self.store
            source = store.find(CommissionSource, category=category).one()
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

    #: the branch this commission was generated
    branch = Branch

    payment = Payment
    sale = Sale

    # Sale
    id = Sale.id
    identifier = Sale.identifier
    identifier_str = Cast(Sale.identifier, 'text')
    sale_status = Sale.status
    confirm_date = Sale.confirm_date

    # Commission
    code = Commission.id
    commission_value = Commission.value
    commission_percentage = Commission.value / Payment.value * 100

    # Payment
    payment_id = Payment.id
    payment_value = Payment.value
    method_name = PaymentMethod.method_name
    paid_date = Payment.paid_date

    # Salesperson
    salesperson_id = SalesPerson.id
    salesperson_name = Person.name

    tables = [
        Sale,
        Join(Branch, Sale.branch_id == Branch.id),
        Join(Commission, Commission.sale_id == Sale.id),
        Join(SalesPerson, SalesPerson.id == Sale.salesperson_id),
        Join(Person, Person.id == SalesPerson.person_id),
        Join(Payment, Payment.id == Commission.payment_id),
        Join(PaymentMethod, Payment.method_id == PaymentMethod.id),
    ]

    @property
    def method_description(self):
        from stoqlib.domain.payment.operation import get_payment_operation
        return get_payment_operation(self.method_name).description

    # pylint: disable=E1120
    @property
    def quantity_sold(self):
        if self.sale_returned:
            # zero means 'this sale does not changed our stock'
            return Decimal(0)

        # FIXME: This is doing one extra query per row when printing the report
        return self.sale.get_items_total_quantity()

    @property
    def payment_amount(self):
        # the returning payment should be shown as negative one
        if self.payment.is_outpayment():
            return -self.payment_value
        return self.payment_value

    @property
    def total_amount(self):
        # XXX: No, the sale amount does not change. But I return different
        # values based in type of the payment to guess how I might show the
        # total sale amount.
        if self.payment.is_outpayment():
            return -self.sale.total_amount
        return self.sale.total_amount
    # pylint: enable=E1120

    @property
    def sale_returned(self):
        return self.sale_status == Sale.STATUS_RETURNED
