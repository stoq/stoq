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

import decimal
import gettext

from stoqlib.domain.account import Account, AccountTransaction
from stoqlib.importers.csvimporter import CSVImporter


class AccountTransactionImporter(CSVImporter):
    fields = ['parent_source',
              'source',
              'parent_dest',
              'dest',
              'date',
              'code',
              'description',
              'value',
              ]

    def _get_account(self, trans, parent_name, account_name):
        parent = None
        if parent_name:
            parent = Account.selectOneBy(description=gettext.gettext(parent_name),
                                         connection=trans)

        account = Account.selectOneBy(parent=parent,
                                      description=gettext.gettext(account_name),
                                      connection=trans)
        if account is None:
            raise ValueError("Missing account; %s:%s" % (parent_name,
                                                         account_name))
        return account

    def process_one(self, data, fields, trans):
        source = self._get_account(trans, data.parent_source, data.source)
        dest = self._get_account(trans, data.parent_dest, data.dest)

        AccountTransaction(account=dest,
                           source_account=source,
                           description=data.description,
                           value=decimal.Decimal(data.value),
                           date=self.parse_date(data.date),
                           code=data.code,
                           connection=trans)
