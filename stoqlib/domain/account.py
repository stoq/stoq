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
""" Domain classes to manage bank accounts """

from sqlobject import UnicodeCol, IntCol

from stoqlib.domain.base import Domain

#
# Base Domain Classes
#

class Bank(Domain):
    """A definition of a bank. A bank can have many branches associated with
    it.

    B{Important attributes}:
        - I{name}: the name of the bank.
        - I{short_name}: a short idenfier for the bank.
        - I{compensation_code}: some financial operations require this code.
                                It is specific for each bank.
    """
    name = UnicodeCol()
    short_name = UnicodeCol()
    compensation_code = UnicodeCol()

class BankAccount(Domain):
    """A bank account definition.

    B{Important atributes}:
        - I{bank_id}: the bank id.
        - I{branch}: the bank branch where this account lives.
        - I{account}: an identifier of this account in the branch.
    """
    bank_id = IntCol(default=0)
    branch = UnicodeCol(default=None)
    account = UnicodeCol(default=None)

