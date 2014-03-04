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

import mock

from stoqlib.domain.receiving import (ReceivingOrder, ReceivingOrderItem,
                                      PurchaseReceivingMap)
from stoqlib.gui.dialogs.receivingdialog import ReceivingOrderDetailsDialog
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.search.receivingsearch import PurchaseReceivingSearch
from stoqlib.reporting.purchasereceival import PurchaseReceivalReport
from stoqlib.lib.dateutils import localdatetime


class TestReceivingOrderSearch(GUITest):
    def _create_domain(self):
        self.clean_domain([ReceivingOrderItem, PurchaseReceivingMap, ReceivingOrder])

        supplier_a = self.create_supplier(u'Mark')
        purchase_order_a = self.create_purchase_order(supplier=supplier_a)
        order_a = self.create_receiving_order(purchase_order=purchase_order_a)

        supplier_b = self.create_supplier(u'Dominique')
        purchase_order_b = self.create_purchase_order(supplier=supplier_b)
        order_b = self.create_receiving_order(purchase_order=purchase_order_b)

        purchase_order_a.identifier = 81954
        order_a.receival_date = localdatetime(2012, 1, 1)

        purchase_order_b.identifier = 78526
        order_b.receival_date = localdatetime(2012, 2, 2)

    def _show_search(self):
        search = PurchaseReceivingSearch(self.store)
        search.search.refresh()
        search.results.select(search.results[0])
        return search

    def test_receiving_order_search(self):
        self._create_domain()
        search = self._show_search()

        self.check_search(search, 'receiving-no-filter')

        search.set_searchbar_search_string('dom')
        search.search.refresh()
        self.check_search(search, 'receiving-string-filter')

    @mock.patch('stoqlib.gui.search.receivingsearch.run_dialog')
    @mock.patch('stoqlib.gui.search.searchdialog.print_report')
    def test_buttons(self, print_report, run_dialog):
        self._create_domain()
        search = self._show_search()

        self.assertSensitive(search._details_slave, ['print_button'])
        self.click(search._details_slave.print_button)
        print_report.assert_called_once_with(PurchaseReceivalReport,
                                             search.results,
                                             list(search.results),
                                             filters=search.search.get_search_filters())

        search.search.refresh()
        self.assertNotSensitive(search._details_slave, ['details_button'])
        search.results.select(search.results[0])
        self.assertSensitive(search._details_slave, ['details_button'])
        self.click(search._details_slave.details_button)
        order = self.store.get(ReceivingOrder, search.results[0].id)
        run_dialog.assert_called_once_with(ReceivingOrderDetailsDialog,
                                           search, self.store, order)
        run_dialog.reset_mock()
        search.results.emit('row_activated', search.results[0])
        run_dialog.assert_called_once_with(ReceivingOrderDetailsDialog,
                                           search, self.store, order)
