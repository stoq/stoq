# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2011 Async Open Source <http://www.async.com.br>
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
""" Domain classes to manage accounts """

from zope.interface import implements

from stoqlib.database.orm import PriceCol
from stoqlib.database.orm import ForeignKey, IntCol, UnicodeCol
from stoqlib.database.orm import DateTimeCol
from stoqlib.database.orm import OR, SingleJoin
from stoqlib.database.orm import Viewable, Alias, LEFTJOINOn
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IDescribable, IOutPayment
from stoqlib.domain.station import BranchStation
from stoqlib.exceptions import PaymentError
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class BillOption(Domain):
    option = UnicodeCol()
    value = UnicodeCol()
    bank_account = ForeignKey('BankAccount')


class BankAccount(Domain):
    """Information specific to a bank

    @ivar bank_branch: the bank branch where this account lives.
    @ivar bank_account: an identifier of this account in the branch.
    """
    account = ForeignKey('Account', default=None)

    bank_number = IntCol(default=0)
    bank_branch = UnicodeCol(default=None)
    bank_account = UnicodeCol(default=None)

    @property
    def options(self):
        return BillOption.selectBy(connection=self.get_connection(),
                                   bank_account=self)


class Account(Domain):
    """An account, a collection of transactions

    @ivar description: name of the account in Stoq
    @ivar code: code which identifies the account
    @ivar parent: parent account, can be None
    @ivar station: for accounts connected to a specific station or None
    """

    (TYPE_BANK,
     TYPE_CASH,
     TYPE_ASSET,
     TYPE_CREDIT,
     TYPE_INCOME,
     TYPE_EXPENSE,
     TYPE_EQUITY) = range(7)

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

    description = UnicodeCol(default=None)
    code = UnicodeCol(default=None)
    parent = ForeignKey('Account', default=None)
    station = ForeignKey('BranchStation', default=None)
    account_type = IntCol(default=None)
    bank = SingleJoin('BankAccount')

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
        @param conn: a connection
        @param station: a BranchStation
        Returns: the account
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
        Returns: list of AccountTransaction
        """
        return AccountTransaction.select(
            OR(self.id == AccountTransaction.q.accountID,
               self.id == AccountTransaction.q.source_accountID),
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
        @param: a transaction
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

        self.delete(self.id, connection=trans)

    def has_child_accounts(self):
        """@returns: True if any other accounts has this account as a parent"""
        return bool(Account.selectBy(connection=self.get_connection(),
                                     parent=self))

    def get_type_label(self, out):
        """Returns the label to show for the increases/decreases
        for transactions of this account.
        @param out: if the transaction is going out
        """
        return self.account_labels[self.account_type][int(out)]

    def matches(self, account_id):
        if self.id == account_id:
            return True
        if self.parentID and self.parentID == account_id:
            return True
        return False


class AccountTransaction(Domain):
    """Transaction between two accounts.

    A transaction is a transfer of money from the @source_account
    to the @account. It removes a negative amount of money from the source
    and increases the account by the same amount.
    There's only one value, but depending on the view it's either negative
    or positive, it can never be zero though.
    A transaction can optionally be tied to a Payment

    @ivar account: destination account
    @ivar source_account: source account
    @ivar description: short human readable summary of the transaction
    @ivar code: identifier of this transaction within a account
    @ivar value: value transfered, positive for credit, negative for debit
    @ivar date: date the transaction was done
    @ivar payment: payment this transaction relates to, can be None
    """

    # FIXME: It's way to tricky to calculate the direction and it's
    #        values for an AccountTransaction due to the fact that
    #        we're only store one value. We should store two values,
    #        one for how much the current account should be increased
    #        with and another one which is how much the other account
    #        should be increased with. For split transaction we might
    #        want to store more values, so it might make sense to allow
    #        N values per transaction.

    account = ForeignKey('Account')
    source_account = ForeignKey('Account')
    description = UnicodeCol()
    code = UnicodeCol()
    value = PriceCol(default=0)
    date = DateTimeCol()
    payment = ForeignKey('Payment', default=None)

    class sqlmeta:
        lazyUpdate = True

    @classmethod
    def create_from_payment(cls, payment, account=None):
        """Create a new transaction based on a payment.
        It's normally used when creating a transaction which represents
        a payment, for instance when you receive a bill or a check from
        a client which will enter a bank account.
        @payment: the payment to create the transaction for.
        @account: account where this payment will arrive
        @returns: the transaction
        """
        if not payment.is_paid():
            raise PaymentError(_("Payment needs to be paid"))
        trans = payment.get_connection()
        value = payment.paid_value
        if IOutPayment(payment, None):
            value = -value
        return cls(source_account=sysparam(trans).IMBALANCE_ACCOUNT,
                   account=account or payment.method.destination_account,
                   value=value,
                   description=payment.description,
                   code=str(payment.id),
                   date=payment.paid_date,
                   connection=trans,
                   payment=payment)

    def get_other_account(self, account):
        """Get the other end of a transaction
        @param account: an account
        @returns: the other end
        """
        if self.source_account == account:
            return self.account
        elif self.account == account:
            return self.source_account
        else:
            raise AssertionError

    def set_other_account(self, other, account):
        """Set the other end of a transaction
        @param other: an account which we do not want to set
        @param account: the account to set
        """
        if self.source_account == other:
            self.account = account
        elif self.account == other:
            self.source_account = account
        else:
            raise AssertionError


class AccountTransactionView(Viewable):
    """AccountTransactionView provides a fast view
    of the transactions tied to a specific account.

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
        dest_accountID=Account_Dest.q.id,
        dest_account_description=Account_Dest.q.description,
        source_accountID=Account_Source.q.id,
        source_account_description=Account_Source.q.description,
        )

    joins = [
        LEFTJOINOn(None, Account_Dest,
                   AccountTransaction.q.accountID == Account_Dest.q.id),
        LEFTJOINOn(None, Account_Source,
                   AccountTransaction.q.source_accountID == Account_Source.q.id),
    ]

    @classmethod
    def get_for_account(cls, account, conn):
        """Get all transactions for this account, see Account.transaction"""
        return cls.select(
            OR(account.id == AccountTransaction.q.accountID,
               account.id == AccountTransaction.q.source_accountID),
            connection=conn)

    def get_account_description(self, account):
        """Get description of the other account, eg.
        the one which is transfered to/from.
        """
        if self.source_accountID == account.id:
            return self.dest_account_description
        elif self.dest_accountID == account.id:
            return self.source_account_description
        else:
            raise AssertionError

    def get_value(self, account):
        """Gets the value for this account.
        For destination accounts this will be negative
        """
        if self.dest_accountID == account.id:
            return self.value
        else:
            return -self.value

    @property
    def transaction(self):
        """Get the AccountTransaction for this view"""
        return AccountTransaction.get(self.id, self.get_connection())
