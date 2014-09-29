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

from stoqlib.api import api
from stoqlib.domain.commission import Commission
from stoqlib.domain.person import Person
from stoqlib.gui.search.commissionsearch import CommissionSearch
from stoqlib.gui.search.searchfilters import DateSearchFilter
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localdatetime, localdate


class TestCommissionSearch(GUITest):
    def test_search(self):
        self.clean_domain([Commission])

        person = self.store.find(Person, name=u'Deivis Alexandre Junior').one()
        salesperson = person.sales_person
        sale = self.create_sale()
        sale.identifier = 74521
        sale.open_date = localdatetime(2012, 1, 1)
        sale.confirm_date = localdatetime(2012, 1, 10)
        sale.salesperson = salesperson
        payment = self.create_payment()
        payment.paid_date = localdatetime(2012, 1, 15)
        Commission(sale=sale,
                   payment=payment,
                   store=self.store)

        person = self.store.find(Person, name=u'Maria Aparecida Ardana').one()
        salesperson = person.sales_person
        sale = self.create_sale()
        sale.identifier = 85412
        sale.open_date = localdatetime(2012, 2, 2)
        sale.confirm_date = localdatetime(2012, 2, 10)
        sale.salesperson = salesperson
        payment = self.create_payment()
        payment.paid_date = localdatetime(2012, 2, 15)
        Commission(sale=sale,
                   payment=payment,
                   store=self.store)

        # First check for columns getting the confirm date of the sale
        api.sysparam.set_bool(self.store,
                              'SALE_PAY_COMMISSION_WHEN_CONFIRMED',
                              True)
        search = CommissionSearch(self.store)
        search._date_filter.select(data=DateSearchFilter.Type.USER_INTERVAL)
        search._date_filter.start_date.update(localdate(2010, 1, 1))
        search._date_filter.end_date.update(localdate(2012, 2, 15))

        search.search.refresh()
        self.check_search(search, 'commission-confirmed-no-filter')

        search.set_searchbar_search_string('dei')
        search.search.refresh()
        self.check_search(search, 'commission-confirmed-string-filter')

        search.set_searchbar_search_string('')
        search._salesperson_filter.set_state(salesperson.id)
        search.search.refresh()
        self.check_search(search, 'commission-confirmed-salesperson-filter')

        # Then check for columns getting the paid date of the payment
        api.sysparam.set_bool(self.store,
                              'SALE_PAY_COMMISSION_WHEN_CONFIRMED',
                              False)
        search = CommissionSearch(self.store)

        search._date_filter.select(data=DateSearchFilter.Type.USER_INTERVAL)
        search._date_filter.start_date.update(localdate(2010, 1, 1))
        search._date_filter.end_date.update(localdate(2012, 2, 15))

        search.search.refresh()
        self.check_search(search, 'commission-paid-no-filter')

        search.set_searchbar_search_string('dei')
        search.search.refresh()
        self.check_search(search, 'commission-paid-string-filter')

        search.set_searchbar_search_string('')
        search._salesperson_filter.set_state(salesperson.id)
        search.search.refresh()
        self.check_search(search, 'commission-paid-salesperson-filter')
