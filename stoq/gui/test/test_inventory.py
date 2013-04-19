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

import gtk
import mock

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.person import Branch
from stoqlib.domain.inventory import Inventory
from stoqlib.gui.dialogs.openinventorydialog import OpenInventoryDialog
from stoqlib.gui.dialogs.productadjustmentdialog import ProductsAdjustmentDialog
from stoqlib.gui.dialogs.productcountingdialog import ProductCountingDialog
from stoqlib.reporting.product import ProductCountingReport
from stoq.gui.inventory import InventoryApp
from stoq.gui.test.baseguitest import BaseGUITest


class TestInventory(BaseGUITest):
    @mock.patch('stoq.gui.inventory.InventoryApp.run_dialog')
    @mock.patch('stoq.gui.inventory.api.new_store')
    def _check_run_dialog(self, action, dialog, other_args, new_store,
                          run_dialog):
        new_store.return_value = self.store

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.activate(action)
                expected_args = [dialog, self.store]
                if other_args:
                    expected_args.extend(other_args)
                run_dialog.assert_called_once_with(*expected_args)

    def testInitial(self):
        app = self.create_app(InventoryApp, u'inventory')
        self.check_app(app, u'inventory')

    def testSelect(self):
        self.create_inventory(branch=get_current_branch(self.store))

        app = self.create_app(InventoryApp, u'InventoryApp')
        results = app.results
        results.select(results[0])

    @mock.patch('stoq.gui.inventory.yesno')
    @mock.patch('stoq.gui.inventory.api.new_store')
    def test_cancel_inventory(self, new_store, yesno):
        new_store.return_value = self.store
        yesno.return_value = True

        self.create_inventory(branch=get_current_branch(self.store))

        app = self.create_app(InventoryApp, u'inventory')

        results = app.results
        results.select(results[0])

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.activate(app.Cancel)
                yesno.assert_called_once_with(u'Are you sure you want to cancel '
                                              u'this inventory ?',
                                              gtk.RESPONSE_NO,
                                              u"Cancel inventory",
                                              u"Don't cancel")
                self.assertEquals(results[0].status, Inventory.STATUS_CANCELLED)

    def test_run_dialogs(self):
        inventory = self.create_inventory(branch=get_current_branch(self.store))

        app = self.create_app(InventoryApp, u'inventory')

        results = app.results
        results.select(results[0])

        self._check_run_dialog(app.AdjustAction,
                               ProductsAdjustmentDialog, [inventory])

        results.select(results[0])
        self._check_run_dialog(app.CountingAction,
                               ProductCountingDialog, [inventory])

        branches = list(self.store.find(Branch))
        branches.remove(inventory.branch)
        self._check_run_dialog(app.NewInventory,
                               OpenInventoryDialog, [branches])

    @mock.patch('stoq.gui.inventory.InventoryApp.print_report')
    @mock.patch('stoq.gui.inventory.warning')
    def test_print_product_listing(self, warning, print_report):
        inventory = self.create_inventory(branch=get_current_branch(self.store))

        app = self.create_app(InventoryApp, u'inventory')

        results = app.results
        results.select(results[0])

        self.activate(app.PrintProductListing)
        warning.assert_called_once_with(u"No products found in the inventory.")

        item = self.create_inventory_item(inventory=inventory)
        self.activate(app.PrintProductListing)
        print_report.assert_called_once_with(ProductCountingReport,
                                             [item.product.sellable])
