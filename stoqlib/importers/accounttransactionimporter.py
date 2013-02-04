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

from stoqlib.domain.account import Account, AccountTransaction
from stoqlib.importers.csvimporter import CSVImporter
from stoqlib.lib.translation import stoqlib_gettext as _


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

    def _get_account(self, store, parent_name, account_name):
        parent = None
        if parent_name:
            parent = store.find(Account,
                                description=_(parent_name)).one()

        account = store.find(Account, parent=parent,
                             description=_(account_name)).one()
        if account is None:
            raise ValueError("Missing account; %s:%s" % (parent_name,
                                                         account_name))
        return account

    def process_one(self, data, fields, store):
        source = self._get_account(store, data.parent_source, data.source)
        dest = self._get_account(store, data.parent_dest, data.dest)

        AccountTransaction(account=dest,
                           source_account=source,
                           description=data.description,
                           value=decimal.Decimal(data.value),
                           date=self.parse_date(data.date),
                           code=data.code,
                           store=store)
