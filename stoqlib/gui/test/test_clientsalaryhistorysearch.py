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

from stoqlib.gui.uitestutils import GUITest
from stoqlib.domain.person import ClientSalaryHistory, LoginUser
from stoqlib.gui.search.clientsalaryhistorysearch import (
                                                    ClientSalaryHistorySearch)


class TestClientSalaryHistorySearch(GUITest):
    def testSearch(self):
        client = self.create_client()

        user_a = LoginUser.selectOneBy(id=1, connection=self.trans)
        user_b = LoginUser.selectOneBy(id=2, connection=self.trans)

        ClientSalaryHistory(date=datetime.datetime(2012, 1, 1),
                            new_salary=1000,
                            old_salary=0,
                            client=client,
                            user=user_a,
                            connection=self.trans)
        ClientSalaryHistory(date=datetime.datetime(2012, 2, 2),
                            new_salary=2000,
                            old_salary=1000,
                            client=client,
                            user=user_b,
                            connection=self.trans)
        ClientSalaryHistory(date=datetime.datetime(2012, 3, 3),
                            new_salary=3000,
                            old_salary=2000,
                            client=client,
                            user=user_a,
                            connection=self.trans)

        search = ClientSalaryHistorySearch(self.trans, client)

        search.search.refresh()
        self.check_search(search, 'client-salary-history-no-filter')

        search.set_searchbar_search_string('ad')
        search.search.refresh()
        self.check_search(search, 'client-salary-history-string-filter')
