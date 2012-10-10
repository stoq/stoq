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

from kiwi.ui.search import DateSearchFilter

from stoqlib.gui.search.salespersonsearch import SalesPersonSalesSearch
from stoqlib.gui.uitestutils import GUITest


class TestSalesPersonSalesSearch(GUITest):
    def testShow(self):
        # 5 items in sale for first salesperson
        sale1 = self.create_sale()
        self.add_product(sale1, quantity=5)
        sale1.order()
        self.add_payments(sale1, method_type='check')
        sale1.confirm()
        sale1.confirm_date = datetime.date(2011, 01, 01)
        sale1.salesperson.person.name = 'salesperson1'

        # 3 items in sale for first salesperson
        sale2 = self.create_sale()
        sale2.salesperson = sale1.salesperson
        self.add_product(sale2, quantity=3)
        sale2.order()
        self.add_payments(sale2, method_type='money')
        sale2.confirm()
        sale2.confirm_date = sale1.confirm_date

        # 15 items for another salesperson
        sale3 = self.create_sale()
        self.add_product(sale3, quantity=15)
        sale3.order()
        self.add_payments(sale3, method_type='bill')
        sale3.confirm()
        sale3.confirm_date = sale1.confirm_date
        sale3.salesperson.person.name = 'salesperson2'

        dialog = SalesPersonSalesSearch(self.trans)
        dialog.date_filter.select(DateSearchFilter.Type.USER_DAY)
        dialog.date_filter.start_date.update(sale1.confirm_date)
        self.click(dialog.search.search.search_button)
        self.check_dialog(dialog, 'sales-person-sales-show')
