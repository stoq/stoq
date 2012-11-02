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

from zope.interface import implements

from stoqlib.database.orm import PriceCol
from stoqlib.database.orm import ForeignKey, IntCol, UnicodeCol
from stoqlib.database.orm import DateTimeCol
from stoqlib.database.orm import OR, SingleJoin
from stoqlib.database.orm import Viewable, Alias, LeftJoin
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

    #: option name, such as nosso_numero
    option = UnicodeCol()

    #: value of the option
    value = UnicodeCol()

    #: the |bankaccount| this option belongs to
    bank_account = ForeignKey('BankAccount')


class BankAccount(Domain):
    """Information specific to a bank

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/bank_account.html>`__
    """

    #: the |account| for this bank account
    account = ForeignKey('Account', default=None)

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
        return BillOption.selectBy(connection=self.get_connection(),
                                   bank_account=self)


class Account(Domain):
    """An account, a collection of |accounttransactions| that may be controlled
    by a bank.

    See also: `schema <http://doc.stoq.com.br/schema/tables/account.html>`__,
    `manual <http://doc.stoq.com.br/manual/account.html>`__
    """

    #: Bank
    TYPE_BANK = 0

    #: Cash/Till
    TYPE_CASH = 1

    #: Assets, like investement account
    TYPE_ASSET = 2

    #: Credit
    TYPE_CREDIT = 3

    #: Income/Salary
    TYPE_INCOME = 4

    #: Expenses
    TYPE_EXPENSE = 5

    #: Equity, like unbalanced
    TYPE_EQUITY = 6

    account_labels = {
        TYPE_BANK: (_("Deposit"), _("Withdrawal")),
        TYPE_CASH: (_("Receive"), _("Spend")),
        TYPE_ASSET: (_("Increase"), _("Decrease")),
        TYPE_CREDIT: (_("Payment"), _("Charge")),
        TYPE_INCOME: (_("Charge"), _("Income")),
        TYPE_EXPENSE: (_("Expense"), _("Rebate")),
        TYPE_EQUITY: (_("Increase"), _("Decrease")),
    }

    account_type_descriptions = [
        (_("Bank"), TYPE_BANK),
        (_("Cash"), TYPE_CASH),
        (_("Asset"), TYPE_ASSET),
        (_("Credit"), TYPE_CREDIT),
        (_("Income"), TYPE_INCOME),
        (_("Expense"), TYPE_EXPENSE),
        (_("Equity"), TYPE_EQUITY),
        ]

    implements(IDescribable)

    #: name of the account
    description = UnicodeCol(default=None)

    #: code which identifies the account
    code = UnicodeCol(default=None)

    #: parent account, can be None
    parent = ForeignKey('Account', default=None)

    #: the |branchstation| tied
    #: to this account, mainly for TYPE_CASH accounts
    station = ForeignKey('BranchStation', default=None)

    #: kind of account, one of the TYPE_* defines in this class
    account_type = IntCol(default=None)

    #: |bankaccount| for this account, used by TYPE_BANK accounts
    bank = SingleJoin('BankAccount', joinColumn='account_id')

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.description

    #
    # Public API
    #

    @classmethod
    def get_by_station(cls, conn, station):
        """Fetch the account assoicated with a station

        :param conn: a connection
        :param station: a |branchstation|
        :returns: the account
        """
        if station is None:
            raise TypeError("station cannot be None")
        if not isinstance(station, BranchStation):
            raise TypeError("station must be a BranchStation, not %r" %
                    (station, ))
        return cls.selectOneBy(connection=conn, station=station)

    @property
    def long_description(self):
        """Get a long description, including all the parent accounts,
        such as Tills:cotovia"""
        parts = []
        account = self
        while account:
            parts.append(account.description)
            account = account.parent
        return ':'.join(reversed(parts))

    @property
    def transactions(self):
        """Returns a list of transactions to this account.

        :returns: list of |accounttransaction|
        """
        return AccountTransaction.select(
            OR(self.id == AccountTransaction.q.account_id,
               self.id == AccountTransaction.q.source_account_id),
            connection=self.get_connection())

    def can_remove(self):
        """If the account can be removed.
        Not all accounts can be removed, some are internal to Stoq
        and cannot be removed"""
        # Can't remove accounts that are used in a parameter
        sparam = sysparam(self.get_connection())
        if self in [sparam.IMBALANCE_ACCOUNT,
                    sparam.TILLS_ACCOUNT,
                    sparam.BANKS_ACCOUNT]:
            return False

        # Can't remove station accounts
        if self.station:
            return False

        # Can't remove an account which has children
        if self.has_child_accounts():
            return False

        return True

    def remove(self, trans):
        """Remove the current account. This updates all transactions which
        refers to this account and removes them.

        :param: a transaction
        """
        if not self.can_remove():
            raise TypeError("Account %r cannot be removed" % (self, ))

        imbalance_account = sysparam(trans).IMBALANCE_ACCOUNT

        for transaction in AccountTransaction.selectBy(
            connection=trans,
            account=self):
            transaction.account = imbalance_account
            transaction.sync()

        for transaction in AccountTransaction.selectBy(
            connection=trans,
            source_account=self):
            transaction.source_account = imbalance_account
            transaction.sync()

        bank = self.bank
        if bank:
            for options in bank.options:
                options.delete(options.id, connection=trans)
            bank.delete(bank.id, connection=trans)

        self.delete(self.id, connection=trans)

    def has_child_accounts(self):
        """If this account has child accounts

        :returns: True if any other accounts has this account as a parent"""
        return bool(Account.selectBy(connection=self.get_connection(),
                                     parent=self))

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

    # FIXME: It's way to tricky to calculate the direction and it's
    #        values for an AccountTransaction due to the fact that
    #        we're only store one value. We should store two values,
    #        one for how much the current account should be increased
    #        with and another one which is how much the other account
    #        should be increased with. For split transaction we might
    #        want to store more values, so it might make sense to allow
    #        N values per transaction.

    #: destination |account|
    account = ForeignKey('Account')

    #: source |account|
    source_account = ForeignKey('Account')

    #: short human readable summary of the transaction
    description = UnicodeCol()

    #: identifier of this transaction within a account
    code = UnicodeCol()

    #: value transfered, positive for credit, negative for debit
    value = PriceCol(default=0)

    #: date the transaction was done
    date = DateTimeCol()

    #: |payment| this transaction relates to, can also be ``None``
    payment = ForeignKey('Payment', default=None)

    class sqlmeta:
        lazyUpdate = True

    @classmethod
    def create_from_payment(cls, payment, account=None):
        """Create a new transaction based on a |payment|.
        It's normally used when creating a transaction which represents
        a payment, for instance when you receive a bill or a check from
        a |client| which will enter a |bankaccount|.

        :param payment: the |payment| to create the transaction for.
        :param account: |account| where this transaction will arrive,
          or ``None``
        :returns: the transaction
        """
        if not payment.is_paid():
            raise PaymentError(_("Payment needs to be paid"))
        trans = payment.get_connection()
        value = payment.paid_value
        if payment.is_outpayment():
            value = -value
        return cls(source_account=sysparam(trans).IMBALANCE_ACCOUNT,
                   account=account or payment.method.destination_account,
                   value=value,
                   description=payment.description,
                   code=str(payment.identifier),
                   date=payment.paid_date,
                   connection=trans,
                   payment=payment)

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
        other = self.get_connection().get(other)
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
    Account_Dest = Alias(Account, 'account_dest')
    Account_Source = Alias(Account, 'account_source')

    columns = dict(
        id=AccountTransaction.q.id,
        code=AccountTransaction.q.code,
        description=AccountTransaction.q.description,
        value=AccountTransaction.q.value,
        date=AccountTransaction.q.date,
        dest_account_id=Account_Dest.q.id,
        dest_account_description=Account_Dest.q.description,
        source_account_id=Account_Source.q.id,
        source_account_description=Account_Source.q.description,
        )

    joins = [
        LeftJoin(Account_Dest,
                   AccountTransaction.q.account_id == Account_Dest.q.id),
        LeftJoin(Account_Source,
                   AccountTransaction.q.source_account_id == Account_Source.q.id),
    ]

    @classmethod
    def get_for_account(cls, account, conn):
        """Get all transactions for this |account|, see Account.transaction"""
        return cls.select(
            OR(account.id == AccountTransaction.q.account_id,
               account.id == AccountTransaction.q.source_account_id),
            connection=conn)

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
        """Gets the value for this |account|.
        For a destination |account| this will be negative
        """
        if self.dest_account_id == account.id:
            return self.value
        else:
            return -self.value

    @property
    def transaction(self):
        """Get the AccountTransaction for this view"""
        return AccountTransaction.get(self.id, self.get_connection())
