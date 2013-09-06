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
from stoqlib.lib.dateutils import localdate
from stoqlib.gui.search.searchfilters import DateSearchFilter
from stoqlib.gui.search.salespersonsearch import SalesPersonSalesSearch
from stoqlib.gui.test.uitestutils import GUITest


class TestSalesPersonSalesSearch(GUITest):

    def test_show(self):
        # 5 items in sale for first salesperson
        sale1 = self.create_sale()
        self.add_product(sale1, quantity=5)
        sale1.order()
        self.add_payments(sale1, method_type=u'check')
        sale1.confirm()
        sale1.confirm_date = localdate(2011, 01, 01).date()
        sale1.salesperson.person.name = u'salesperson1'

        # 3 items in sale for first salesperson
        sale2 = self.create_sale()
        sale2.salesperson = sale1.salesperson
        self.add_product(sale2, quantity=3)
        sale2.order()
        self.add_payments(sale2, method_type=u'money')
        sale2.confirm()
        sale2.confirm_date = sale1.confirm_date

        # 15 items for another salesperson
        sale3 = self.create_sale()
        self.add_product(sale3, quantity=15)
        sale3.order()
        self.add_payments(sale3, method_type=u'bill')
        sale3.confirm()
        sale3.confirm_date = sale1.confirm_date
        sale3.salesperson.person.name = u'salesperson2'

        dialog = SalesPersonSalesSearch(self.store)
        dialog.date_filter.select(DateSearchFilter.Type.USER_DAY)
        dialog.date_filter.start_date.update(sale1.confirm_date)
        self.click(dialog.search.search_button)
        self.check_dialog(dialog, 'sales-person-sales-show')

    def test_synchronized_mode(self):
        # This is a non editable parameter
        with self.sysparam(SYNCHRONIZED_MODE=True):
            current = api.get_current_branch(self.store)
            other_branch = self.create_branch()

            # One sale on one branch
            sale1 = self.create_sale(branch=current)
            self.add_product(sale1)
            sale1.order()
            self.add_payments(sale1, method_type=u'check')
            sale1.confirm()
            sale1.confirm_date = localdate(2011, 01, 01).date()
            sale1.salesperson.person.name = u'salesperson1'

            # And another one on a second branch
            sale2 = self.create_sale(branch=other_branch)
            sale2.salesperson = sale1.salesperson
            self.add_product(sale2)
            sale2.order()
            self.add_payments(sale2, method_type=u'money')
            sale2.confirm()
            sale2.confirm_date = sale1.confirm_date

            dialog = SalesPersonSalesSearch(self.store)
            dialog.date_filter.select(DateSearchFilter.Type.USER_INTERVAL)
            dialog.date_filter.start_date.update(sale1.confirm_date)
            dialog.date_filter.end_date.update(sale1.confirm_date)
            self.click(dialog.search.search_button)
            self.check_dialog(dialog, 'sales-person-sales-synchronized-show')
