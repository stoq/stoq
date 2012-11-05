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
    @mock.patch('stoq.gui.inventory.api.new_transaction')
    def _check_run_dialog(self, action, dialog, other_args, new_transaction,
                          run_dialog):
        new_transaction.return_value = self.trans

        with mock.patch.object(self.trans, 'commit'):
            with mock.patch.object(self.trans, 'close'):
                self.activate(action)
                expected_args = [dialog, self.trans]
                if other_args:
                    expected_args.extend(other_args)
                run_dialog.assert_called_once_with(*expected_args)

    def testInitial(self):
        app = self.create_app(InventoryApp, 'inventory')
        self.check_app(app, 'inventory')

    def testSelect(self):
        self.create_inventory(branch=get_current_branch(self.trans))

        app = self.create_app(InventoryApp, 'InventoryApp')
        results = app.main_window.results
        results.select(results[0])

    @mock.patch('stoq.gui.inventory.yesno')
    @mock.patch('stoq.gui.inventory.api.new_transaction')
    def test_cancel_inventory(self, new_transaction, yesno):
        new_transaction.return_value = self.trans
        yesno.return_value = False

        self.create_inventory(branch=get_current_branch(self.trans))

        app = self.create_app(InventoryApp, 'inventory')

        results = app.main_window.results
        results.select(results[0])

        with mock.patch.object(self.trans, 'commit'):
            with mock.patch.object(self.trans, 'close'):
                self.activate(app.main_window.Cancel)
                yesno.assert_called_once_with('Are you sure you want to cancel '
                                              'this inventory ?',
                                              gtk.RESPONSE_YES, "Don't cancel",
                                              "Cancel inventory")
                self.assertEquals(results[0].status, Inventory.STATUS_CANCELLED)

    def test_run_dialogs(self):
        inventory = self.create_inventory(branch=get_current_branch(self.trans))

        app = self.create_app(InventoryApp, 'inventory')

        results = app.main_window.results
        results.select(results[0])

        self._check_run_dialog(app.main_window.AdjustAction,
                               ProductsAdjustmentDialog, [inventory])

        results.select(results[0])
        self._check_run_dialog(app.main_window.CountingAction,
                               ProductCountingDialog, [inventory])

        branches = list(Branch.select(connection=self.trans))
        branches.remove(inventory.branch)
        self._check_run_dialog(app.main_window.NewInventory,
                               OpenInventoryDialog, [branches])

    @mock.patch('stoq.gui.inventory.InventoryApp.print_report')
    @mock.patch('stoq.gui.inventory.warning')
    def test_print_product_listing(self, warning, print_report):
        inventory = self.create_inventory(branch=get_current_branch(self.trans))

        app = self.create_app(InventoryApp, 'inventory')

        results = app.main_window.results
        results.select(results[0])

        self.activate(app.main_window.PrintProductListing)
        warning.assert_called_once_with("No products found in the inventory.")

        item = self.create_inventory_item(inventory=inventory)
        self.activate(app.main_window.PrintProductListing)
        print_report.assert_called_once_with(ProductCountingReport,
                                             [item.product.sellable])
