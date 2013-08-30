# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""Domain implementation for Cost Centers
"""

# pylint: enable=E1101

from storm.expr import And, Ne
from stoqlib.database.properties import (BoolCol, PriceCol,
                                         UnicodeCol, IdCol)
from storm.references import Reference
from stoqlib.domain.base import Domain
from stoqlib.domain.stockdecrease import StockDecrease
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class CostCenter(Domain):
    """A |costcenter| holds a set of |costcenterentry| objects.

    |costcenterentry| are created when a resource from the company is spent. Right
    now, these resources are:

    * Money used to pay an lonely out |payment|
    * Products removed from the stock (not all situations).

    Entries are not created for out |payment| related to a |purchase|,
    |stockdecrease| or any other operation that changes the stock, since those
    costs will be accounted when the stock is actually decreased.

    Also, entries are only created for stock removal when the products are
    actually destined for a final usage. For instance, |transfer| and |loan| should
    not generate cost entries.

    As of this writing, the only stock operations that should trigger a cost
    entry creation are:

    * |sale|
    * |stockdecrease|
    """

    __storm_table__ = 'cost_center'

    #: the name of the cost center
    name = UnicodeCol(default=u'')

    #: a description for the cost center
    description = UnicodeCol(default=u'')

    #: The budget available for this cost center
    budget = PriceCol(default=0)

    #: indicates whether it's still possible to add entries to this
    #: |costcenter|.
    is_active = BoolCol(default=True)

    #
    # Public API
    #

    def get_payment_entries(self):
        return self.store.find(CostCenterEntry,
                               And(CostCenterEntry.cost_center == self,
                                   Ne(CostCenterEntry.payment_id, None)))

    def get_stock_transaction_entries(self):
        return self.store.find(CostCenterEntry,
                               And(CostCenterEntry.cost_center == self,
                                   Ne(CostCenterEntry.stock_transaction_id, None)))

    def get_stock_decreases(self):
        """This method fetches all the |stockdecreases| related to this
        |costcenter|.
        """
        return self.store.find(StockDecrease, cost_center=self)

    def get_sales(self):
        """This method fetches all the |sales| related to this |costcenter|"""
        from stoqlib.domain.sale import Sale
        return self.store.find(Sale, cost_center=self)

    def get_payments(self):
        """Returns all payments registred in this |costcenter|
        """
        from stoqlib.domain.payment.payment import Payment
        query = And(CostCenterEntry.cost_center == self,
                    CostCenterEntry.payment_id == Payment.id)
        return self.store.find(Payment, query)

    def get_entries(self):
        """This method gets all the |costcenterentry| related to this
        |costcenter|.
        """
        return self.store.find(CostCenterEntry, cost_center=self)

    @classmethod
    def get_active(cls, store):
        return store.find(cls, is_active=True)

    def add_stock_transaction(self, stock_transaction):
        """This method is called to create a |costcenterentry| when a product
        is removed from stock and this is being related to this
        |costcenter|."""

        assert stock_transaction.quantity < 0
        assert self.is_active

        CostCenterEntry(cost_center=self, stock_transaction=stock_transaction,
                        store=self.store)

    def add_lonely_payment(self, lonely_payment):
        """This method is called to create a |costcenterentry| when a lonely
        payment is confirmed and being related to this |costcenter|."""

        assert self.is_active

        CostCenterEntry(cost_center=self, payment=lonely_payment,
                        store=self.store)


class CostCenterEntry(Domain):
    """A operation that generated some cost in a |costcenter|.

    A cost can be generated when a lonely out |payment| is paid or when some
    operations on the stock are performed.
    """
    __storm_table__ = 'cost_center_entry'

    cost_center_id = IdCol()

    #: The cost center this entry belongs to
    cost_center = Reference(cost_center_id, 'CostCenter.id')

    payment_id = IdCol()

    #: The payment that generated this cost.
    payment = Reference(payment_id, 'Payment.id')

    stock_transaction_id = IdCol()

    #: The stock movement transaction that generated this cost.
    stock_transaction = Reference(stock_transaction_id,
                                  'StockTransactionHistory.id')
