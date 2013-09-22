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

import contextlib

import gtk
import mock
from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.inventory import Inventory
from stoqlib.gui.dialogs.inventorydetails import InventoryDetailsDialog
from stoqlib.gui.editors.inventoryadjustmenteditor import InventoryAdjustmentEditor
from stoqlib.gui.editors.inventoryeditor import InventoryOpenEditor
from stoqlib.gui.wizards.inventorywizard import InventoryCountWizard
from stoqlib.reporting.product import ProductCountingReport

from stoq.gui.inventory import InventoryApp
from stoq.gui.test.baseguitest import BaseGUITest


class TestInventory(BaseGUITest):
    def _check_run_dialog(self, action, dialog, other_args):
        with contextlib.nested(
                mock.patch('stoq.gui.inventory.InventoryApp.run_dialog'),
                mock.patch('stoq.gui.inventory.api.new_store'),
                mock.patch.object(self.store, 'commit'),
                mock.patch.object(self.store, 'close')) as ctx:
            new_store = ctx[1]
            new_store.return_value = self.store

            self.activate(action)
            expected_args = [dialog, self.store]
            if other_args:
                expected_args.extend(other_args)
            run_dialog = ctx[0]
            run_dialog.assert_called_once_with(*expected_args)

    def test_initial(self):
        app = self.create_app(InventoryApp, u'inventory')
        self.check_app(app, u'inventory')

    def test_select(self):
        self.create_inventory(branch=get_current_branch(self.store))

        app = self.create_app(InventoryApp, u'inventory')
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

    @mock.patch('stoq.gui.inventory.yesno')
    @mock.patch('stoq.gui.inventory.api.new_store')
    def test_cancel_inventory_false(self, new_store, yesno):
        new_store.return_value = self.store
        yesno.return_value = False

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
                self.assertEquals(results[0].status, Inventory.STATUS_OPEN)

    def test_run_dialogs(self):
        inventory = self.create_inventory(branch=get_current_branch(self.store))

        app = self.create_app(InventoryApp, u'inventory')

        results = app.results
        results.select(results[0])

        self._check_run_dialog(app.AdjustAction,
                               InventoryAdjustmentEditor, [inventory])

        with mock.patch.object(results[0], 'all_items_counted', new=lambda: False):
            results.select(results[0])
            self._check_run_dialog(app.CountingAction,
                                   InventoryCountWizard, [inventory])

        inventory.close()
        app._update_widgets()
        self._check_run_dialog(app.NewInventory,
                               InventoryOpenEditor, [])

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

    @mock.patch('stoq.gui.inventory.api.new_store')
    @mock.patch('stoq.gui.inventory.InventoryApp.run_dialog')
    def test_show_inventory_details(self, run_dialog, new_store):
        new_store.return_value = self.store
        self.create_inventory(branch=get_current_branch(self.store))

        app = self.create_app(InventoryApp, u'inventory')
        results = app.results
        results.select(results[0])

        with mock.patch.object(self.store, 'close'):
            self.activate(app.Details)

        run_dialog.assert_called_once_with(InventoryDetailsDialog, self.store, results[0])

    @mock.patch('stoq.gui.inventory.warning')
    @mock.patch('stoq.gui.inventory.api.new_store')
    def test_new_activate(self, new_store, warning):
        new_store.return_value = self.store
        self.create_inventory(branch=get_current_branch(self.store))

        app = self.create_app(InventoryApp, u'inventory')
        self.activate(app.window.NewToolItem)
        warning.assert_called_once_with("You cannot open an inventory without having a "
                                        "branch with stock in it.")

    def test_deactivate(self):
        app = self.create_app(InventoryApp, u'inventory')
        self.activate(app.window.Close)
