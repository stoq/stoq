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
## Author(s): Stoq Team <stoq-devel@async.com.br>
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
from stoqlib.domain.payment.method import CheckData, CreditCardData, Payment
from stoqlib.domain.person import PersonAdaptToCreditProvider
from stoqlib.lib.interfaces import IPaymentOperation, IPaymentOperationManager
from stoqlib.lib.translation import stoqlib_gettext

from stoqdrivers.enum import PaymentMethodType

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

    def create_transaction(self):
        return False

    def selectable(self, method):
        return True

    def get_constant(self, payment):
        return PaymentMethodType.MONEY


class CheckPaymentOperation(object):
    implements(IPaymentOperation)

    description = _(u'Check')
    max_installments = 12

    def payment_create(self, payment):
        conn = payment.get_connection()
        bank_account = BankAccount(connection=conn,
                                   bank_number=None,
                                   bank_branch='',
                                   bank_account='')
        CheckData(bank_account=bank_account,
                  payment=payment,
                  connection=conn)

    def payment_delete(self, payment):
        conn = payment.get_connection()
        check_data = self.get_check_data_by_payment(payment)
        bank_account = check_data.bank_account
        CheckData.delete(check_data.id, connection=conn)
        BankAccount.delete(bank_account.id, connection=conn)

    def create_transaction(self):
        return True

    def selectable(self, method):
        return True

    def get_constant(self, payment):
        return PaymentMethodType.CHECK

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

    def create_transaction(self):
        return True

    def selectable(self, method):
        return True

    def get_constant(self, payment):
        return PaymentMethodType.BILL


class CardPaymentOperation(object):
    implements(IPaymentOperation)

    description = _(u'Card')
    max_installments = 12

    CARD_METHOD_CONSTANTS = {
        CreditCardData.TYPE_CREDIT: PaymentMethodType.CREDIT_CARD,
        CreditCardData.TYPE_DEBIT: PaymentMethodType.DEBIT_CARD,
        CreditCardData.TYPE_CREDIT_INSTALLMENTS_STORE:
             PaymentMethodType.CREDIT_CARD,
        CreditCardData.TYPE_CREDIT_INSTALLMENTS_PROVIDER:
             PaymentMethodType.CREDIT_CARD,
        CreditCardData.TYPE_DEBIT_PRE_DATED: PaymentMethodType.DEBIT_CARD,
    }

    #
    # IPaymentOperation
    #

    def payment_create(self, payment):
        return CreditCardData(connection=payment.get_connection(),
                              payment=payment)

    def payment_delete(self, payment):
        conn = payment.get_connection()
        credit_card_data = self.get_card_data_by_payment(payment)
        CreditCardData.delete(credit_card_data.id, connection=conn)

    def create_transaction(self):
        return True

    def selectable(self, method):
        return PersonAdaptToCreditProvider.has_card_provider(
            method.get_connection())

    def get_constant(self, payment):
        card_data = self.get_card_data_by_payment(payment)
        return self.CARD_METHOD_CONSTANTS.get(card_data.card_type)

    @argcheck(Payment)
    def get_card_data_by_payment(self, payment):
        """Get an existing CreditCardData instance from a payment object."""
        return CreditCardData.selectOneBy(payment=payment,
                                          connection=payment.get_connection())


class StoreCreditPaymentOperation(object):
    implements(IPaymentOperation)

    description = _(u'Store Credit')
    max_installments = 1

    #
    # IPaymentOperation
    #

    def payment_create(self, payment):
        pass

    def payment_delete(self, payment):
        pass

    def create_transaction(self):
        return False

    def selectable(self, method):
        return True

    def get_constant(self, payment):
        # FIXME: Add another constant to stoqdrivers?
        return PaymentMethodType.CUSTOM


class DepositPaymentOperation(object):
    implements(IPaymentOperation)

    description = _(u'Deposit')
    max_installments = 12

    #
    # IPaymentOperation
    #

    def payment_create(self, payment):
        pass

    def payment_delete(self, payment):
        pass

    def create_transaction(self):
        return True

    def selectable(self, method):
        return False

    def get_constant(self, payment):
        return PaymentMethodType.MONEY


# The MultiplePaymentOperation is not a payment operation, but we need to
# register it, so it could be activated or not. It will not create anything
# related to payments.
class MultiplePaymentOperation(object):
    implements(IPaymentOperation)

    description = _(u'Multiple')
    max_installments = 12

    #
    # IPaymentOperation
    #

    def payment_create(self, payment):
        pass

    def payment_delete(self, payment):
        pass

    def create_transaction(self):
        return True

    def selectable(self, method):
        return True

    def get_constant(self, payment):
        return PaymentMethodType.MULTIPLE


def register_payment_operations():
    pmm = get_utility(IPaymentOperationManager, None)
    if pmm is None:
        from stoqlib.lib.payment import PaymentOperationManager
        pmm = PaymentOperationManager()
        provide_utility(IPaymentOperationManager, pmm)

    # FIXME: maybe we should be doing this just once
    pmm.register('money', MoneyPaymentOperation())
    pmm.register('check', CheckPaymentOperation())
    pmm.register('bill', BillPaymentOperation())
    pmm.register('card', CardPaymentOperation())
    pmm.register('store_credit', StoreCreditPaymentOperation())
    pmm.register('multiple', MultiplePaymentOperation())
    pmm.register('deposit', DepositPaymentOperation())
