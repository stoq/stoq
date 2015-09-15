# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source <http://www.async.com.br>
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

"""
This module contains classes centered around account, banks and transactions
between accounts.

The main class is an :class:`Account` holds a set of :class:`AccountTransaction`.

For accounts that are banks there's a :class:`BankAccount` class for
the bank specific state and for bill generation there's also
:class:`BillOption`.

Finally there's a :class:`AccountTransactionView` that is used by
the financial application to efficiently display a ledger.
"""

# pylint: enable=E1101

import datetime

from kiwi.currency import currency
from storm.expr import And, LeftJoin, Or
from storm.info import ClassAlias
from storm.references import Reference
from zope.interface import implementer

from stoqlib.database.expr import TransactionTimestamp, Date
from stoqlib.database.properties import (DateTimeCol, EnumCol, IdCol,
                                         IntCol, PriceCol, UnicodeCol)
from stoqlib.database.viewable import Viewable
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IDescribable
from stoqlib.domain.station import BranchStation
from stoqlib.exceptions import PaymentError
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class BillOption(Domain):
    """List of values for bill (boleto) generation

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/bill_option.html>`__
    """

    __storm_table__ = 'bill_option'

    #: option name, such as nosso_numero
    option = UnicodeCol()

    #: value of the option
    value = UnicodeCol()

    bank_account_id = IdCol()

    #: the |bankaccount| this option belongs to
    bank_account = Reference(bank_account_id, 'BankAccount.id')


class BankAccount(Domain):
    """Information specific to a bank

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/bank_account.html>`__
    """

    __storm_table__ = 'bank_account'

    account_id = IdCol()

    #: the |account| for this bank account
    account = Reference(account_id, 'Account.id')

    # FIXME: This is brazil specific, should probably be replaced by a
    #        bank reference to a separate class with name in addition to
    #        the bank number
    #: an identify for the bank type of this account,
    bank_number = IntCol(default=0)

    #: an identifier for the bank branch/agency which is responsible
    #: for this
    bank_branch = UnicodeCol(default=None)

    #: an identifier for this bank account
    bank_account = UnicodeCol(default=None)

    @property
    def options(self):
        """Get the bill options for this bank account
        :returns: a list of :class:`BillOption`
        """
        return self.store.find(BillOption,
                               bank_account=self)


