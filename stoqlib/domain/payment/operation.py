# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008-2013 Async Open Source <http://www.async.com.br>
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

# pylint: enable=E1101

from kiwi.component import get_utility, provide_utility
from stoqdrivers.enum import PaymentMethodType
from zope.interface import implementer

from stoqlib.domain.account import BankAccount
from stoqlib.domain.payment.card import CreditProvider, CreditCardData
from stoqlib.domain.payment.method import CheckData, Payment
from stoqlib.lib.interfaces import IPaymentOperation, IPaymentOperationManager
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


def payment_operation(method_name=None, fallback=False):
    """
    A class decorator to register a payment operation which contains some
    of the business logic for a certain payment method.

    :param method_name: name of the method or ``None``
    :param fallback: if ``True``, will be registered as a fallback
    """
    def wrapper(cls):
        pmm = get_payment_operation_manager()
        if fallback:
            pmm.register_fallback(cls())
        else:
            pmm.register(method_name, cls())
        return cls
    return wrapper


def get_payment_operation_manager():
    """Returns the payment operation manager"""
    pmm = get_utility(IPaymentOperationManager, None)

    if not pmm:
        from stoqlib.lib.payment import PaymentOperationManager
        pmm = PaymentOperationManager()
        provide_utility(IPaymentOperationManager, pmm)

    return pmm


def get_payment_operation(method_name):
    """Returns the payment operation for method_name

    :param method_name: the method name
    """
    pmm = get_payment_operation_manager()
    pm = pmm.get(method_name)
    if not pm:  # pragma: nocover
        raise KeyError(u"There's no payment operation for method '%s'" %
                       method_name)

    return pm


@payment_operation(u'money')
@implementer(IPaymentOperation)
class MoneyPaymentOperation(object):

    description = _(u'Money')
    max_installments = 1

    #
    # IPaymentOperation
    #

    def pay_on_sale_confirm(self):
        return True

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

    def can_set_not_paid(self, payment):
        return True

    def print_(self, payments):
        pass

    def require_person(self, payment_type):
        return False


@payment_operation(u'check')
@implementer(IPaymentOperation)
class CheckPaymentOperation(object):

    description = _(u'Check')
    max_installments = 12

    def pay_on_sale_confirm(self):
        return False

    def payment_create(self, payment):
        store = payment.store
        bank_account = BankAccount(store=store,
                                   bank_number=None,
                                   bank_branch=u'',
                                   bank_account=u'')
        CheckData(bank_account=bank_account,
                  payment=payment,
                  store=store)

    def payment_delete(self, payment):
        store = payment.store
        check_data = self.get_check_data_by_payment(payment)
        bank_account = check_data.bank_account
        store.remove(check_data)
        store.remove(bank_account)

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

    def can_set_not_paid(self, payment):
        return True

    def print_(self, payments):
        pass

    def require_person(self, payment_type):
        return False

    #
    # Public API
    #

    def get_check_data_by_payment(self, payment):
        """Get an existing CheckData instance from a payment object."""
        store = payment.store
        return store.find(CheckData, payment=payment).one()


@payment_operation(u'bill')
@implementer(IPaymentOperation)
class BillPaymentOperation(object):

    description = _(u'Bill')
    max_installments = 12

    #
    # IPaymentOperation
    #

    def pay_on_sale_confirm(self):
        return False

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

    def can_set_not_paid(self, payment):
        return True

    def print_(self, payments):
        from stoqlib.reporting.boleto import BillReport
        if not BillReport.check_printable(payments):
            return None
        return BillReport

    def get_constant(self, payment):
        return PaymentMethodType.BILL

    def require_person(self, payment_type):
        if payment_type == Payment.TYPE_IN:
            return True
        return False


@payment_operation(u'card')
@implementer(IPaymentOperation)
class CardPaymentOperation(object):

    description = _(u'Card')
    max_installments = 12

    CARD_METHOD_CONSTANTS = {
        CreditCardData.TYPE_CREDIT: PaymentMethodType.CREDIT_CARD,
        CreditCardData.TYPE_DEBIT: PaymentMethodType.DEBIT_CARD,
        CreditCardData.TYPE_CREDIT_INSTALLMENTS_STORE: PaymentMethodType.CREDIT_CARD,
        CreditCardData.TYPE_CREDIT_INSTALLMENTS_PROVIDER: PaymentMethodType.CREDIT_CARD,
        CreditCardData.TYPE_DEBIT_PRE_DATED: PaymentMethodType.DEBIT_CARD,
    }

    #
    # IPaymentOperation
    #

    def pay_on_sale_confirm(self):
        return False

    def payment_create(self, payment):
        return CreditCardData(store=payment.store,
                              payment=payment)

    def payment_delete(self, payment):
        store = payment.store
        credit_card_data = self.get_card_data_by_payment(payment)
        store.remove(credit_card_data)

    def create_transaction(self):
        return True

    def selectable(self, method):
        return CreditProvider.has_card_provider(
            method.store)

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

    def can_set_not_paid(self, payment):
        return True

    def print_(self, payments):
        pass

    def get_constant(self, payment):
        card_data = self.get_card_data_by_payment(payment)
        return self.CARD_METHOD_CONSTANTS.get(card_data.card_type)

    def require_person(self, payment_type):
        return False

    #
    #  Public API
    #

    def get_card_data_by_payment(self, payment):
        """Get an existing CreditCardData instance from a payment object."""
        store = payment.store
        return store.find(CreditCardData, payment=payment).one()


