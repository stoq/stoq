# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

import datetime

from stoqlib.gui.uitestutils import GUITest
from stoqlib.domain.commission import Commission
from stoqlib.domain.person import SalesPerson, Person
from stoqlib.gui.search.commissionsearch import CommissionSearch


class TestCommissionSearch(GUITest):
    def testSearch(self):
        self.clean_domain([Commission])

        person = Person.selectOneBy(name='Deivis Alexandre Junior',
                                    connection=self.trans)
        salesperson = SalesPerson.selectOneBy(person=person,
                                              connection=self.trans)
        sale = self.create_sale()
        sale.identifier = 74521
        sale.open_date = datetime.datetime(2012, 1, 1)
        Commission(salesperson=salesperson,
                   sale=sale,
                   payment=self.create_payment(),
                   connection=self.trans)

        person = Person.selectOneBy(name='Maria Aparecida Ardana',
                                    connection=self.trans)
        salesperson = SalesPerson.selectOneBy(person=person,
                                              connection=self.trans)
        sale = self.create_sale()
        sale.identifier = 85412
        sale.open_date = datetime.datetime(2012, 2, 2)
        Commission(salesperson=salesperson,
                   sale=sale,
                   payment=self.create_payment(),
                   connection=self.trans)

        search = CommissionSearch(self.trans)

        search.search.refresh()
        self.check_search(search, 'commission-no-filter')

        search.set_searchbar_search_string('dei')
        search.search.refresh()
        self.check_search(search, 'commission-string-filter')

        search.set_searchbar_search_string('')
        search._salesperson_filter.set_state('Maria Aparecida Ardana')
        search.search.refresh()
        self.check_search(search, 'commission-salesperson-filter')