@implementer(IDescribable)
class Account(Domain):
    """An account, a collection of |accounttransactions| that may be controlled
    by a bank.

    See also: `schema <http://doc.stoq.com.br/schema/tables/account.html>`__,
    `manual <http://doc.stoq.com.br/manual/account.html>`__
    """

    __storm_table__ = 'account'

    #: Bank
    TYPE_BANK = u'bank'

    #: Cash/Till
    TYPE_CASH = u'cash'

    #: Assets, like investement account
    TYPE_ASSET = u'asset'

    #: Credit
    TYPE_CREDIT = u'credit'

    #: Income/Salary
    TYPE_INCOME = u'income'

    #: Expenses
    TYPE_EXPENSE = u'expense'

    #: Equity, like unbalanced
    TYPE_EQUITY = u'equity'

    account_labels = {
        TYPE_BANK: (_(u"Deposit"), _(u"Withdrawal")),
        TYPE_CASH: (_(u"Receive"), _(u"Spend")),
        TYPE_ASSET: (_(u"Increase"), _(u"Decrease")),
        TYPE_CREDIT: (_(u"Payment"), _(u"Charge")),
        TYPE_INCOME: (_(u"Income"), _(u"Charge"),),
        TYPE_EXPENSE: (_(u"Rebate"), _(u"Expense")),
        TYPE_EQUITY: (_(u"Increase"), _(u"Decrease")),
    }

    account_type_descriptions = [
        (_(u"Bank"), TYPE_BANK),
        (_(u"Cash"), TYPE_CASH),
        (_(u"Asset"), TYPE_ASSET),
        (_(u"Credit"), TYPE_CREDIT),
        (_(u"Income"), TYPE_INCOME),
        (_(u"Expense"), TYPE_EXPENSE),
        (_(u"Equity"), TYPE_EQUITY),
    ]

    #: name of the account
    description = UnicodeCol(default=None)

    #: code which identifies the account
    code = UnicodeCol(default=None)

    #: parent account id, can be None
    parent_id = IdCol(default=None)

    #: parent account
    parent = Reference(parent_id, 'Account.id')

    station_id = IdCol(default=None)

    #: the |branchstation| tied
    #: to this account, mainly for TYPE_CASH accounts
    station = Reference(station_id, 'BranchStation.id')

    #: kind of account, one of the TYPE_* defines in this class
    account_type = EnumCol(allow_none=False, default=TYPE_BANK)

    #: |bankaccount| for this account, used by TYPE_BANK accounts
    bank = Reference('id', 'BankAccount.account_id', on_remote=True)

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.description

    #
    # Class Methods
    #

    @classmethod
    def get_by_station(cls, store, station):
        """Fetch the account assoicated with a station

        :param store: a store
        :param station: a |branchstation|
        :returns: the account
        """
        if station is None:
            raise TypeError("station cannot be None")
        if not isinstance(station, BranchStation):
            raise TypeError("station must be a BranchStation, not %r" %
                            (station, ))
        return store.find(cls, station=station).one()

    @classmethod
    def get_children_for(cls, store, parent):
        """Get a list of child accounts for

        :param store:
        :param |account| parent: parent account
        :returns: the child accounts
        :rtype: resultset
        """
        return store.find(cls, parent=parent)

    @classmethod
    def get_accounts(cls, store):
        """Get a list of all accounts

        :param store: a store
        :returns all accounts
        :rtype: resultset
        """
        return store.find(cls)

    #
    # Properties
    #

    @property
    def long_description(self):
        """Get a long description, including all the parent accounts,
        such as Tills:cotovia"""
        parts = []
        account = self
        while account:
            if not account in parts:
                parts.append(account)
                account = account.parent
        return u':'.join([a.description for a in reversed(parts)])

    @property
    def transactions(self):
        """Returns a list of transactions to this account.

        :returns: list of |accounttransaction|
        """
        return self.store.find(AccountTransaction,
                               Or(self.id == AccountTransaction.account_id,
                                  self.id == AccountTransaction.source_account_id))

    #
    # Public API
    #

    def get_total_for_interval(self, start, end):
        """Fetch total value for a given interval

        :param datetime start: beginning of interval
        :param datetime end: of interval
        :returns: total value or one
        """
        if not isinstance(start, datetime.datetime):
            raise TypeError("start must be a datetime.datetime, not %s" % (
                type(start), ))
        if not isinstance(end, datetime.datetime):
            raise TypeError("end must be a datetime.datetime, not %s" % (
                type(end), ))

        query = And(Date(AccountTransaction.date) >= start,
                    Date(AccountTransaction.date) <= end,
                    AccountTransaction.source_account_id != AccountTransaction.account_id)

        transactions = self.store.find(AccountTransaction, query)
        incoming = transactions.find(AccountTransaction.account_id == self.id)
        outgoing = transactions.find(AccountTransaction.source_account_id == self.id)

        positive_values = incoming.sum(AccountTransaction.value) or 0
        negative_values = outgoing.sum(AccountTransaction.value) or 0

        return currency(positive_values - negative_values)

    def can_remove(self):
        """If the account can be removed.
        Not all accounts can be removed, some are internal to Stoq
        and cannot be removed"""
        # Can't remove accounts that are used in a parameter
        if (sysparam.compare_object('IMBALANCE_ACCOUNT', self) or
            sysparam.compare_object('TILLS_ACCOUNT', self) or
            sysparam.compare_object('BANKS_ACCOUNT', self)):
            return False

        # Can't remove station accounts
        if self.station:
            return False

        # When we remove this Account, all the related AccountTransaction will
        # be assigned to the IMBALANCE_ACCOUNT and BankAccount will be removed,
        # so we need to skip them here
        return super(Account, self).can_remove(
            skip=[('account_transaction', 'account_id'),
                  ('account_transaction', 'source_account_id'),
                  ('bank_account', 'account_id')])

    def remove(self, store):
        """Remove the current account. This updates all transactions which
        refers to this account and removes them.

        :param store: a store
        """
        if not self.can_remove():
            raise TypeError("Account %r cannot be removed" % (self, ))

        imbalance_account_id = sysparam.get_object_id('IMBALANCE_ACCOUNT')

        for transaction in store.find(AccountTransaction,
                                      account=self):
            transaction.account_id = imbalance_account_id
            store.flush()

        for transaction in store.find(AccountTransaction,
                                      source_account=self):
            transaction.source_account_id = imbalance_account_id
            store.flush()

        bank = self.bank
        if bank:
            for option in bank.options:
                store.remove(option)
            store.remove(bank)

        self.store.remove(self)

    def has_child_accounts(self):
        """If this account has child accounts

        :returns: True if any other accounts has this account as a parent"""
        return not self.store.find(Account, parent=self).is_empty()

    def get_type_label(self, out):
        """Returns the label to show for the increases/decreases
        for transactions of this account.
        See :obj:`~..account_labels`

        :param out: if the transaction is going out
        """
        return self.account_labels[self.account_type][int(out)]

    def matches(self, account_id):
        """Check if this account or it's parent account is the same
        as another account id.

        :param account_id: the account id to compare with
        :returns: if the accounts matches.
        """
        if self.id == account_id:
            return True
        if self.parent_id and self.parent_id == account_id:
            return True
        return False


