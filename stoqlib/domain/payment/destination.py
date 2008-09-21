# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2008 Async Open Source <http://www.async.com.br>
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
##              Johan Dahlin               <jdahlin@async.com.br>
##
""" Payment destination management implementations. """

from sqlobject import UnicodeCol, ForeignKey
from zope.interface import implements

from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IDescribable

#
# Domain Classes
#

class PaymentDestination(Domain):
    """PaymentDestination is the location where all the paid payments live.

    @ivar description: an easy identification for this payment
        destination.
    @ivar account: if this payment destination represents a bank account,
        use it here.
    """
    implements(IDescribable)

    description = UnicodeCol()
    account = ForeignKey('BankAccount', default=None)
    notes = UnicodeCol(default='')
    branch = ForeignKey('PersonAdaptToBranch')

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.description
