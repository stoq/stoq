# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from stoqlib.domain.account import Account
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.migration.parameter import get_parameter


class ParameterTest(DomainTest):
    def test_get_existent_parameter(self):
        imbalance = self.store.find(Account,
                                    description=u'Imbalance').one()
        account = get_parameter(self.store, u'IMBALANCE_ACCOUNT')

        self.assertEquals(imbalance.id, unicode(account))

    def test_get_nonexistent_parameter(self):
        account = get_parameter(self.store, u'NONEXISTENT PARAMETER')
        self.assertEquals(account, None)
