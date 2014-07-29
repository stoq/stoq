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

import mock

from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.search.searchoptions import Any
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localtoday

from ..medicssearch import OpticalMedicSearch, MedicSalesSearch
from .test_optical_domain import OpticalDomainTest


class TestMedicSearch(GUITest, OpticalDomainTest):

    def test_show(self):
        search = OpticalMedicSearch(self.store)
        search.search.refresh()
        self.check_search(search, 'opticalmedic-show')

    def test_get_editor_model(self):
        medic = self.create_optical_medic()
        search = OpticalMedicSearch(self.store)
        search.search.refresh()
        view = search.search.result_view[0]
        assert search.get_editor_model(view)
        assert search.get_editor_model(view).id == medic.id


class TestMedicSalesSearch(GUITest, OpticalDomainTest):

    @mock.patch('plugins.optical.medicssearch.run_dialog')
    def test_show(self, run_dialog):
        optical = self.create_optical_work_order()
        optical.medic = self.create_optical_medic()

        sale = self.create_sale()
        sale.identifier = 99413

        workorder = optical.work_order
        workorder.sale = sale

        sellable = self.create_sellable()
        sale_item = sale.add_sellable(sellable)
        wo_item = self.create_work_order_item(order=workorder)
        wo_item.sale_item = sale_item
        self.add_payments(sale)
        sale.order()
        sale.confirm()
        sale.open_date = localtoday()
        sale.confirm_date = localtoday()

        search = MedicSalesSearch(self.store)
        search._date_filter.select(data=Any)
        search.search.refresh()
        self.check_search(search, 'optical-medic-sales-search')

        search.results.select(search.results[0])
        self.click(search.sale_details_button)

        self.assertEquals(run_dialog.call_count, 1)
        self.assertEquals(run_dialog.call_args[0][0], SaleDetailsDialog)
        self.assertEquals(run_dialog.call_args[0][1], search)
        self.assertEquals(run_dialog.call_args[0][2], self.store)
        self.assertEquals(run_dialog.call_args[0][3].id, sale.id)
