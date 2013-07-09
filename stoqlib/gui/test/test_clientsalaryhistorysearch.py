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
## GNU Lesser General Public License for more details.  ##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import datetime

from stoqlib.domain.person import ClientSalaryHistory, LoginUser
from stoqlib.gui.search.clientsalaryhistorysearch import (
    ClientSalaryHistorySearch)
from stoqlib.gui.test.uitestutils import GUITest


class TestClientSalaryHistorySearch(GUITest):
    def test_search(self):
        client = self.create_client()

        users = self.store.find(LoginUser).order_by(LoginUser.username)
        user_a = users[0]
        user_b = users[1]

        ClientSalaryHistory(date=datetime.datetime(2012, 1, 1),
                            new_salary=1000,
                            old_salary=0,
                            client=client,
                            user=user_a,
                            store=self.store)
        ClientSalaryHistory(date=datetime.datetime(2012, 2, 2),
                            new_salary=2000,
                            old_salary=1000,
                            client=client,
                            user=user_b,
                            store=self.store)
        ClientSalaryHistory(date=datetime.datetime(2012, 3, 3),
                            new_salary=3000,
                            old_salary=2000,
                            client=client,
                            user=user_a,
                            store=self.store)

        search = ClientSalaryHistorySearch(self.store, client)

        search.search.refresh()
        self.check_search(search, 'client-salary-history-no-filter')

        search.set_searchbar_search_string('ad')
        search.search.refresh()
        self.check_search(search, 'client-salary-history-string-filter')