class AccountTransaction(Domain):
    """Transaction between two accounts.

    A transaction is a transfer of money from the
    :obj:`~.source_account` to the
    :obj:`~.account`.

    It removes a negative amount of money from the source and increases
    the account by the same amount.
    There's only one value, but depending on the view it's either negative
    or positive, it can never be zero though.
    A transaction can optionally be tied to a |payment|

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/account_transaction.html>`__
    `manual <http://doc.stoq.com.br/manual/transaction.html>`__

    """

    __storm_table__ = 'account_transaction'

    # operation_type values
    TYPE_IN = u'in'
    TYPE_OUT = u'out'

    # FIXME: It's way to tricky to calculate the direction and it's
    #        values for an AccountTransaction due to the fact that
    #        we're only store one value. We should store two values,
    #        one for how much the current account should be increased
    #        with and another one which is how much the other account
    #        should be increased with. For split transaction we might
    #        want to store more values, so it might make sense to allow
    #        N values per transaction.

    account_id = IdCol()

    #: destination |account|
    account = Reference(account_id, 'Account.id')

    source_account_id = IdCol()

    #: source |account|
    source_account = Reference(source_account_id, 'Account.id')

    #: short human readable summary of the transaction
    description = UnicodeCol()

    #: identifier of this transaction within a account
    code = UnicodeCol()

    #: value transfered
    value = PriceCol(default=0)

    #: date the transaction was done
    date = DateTimeCol()

    payment_id = IdCol(default=None)

    #: |payment| this transaction relates to, can also be ``None``
    payment = Reference(payment_id, 'Payment.id')

    #: operation_type represents the type of transaction (debit/credit)
    operation_type = EnumCol(allow_none=False, default=TYPE_IN)

    class sqlmeta:
        lazyUpdate = True

    @classmethod
    def get_inverted_operation_type(cls, operation_type):
        """ Get the inverted operation_type (IN->OUT / OUT->IN)

        :param operation_type: the type of transaction
        :returns: the inverted transaction type
        """
        if operation_type == cls.TYPE_IN:
            return cls.TYPE_OUT
        return cls.TYPE_IN

    @classmethod
    def create_from_payment(cls, payment, code=None,
                            source_account=None, destination_account=None):
        """Create a new transaction based on a |payment|.
        It's normally used when creating a transaction which represents
        a payment, for instance when you receive a bill or a check from
        a |client| which will enter a |bankaccount|.

        :param payment: the |payment| to create the transaction for.
        :param code: the code for the transaction. If not provided,
            the payment identifier will be used by default
        :param source_account: the source |account| for the transaction.
        :param destination_account: the destination |account| for the transaction.
        :returns: the transaction
        """
        if not payment.is_paid():
            raise PaymentError(_("Payment needs to be paid"))
        store = payment.store
        value = payment.paid_value
        if payment.is_outpayment():
            operation_type = cls.TYPE_OUT
            source = source_account or payment.method.destination_account
            destination = (destination_account or
                           sysparam.get_object(store, 'IMBALANCE_ACCOUNT'))
        else:
            operation_type = cls.TYPE_IN
            source = (source_account or
                      sysparam.get_object(store, 'IMBALANCE_ACCOUNT'))
            destination = (destination_account or
                           payment.method.destination_account)

        code = code if code is not None else unicode(payment.identifier)
        return cls(source_account=source,
                   account=destination,
                   value=value,
                   description=payment.description,
                   code=code,
                   date=payment.paid_date,
                   store=store,
                   payment=payment,
                   operation_type=operation_type)

    def create_reverse(self):
        """Reverse this transaction, this happens when a payment
        is set as not paid.

        :returns: the newly created account transaction representing
           the reversal
        """

        # We're effectively canceling the old transaction here,
        # to avoid having more than one transaction referencing the same
        # payment we reset the payment to None.
        #
        # It would be nice to have all of them reference the same payment,
        # but it makes it harder to create the reversal.

        self.payment = None
        new_type = self.get_inverted_operation_type(self.operation_type)
        return AccountTransaction(
            source_account=self.account,
            account=self.source_account,
            value=self.value,
            description=_(u"Reverted: %s") % (self.description),
            code=self.code,
            date=TransactionTimestamp(),
            store=self.store,
            payment=None,
            operation_type=new_type)

    def invert_transaction_type(self):
        """ Invert source/destination accounts and operation_type

        When change a incoming transaction to outgoing or vice-versa. The source and
        destination accounts must be inverted. Thus, the outgoing value always
        will belong to the source account.
        """
        temp_account = self.account
        operation_type = self.operation_type

        self.account = self.source_account
        self.source_account = temp_account
        self.operation_type = self.get_inverted_operation_type(operation_type)

    def get_other_account(self, account):
        """Get the other end of a transaction

        :param account: an |account|
        :returns: the other end
        """
        if self.source_account == account:
            return self.account
        elif self.account == account:
            return self.source_account
        else:
            raise AssertionError

    def set_other_account(self, other, account):
        """Set the other end of a transaction

        :param other: an |account| which we do not want to set
        :param account: the |account| to set
        """
        other = self.store.fetch(other)
        if self.source_account == other:
            self.account = account
        elif self.account == other:
            self.source_account = account
        else:
            raise AssertionError