@payment_operation(u'store_credit')
@implementer(IPaymentOperation)
class StoreCreditPaymentOperation(object):

    description = _(u'Store Credit')
    max_installments = 1
    #
    # IPaymentOperation
    #

    def pay_on_sale_confirm(self):
        return False

    def payment_create(self, payment):
        pass

    def payment_delete(self, payment):
        pass

    def create_transaction(self):
        return True

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
        return True

    def can_print(self, payment):
        # FIXME: Because of bug #5039, it's possible to create an alone
        #        store_credit payment without a payer. It makes no sense
        #        to print those as none will pay. Remove this when fixed
        if not payment.group.payer:
            return False
        if payment.status != Payment.STATUS_PENDING:
            return False

        return True

    def can_set_not_paid(self, payment):
        return True

    def print_(self, payments):
        from stoqlib.reporting.booklet import BookletReport
        return BookletReport

    def get_constant(self, payment):
        # FIXME: Add another constant to stoqdrivers?
        return PaymentMethodType.MONEY

    def require_person(self, payment_type):
        if payment_type == Payment.TYPE_IN:
            return True
        return False


@payment_operation(u'credit')
@implementer(IPaymentOperation)
class CreditPaymentOperation(object):
    """This payment method is used to register deposits (inpayments) and
    withdrawals (outpayments) in a client's credit account.

    When returning a sale, the store or the client can choose whether they want
    to return in cash or if the account is deposited as credit so the client
    can use it in the future.
    """

    description = _(u'Credit')
    max_installments = 1

    #
    # IPaymentOperation
    #

    def pay_on_sale_confirm(self):
        return True

    def payment_create(self, payment):
        pass

    def payment_delete(self, payment):
        pass

    def create_transaction(self):
        return False

    def selectable(self, method):
        return True

    def creatable(self, method, payment_type, separate):
        # Credit is only allowed when selling.
        if payment_type != Payment.TYPE_IN:
            return False
        return True

    def can_cancel(self, payment):
        return False

    def can_change_due_date(self, payment):
        return False

    def can_pay(self, payment):
        return True

    def can_print(self, payment):
        return False

    def can_set_not_paid(self, payment):
        return False

    def print_(self, payments):
        pass

    def get_constant(self, payment):
        # FIXME: Add another constant to stoqdrivers?
        return PaymentMethodType.MONEY

    def require_person(self, payment_type):
        return True


@payment_operation(u'deposit')
@implementer(IPaymentOperation)
class DepositPaymentOperation(object):

    description = _(u'Deposit')
    max_installments = 12

    #
    # IPaymentOperation
    #

    def pay_on_sale_confirm(self):
        return False

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

    def can_set_not_paid(self, payment):
        return True

    def print_(self, payments):
        pass

    def require_person(self, payment_type):
        return False


@payment_operation(u'online')
@implementer(IPaymentOperation)
class OnlinePaymentOperation(object):

    description = _(u'Online')
    max_installments = 1

    #
    # IPaymentOperation
    #

    def pay_on_sale_confirm(self):
        return False

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
        return True

    def can_print(self, payment):
        return False

    def can_set_not_paid(self, payment):
        return True

    def print_(self, payments):
        pass

    def require_person(self, payment_type):
        return True


@payment_operation(u'trade')
@implementer(IPaymentOperation)
class TradePaymentOperation(object):

    description = _(u'Trade')
    max_installments = 1

    #
    # IPaymentOperation
    #

    def pay_on_sale_confirm(self):
        return False

    def payment_create(self, payment):
        pass

    def payment_delete(self, payment):
        pass

    def create_transaction(self):
        # FIXME: Is it right to not create a transaction for this?
        return False

    def selectable(self, method):
        return False

    def creatable(self, method, payment_type, separate):
        return False

    def can_cancel(self, payment):
        return False

    def can_change_due_date(self, payment):
        return False

    def can_pay(self, payment):
        return False

    def can_print(self, payment):
        return False

    def can_set_not_paid(self, payment):
        return False

    def print_(self, payments):
        pass

    def get_constant(self, payment):
        # FIXME: What constant should this get?
        return PaymentMethodType.MONEY

    def require_person(self, payment_type):
        return False


# The MultiplePaymentOperation is not a payment operation, but we need to
# register it, so it could be activated or not. It will not create anything
# related to payments.
@payment_operation(u'multiple')
@implementer(IPaymentOperation)
class MultiplePaymentOperation(object):

    description = _(u'Multiple')
    max_installments = 12

    #
    # IPaymentOperation
    #

    def pay_on_sale_confirm(self):
        return False

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

    def can_set_not_paid(self, payment):
        return False

    def print_(self, payments):
        pass

    def get_constant(self, payment):
        return PaymentMethodType.MULTIPLE

    def require_person(self, payment_type):
        return False


@payment_operation(fallback=True)
@implementer(IPaymentOperation)
class InvalidPaymentOperation(object):
    """This operation will be used as a fallback for methods that wore removed
    from stoq, but may still exist in the database (they cannot be removed,
    since payments may have been created using that method).
    """

    description = _(u'Invalid payment')
    max_installments = 1

    #
    # IPaymentOperation
    #

    def pay_on_sale_confirm(self):
        return False

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

    def can_set_not_paid(self, payment):
        return True

    def print_(self, payments):
        pass

    def require_person(self, payment_type):
        return False
