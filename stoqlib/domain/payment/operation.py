# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008-2012 Async Open Source <http://www.async.com.br>
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
from stoqlib.domain.person import CreditProvider
from stoqlib.lib.interfaces import IPaymentOperation, IPaymentOperationManager
from stoqlib.lib.translation import stoqlib_gettext

from stoqdrivers.enum import PaymentMethodType

_ = stoqlib_gettext


class MoneyPaymentOperation(object):
    implements(IPaymentOperation)

    description = _('Money')
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

    def creatable(self, method, payment_type, separate):
        # FIXME: This needs an editor
        if payment_type == Payment.TYPE_OUT:
            return False
        return True

    def get_constant(self, payment):
        return PaymentMethodType.MONEY

    def can_cancel(self, payment):
        return True

    def can_change_due_date(self, payment):
        return True

    def can_pay(self, payment):
        return True

    def can_print(self, payment):
        return False

    def print_(self, payment):
        pass


class CheckPaymentOperation(object):
    implements(IPaymentOperation)

    description = _('Check')
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

    def creatable(self, method, payment_type, separate):
        return True

    def get_constant(self, payment):
        return PaymentMethodType.CHECK

    def can_cancel(self, payment):
        return True

    def can_change_due_date(self, payment):
        return True

    def can_pay(self, payment):
        return True

    def can_print(self, payment):
        return False

    def print_(self, payment):
        pass

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

    description = _('Bill')
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

    def creatable(self, method, payment_type, separate):
        return True

    def payable(self, payment_type):
        return True

    def can_cancel(self, payment):
        return True

    def can_change_due_date(self, payment):
        return True

    def can_pay(self, payment):
        return True

    def can_print(self, payment):
        if payment.status != Payment.STATUS_PENDING:
            return False
        return True

    def print_(self, payments):
        from stoqlib.reporting.boleto import BillReport
        if not BillReport.check_printable(payments):
            return None
        return BillReport

    def get_constant(self, payment):
        return PaymentMethodType.BILL


class CardPaymentOperation(object):
    implements(IPaymentOperation)

    description = _('Card')
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
        return CreditProvider.has_card_provider(
            method.get_connection())

    def creatable(self, method, payment_type, separate):
        # FIXME: this needs more work, probably just a simple bug
        if payment_type == Payment.TYPE_OUT:
            return False
        return True

    def can_cancel(self, payment):
        return True

    def can_change_due_date(self, payment):
        return True

    def can_pay(self, payment):
        return True

    def can_print(self, payment):
        return False

    def print_(self, payment):
        pass

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

    description = _('Store Credit')
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

    def creatable(self, method, payment_type, separate):
        # Store credits are only allowed when selling of course.
        if payment_type != Payment.TYPE_IN:
            return False

        return True

    def can_cancel(self, payment):
        return True

    def can_change_due_date(self, payment):
        return True

    def can_pay(self, payment):
        # Until we fix bug 3703, don't allow receiving store credit payments
        return False

    def can_print(self, payment):
        return False

    def print_(self, payment):
        pass

    def get_constant(self, payment):
        # FIXME: Add another constant to stoqdrivers?
        return PaymentMethodType.CUSTOM


class DepositPaymentOperation(object):
    implements(IPaymentOperation)

    description = _('Deposit')
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

    def creatable(self, method, payment_type, separate):
        return True

    def get_constant(self, payment):
        return PaymentMethodType.MONEY

    def can_cancel(self, payment):
        return True

    def can_change_due_date(self, payment):
        return True

    def can_pay(self, payment):
        return True

    def can_print(self, payment):
        return False

    def print_(self, payment):
        pass


class OnlinePaymentOperation(object):
    implements(IPaymentOperation)

    description = _('Online')
    max_installments = 1

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

    def creatable(self, method, payment_type, separate):
        return False

    def get_constant(self, payment):
        # FIXME: Using MONEY for now..Maybe we should add a new constant.
        return PaymentMethodType.MONEY

    def can_cancel(self, payment):
        return False

    def can_change_due_date(self, payment):
        return False

    def can_pay(self, payment):
        return False

    def can_print(self, payment):
        return False

    def print_(self, payment):
        pass


# The MultiplePaymentOperation is not a payment operation, but we need to
# register it, so it could be activated or not. It will not create anything
# related to payments.
class MultiplePaymentOperation(object):
    implements(IPaymentOperation)

    description = _('Multiple')
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

    def creatable(self, method, payment_type, separate):
        # FIXME: This is currently not implemented, we just need
        #        a new interface for that.
        if separate:
            return False

        # FIXME: This is just a bug, needs some debugging
        if payment_type == Payment.TYPE_OUT:
            return False

        return True

    def can_cancel(self, payment):
        return False

    def can_change_due_date(self, payment):
        return False

    def can_pay(self, payment):
        return False

    def can_print(self, payment):
        return False

    def print_(self, payment):
        pass

    def get_constant(self, payment):
        return PaymentMethodType.MULTIPLE


class InvalidPaymentOperation(object):
    """This operation will be used as a fallback for methods that wore removed
    from stoq, but may still exist in the database (they cannot be removed,
    since payments may have been created using that method).
    """
    implements(IPaymentOperation)

    description = _('Invalid payment')
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
        return False

    def creatable(self, method, payment_type, separate):
        return False

    def get_constant(self, payment):
        return PaymentMethodType.MONEY

    def can_cancel(self, payment):
        return True

    def can_change_due_date(self, payment):
        return True

    def can_pay(self, payment):
        return True

    def can_print(self, payment):
        return False

    def print_(self, payment):
        pass


def get_payment_operation_manager():
    """Returns the payment operation manager"""
    pmm = get_utility(IPaymentOperationManager, None)

    if not pmm:
        from stoqlib.lib.payment import PaymentOperationManager
        pmm = PaymentOperationManager()
        provide_utility(IPaymentOperationManager, pmm)

        for method_name, klass in [
            ('money', MoneyPaymentOperation),
            ('check', CheckPaymentOperation),
            ('bill', BillPaymentOperation),
            ('card', CardPaymentOperation),
            ('store_credit', StoreCreditPaymentOperation),
            ('multiple', MultiplePaymentOperation),
            ('deposit', DepositPaymentOperation),
            ('online', OnlinePaymentOperation),
            ]:
            pmm.register(method_name, klass())
        # Also, register InvalidPaymentOperation as a fallback operation
        pmm.register_fallback(InvalidPaymentOperation())

    return pmm


def get_payment_operation(method_name):
    """Returns the payment operation for method_name

    :param method_name: the method name
    """
    pmm = get_payment_operation_manager()
    pm = pmm.get(method_name)
    if not pm:
        raise KeyError("There's no payment operation for method '%s'" %
                       method_name)

    return pm
