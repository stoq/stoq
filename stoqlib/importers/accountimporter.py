# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

import gettext

from stoqlib.api import api
from stoqlib.domain.account import Account, BankAccount
from stoqlib.importers.csvimporter import CSVImporter


class AccountImporter(CSVImporter):
    fields = ['parent_account',
              'description',
              'account_type',
              'bank_number',
              'bank_branch',
              'bank_account']

    def process_one(self, data, fields, trans):
        if data.parent_account:
            name = gettext.gettext(data.parent_account)
            parent = Account.selectOneBy(description=name,
                                         connection=trans)
        else:
            parent = None
        account = Account(description=data.description,
                          parent=parent,
                          code=None,
                          station=api.get_current_station(trans),
                          account_type=int(data.account_type),
                          connection=trans)

        if data.bank_number:
            BankAccount(account=account,
                        bank_account=data.bank_account,
                        bank_number=int(data.bank_number),
                        bank_branch=data.bank_branch,
                        connection=trans)
