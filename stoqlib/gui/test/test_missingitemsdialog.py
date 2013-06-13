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

from decimal import Decimal
import mock

from kiwi.python import Settable

from stoqlib.domain.production import ProductionOrder
from stoqlib.domain.sale import Sale
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.gui.dialogs.missingitemsdialog import (get_missing_items,
                                                    MissingItemsDialog)
from stoqlib.gui.test.uitestutils import GUITest


class TestMissingItemsDialog(GUITest):
    @mock.patch('stoqlib.gui.dialogs.missingitemsdialog.api.new_store')
    def test_confirm(self, new_store):
        # We need to use the current transaction in the test, since the test
        # object is only in this transaction
        new_store.return_value = self.store

        sale = self.create_sale()
        sale_item = self.create_sale_item(sale=sale)
        product = sale_item.sellable.product
        self.create_storable(product=product)
        missing_item = Settable(description='desc',
                                ordered=Decimal('1'),
                                stock=Decimal('0'),
                                storable=sale_item.sellable.product.storable)

        sale.status = Sale.STATUS_QUOTE
        dialog = MissingItemsDialog(sale, [missing_item])

        # Dont commit the transaction
        with mock.patch.object(self.store, 'commit'):
            # Also dont close it, since tearDown will do it.
            with mock.patch.object(self.store, 'close'):
                self.click(dialog.ok_button)

        storable = dialog.retval[0].storable
        self.check_dialog(dialog, 'test-confirm-sale-missing-dialog-confirm',
                          [storable, sale, sale_item, product])

    @mock.patch('stoqlib.gui.dialogs.missingitemsdialog.info')
    @mock.patch('stoqlib.gui.dialogs.missingitemsdialog.api.new_store')
    def test_confirm_production(self, new_store, info):
        # We need to use the current transaction in the test, since the test
        # object is only in this transaction
        new_store.return_value = self.store

        sale = self.create_sale()
        sale.status = Sale.STATUS_QUOTE
        product = self.create_product()
        self.create_storable(product)
        self.create_product_component(product)

        sale.add_sellable(product.sellable, quantity=15)
        missing_item = Settable(description='desc',
                                ordered=Decimal('15'),
                                stock=Decimal('0'),
                                storable=product.storable)

        dialog = MissingItemsDialog(sale, [missing_item])

        self.assertEquals(self.store.find(ProductionOrder).count(), 0)

        # Dont commit the transaction
        with mock.patch.object(self.store, 'commit'):
            # Also dont close it, since tearDown will do it.
            with mock.patch.object(self.store, 'close'):
                self.click(dialog.ok_button)

        info.assert_called_once_with('A new production was created for the '
                                     'missing composed products')
        self.assertEquals(self.store.find(ProductionOrder).count(), 1)
        production = self.store.find(ProductionOrder).any()
        self.assertEquals(production.get_items().count(), 1)
        self.assertEquals(production.get_items()[0].product, product)
        self.assertEquals(production.get_items()[0].quantity, 15)


class TestGetMissingItems(DomainTest):
    def test_get_missing_items(self):
        sale = self.create_sale()

        stock_item = self.create_sale_item(sale=sale)
        missing_item = self.create_sale_item(sale=sale)

        stock_storable = self.create_storable(
            product=stock_item.sellable.product)
        missing_storable = self.create_storable(
            product=missing_item.sellable.product)

        self.create_product_stock_item(storable=stock_storable, quantity=1)
        self.create_product_stock_item(storable=missing_storable, quantity=0)

        missing = get_missing_items(sale, self.store)

        self.assertEquals(missing[0].storable, missing_storable)