class AccountTransactionView(Viewable):
    """AccountTransactionView provides a fast view
    of the transactions tied to a specific |account|.

    It's mainly used to show a ledger.
    """
    Account_Dest = ClassAlias(Account, 'account_dest')
    Account_Source = ClassAlias(Account, 'account_source')

    transaction = AccountTransaction

    id = AccountTransaction.id
    code = AccountTransaction.code
    description = AccountTransaction.description
    value = AccountTransaction.value
    date = AccountTransaction.date
    operation_type = AccountTransaction.operation_type

    dest_account_id = Account_Dest.id
    dest_account_description = Account_Dest.description

    source_account_id = Account_Source.id
    source_account_description = Account_Source.description

    tables = [
        AccountTransaction,
        LeftJoin(Account_Dest,
                 AccountTransaction.account_id == Account_Dest.id),
        LeftJoin(Account_Source,
                 AccountTransaction.source_account_id == Account_Source.id),
    ]

    @classmethod
    def get_for_account(cls, account, store):
        """Get all transactions for this |account|, see Account.transaction"""
        return store.find(cls, Or(account.id == AccountTransaction.account_id,
                                  account.id == AccountTransaction.source_account_id))

    def get_account_description(self, account):
        """Get description of the other |account|, eg.
        the one which is transfered to/from.
        """
        if self.source_account_id == account.id:
            return self.dest_account_description
        elif self.dest_account_id == account.id:
            return self.source_account_description
        else:
            raise AssertionError

    def get_value(self, account):
        """ Gets the transaction value according to an |account|.

        If this |account| is the source, the value returned will be negative.
        Representing a outgoing transaction.
        """
        # A transaction that was not adjusted, will have the source equals
        # to destination account. So get the value based on operation type.
        if self.source_account_id == self.dest_account_id:
            return self.get_value_by_type()
        elif self.source_account_id == account.id:
            return -self.value
        else:
            return self.value

    def get_value_by_type(self):
        """ Returns the transaction value, based on operation type.
        """
        if self.operation_type == AccountTransaction.TYPE_IN:
            return self.value
        else:
            return -self.value
