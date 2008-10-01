# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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
## Author(s):   Johan Dahlin               <jdahlin@async.com.br>
##

"""Payment operations

This file contains payment operations, a payment operation is responsible
for the logic needed by a payment method.
Such as storing the kind of credit card or associate a check with a bank account.
"""

from kiwi.argcheck import argcheck
from kiwi.component import get_utility, provide_utility
from zope.interface import implements

from stoqlib.domain.account import BankAccount
from stoqlib.domain.payment.method import CheckData, Payment
from stoqlib.domain.person import PersonAdaptToCreditProvider
from stoqlib.lib.interfaces import IPaymentOperation, IPaymentOperationManager
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class MoneyPaymentOperation(object):
    implements(IPaymentOperation)

    description = _(u'Money')
    max_installments = 1

    #
    # IPaymentOperation
    #

    def payment_create(self, payment):
        pass

    def payment_delete(self, payment):
        pass

    def selectable(self, method):
        return True


class CheckPaymentOperation(object):
    implements(IPaymentOperation)

    description = _(u'Check')
    max_installments = 12


    #
    # IPaymentOperation
    #

    def payment_create(self, payment):
        conn = payment.get_connection()
        # Every check must have a check data reference
        CheckData(bank_data=BankAccount(connection=conn),
                  payment=payment.get_adapted(),
                  connection=conn)

    def payment_delete(self, payment):
        conn = payment.get_connection()
        check_data = self.get_check_data_by_payment(payment)
        bank_data = check_data.bank_data
        CheckData.delete(check_data.id, connection=conn)
        BankAccount.delete(bank_data.id, connection=conn)

    def selectable(self, method):
        return True

    #
    # Public API
    #

    @argcheck(Payment)
    def get_check_data_by_payment(self, payment):
        """Get an existing CheckData instance from a payment object."""
        return CheckData.selectOneBy(payment=payment,
                                     connection=payment.get_connection())


class BillPaymentOperation(object):
    implements(IPaymentOperation)

    description = _(u'Bill')
    max_installments = 12

    #
    # IPaymentOperation
    #

    def payment_create(self, payment):
        pass

    def payment_delete(self, payment):
        pass

    def selectable(self, method):
        return True


class CardPaymentOperation(object):
    implements(IPaymentOperation)

    description = _(u'Card')
    max_installments = 12

    #
    # IPaymentOperation
    #

    def payment_create(self, payment):
        pass

    def payment_delete(self, payment):
        pass

    def selectable(self, method):
        return PersonAdaptToCreditProvider.has_card_provider(
            method.get_connection())


def register_payment_operations():
    pmm = get_utility(IPaymentOperationManager, None)
    if pmm is None:
        from stoqlib.lib.paymentoperation import PaymentOperationManager
        pmm = PaymentOperationManager()
        provide_utility(IPaymentOperationManager, pmm)
    pmm.register('money', MoneyPaymentOperation())
    pmm.register('check', CheckPaymentOperation())
    pmm.register('bill', BillPaymentOperation())
    pmm.register('card', CardPaymentOperation())
