# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005,2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito     <evandro@async.com.br>
##
""" Payment destination management implementations. """

from sqlobject import UnicodeCol, ForeignKey
from zope.interface import implements

from stoqlib.domain.base import InheritableModel
from stoqlib.domain.interfaces import IDescribable

#
# Domain Classes
#

class PaymentDestination(InheritableModel):
    """PaymentDestination is the location where all the paid payments live.

    B{Important attributes}:
        - I{description}: an easy identification for this payment
                          destination.
        - I{account}: if this payment destination represents a bank account,
                      use it here.
    """
    implements(IDescribable)

    description = UnicodeCol()
    account = ForeignKey('BankAccount', default=None)
    notes = UnicodeCol(default='')

    def get_balance(self, start_date=None, end_date=None):
        raise NotImplementedError

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.description

class StoreDestination(PaymentDestination):
    """A StoreDestination is a payment destination which lives in a Store.
    Most of times this will represent the total value of operations in this
    store.

    B{Importante attributes}:
        - I{branch}: the store itself.
    """
    _inheritable = False
    branch = ForeignKey('PersonAdaptToBranch')


class BankDestination(PaymentDestination):
    """A Bank Destination is a payment destination which lives in a bank.

    B{Importante attributes}:
        - I{branch}: the bank branch where all the paid payments are send
                     to.
    """
    _inheritable = False
    branch = ForeignKey('PersonAdaptToBankBranch')
