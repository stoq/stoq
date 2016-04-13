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

from decimal import Decimal
from kiwi.currency import currency


from stoqlib.database.runtime import get_current_user
from stoqlib.domain.event import Event
from stoqlib.domain.sale import Sale
from stoqlib.gui.editors.saleeditor import (SaleQuoteItemEditor, SaleClientEditor,
                                            SalesPersonEditor, SaleTokenEditor)
from stoqlib.gui.test.uitestutils import GUITest


class TestSaleQuoteItemEditor(GUITest):
    def test_show(self):
        sale = self.create_sale()
        storable = self.create_storable(branch=sale.branch, stock=20)
        sale_item = sale.add_sellable(storable.product.sellable)
        sale_item.price = 100
        editor = SaleQuoteItemEditor(self.store, sale_item)
        editor.item_slave.sale.set_label('12345')

        self.check_editor(editor, 'editor-salequoteitem-show')
        module = 'stoqlib.lib.pluginmanager.PluginManager.is_active'
        with mock.patch(module) as patch:
            patch.return_value = True
            editor = SaleQuoteItemEditor(self.store, sale_item)
            editor.item_slave.sale.set_label('23456')
            self.check_editor(editor, 'editor-salequoteitem-show-nfe')

    @mock.patch('stoqlib.gui.editors.invoiceitemeditor.get_plugin_manager')
    def test_create_taxes(self, get_plugin_manager):
        manager = mock.Mock()
        manager.is_active.return_value = True
        get_plugin_manager.return_value = manager

        sale = self.create_sale()
        storable = self.create_storable(branch=sale.branch, stock=20)
        sale_item = sale.add_sellable(storable.product.sellable)

        # Mimic an item with missing taxes
        sale_item.icms_info = None
        sale_item.ipi_info = None
        sale_item.pis_info = None
        sale_item.cofins_info = None

        SaleQuoteItemEditor(self.store, sale_item)
        # Make sure the editor created the missing taxes
        self.assertIsNotNone(sale_item.icms_info)
        self.assertIsNotNone(sale_item.pis_info)
        self.assertIsNotNone(sale_item.ipi_info)
        self.assertIsNotNone(sale_item.cofins_info)


class TestSaleQuoteItemSlave(GUITest):
    def test_show_param_allow_higher_sale_price(self):
        sale = self.create_sale()
        storable = self.create_storable(branch=sale.branch, stock=20)
        sale_item = sale.add_sellable(storable.product.sellable)
        sale_item.price = 100
        editor = SaleQuoteItemEditor(self.store, sale_item)
        slave = editor.item_slave
        slave.sale.set_label('12345')

        # quantity=1, price=100
        with self.sysparam(ALLOW_HIGHER_SALE_PRICE=True):
            self.assertEqual(slave.total.read(), 100)
            slave.quantity.update(2)
            self.assertEqual(slave.total.read(), 200)
            slave.price.update(150)
            self.assertEqual(slave.total.read(), 300)

            slave.reserved.update(1)
            self.click(editor.main_dialog.ok_button)

            self.check_editor(editor, 'slave-salequoteitem-with-higher-price-show')

    def test_edit_product_without_storable(self):
        sale_item = self.create_sale_item()
        sale_item.price = 100
        self.assertEqual(sale_item.quantity, 1)
        editor = SaleQuoteItemEditor(self.store, sale_item)
        slave = editor.item_slave
        slave.sale.set_label('12345')
        self.assertNotVisible(slave, ['reserved'])

        self.assertEqual(slave.total.read(), 100)
        slave.quantity.update(3)
        self.assertEqual(slave.total.read(), 300)
        self.click(editor.main_dialog.ok_button)
        self.assertEqual(sale_item.quantity, 3)

    def test_edit_product_with_batch(self):
        sale = self.create_sale()
        product = self.create_product()
        self.create_storable(product=product, is_batch=True)

        sale.status = Sale.STATUS_QUOTE
        sale_item = sale.add_sellable(product.sellable)
        sale_item.price = 10
        self.assertEqual(sale_item.quantity, 1)

        editor = SaleQuoteItemEditor(self.store, sale_item)
        slave = editor.item_slave
        self.assertNotVisible(slave, ['reserved'])
        slave.quantity.update(2)
        self.assertEqual(slave.total.read(), 20)
        self.click(editor.main_dialog.ok_button)
        self.assertEqual(sale_item.quantity, 2)

    def test_reserve(self):
        product = self.create_product(stock=1, storable=True)
        sale_item = self.create_sale_item(sellable=product.sellable)

        editor = SaleQuoteItemEditor(self.store, sale_item)
        slave = editor.item_slave
        upper = slave.reserved.get_adjustment().get_upper()
        self.assertEquals(upper, 1)
        self.assertEquals(unicode(slave.reserved.emit('validate', 2)),
                          "Not enough stock to reserve.")

        slave.quantity.update(3)
        upper = slave.reserved.get_adjustment().get_upper()
        self.assertEquals(upper, 3)

    def test_reserve_service(self):
        service = self.create_service(description=u'Service')
        sale_item = self.create_sale_item(sellable=service.sellable)
        editor = SaleQuoteItemEditor(self.store, sale_item)
        slave = editor.item_slave
        self.assertNotVisible(slave, ['reserved'])

    def test_reserve_package(self):
        package_product = self.create_product(is_package=True)
        component = self.create_product(stock=1)
        self.create_product_component(product=package_product,
                                      component=component)
        sale_item = self.create_sale_item(sellable=package_product.sellable)
        self.create_sale_item(sellable=component.sellable, parent_item=sale_item)

        editor = SaleQuoteItemEditor(self.store, sale_item)
        slave = editor.item_slave
        self.assertEquals(unicode(slave.reserved.emit('validate', 3)),
                          "One or more components for this package doesn't have "
                          "enough of stock to reserve")
        self.assertSensitive(slave, ['reserved', 'quantity'])
        slave.reserved.update(1)
        self.click(editor.main_dialog.ok_button)

        # Nothing to reserve
        sale_item.quantity_decreased = 1
        editor = SaleQuoteItemEditor(self.store, sale_item)
        slave = editor.item_slave
        slave.reserved.update(1)
        self.click(editor.main_dialog.ok_button)

    def test_return_package_product_to_stock(self):
        package_product = self.create_product(is_package=True)
        component = self.create_product(stock=1)
        self.create_product_component(product=package_product,
                                      component=component,
                                      component_quantity=1)
        sale_item = self.create_sale_item(sellable=package_product.sellable)
        child_item = self.create_sale_item(sellable=component.sellable, parent_item=sale_item)
        sale_item.quantity_decreased = 1
        child_item.quantity_decreased = 1
        child_storable = child_item.sellable.product_storable

        editor = SaleQuoteItemEditor(self.store, sale_item)
        slave = editor.item_slave
        slave.reserved.update(0)
        self.click(editor.main_dialog.ok_button)
        stock_item = child_storable.get_stock_item(child_item.sale.branch,
                                                   child_item.batch)
        self.assertEquals(stock_item.quantity, 2)

    def test_edit_package_child(self):
        package_product = self.create_product(is_package=True)
        component = self.create_product(stock=2)
        self.create_product_component(product=package_product,
                                      component=component)
        sale_item = self.create_sale_item(sellable=package_product.sellable)
        child = self.create_sale_item(sellable=component.sellable,
                                      parent_item=sale_item)

        editor = SaleQuoteItemEditor(self.store, child)
        slave = editor.item_slave
        # We should be able to see, but not modify those widgets
        self.assertVisible(slave, ['reserved', 'quantity', 'price'])
        self.assertNotSensitive(slave, ['reserved', 'quantity', 'price'])

    def test_show_param_no_allow_higher_sale_price(self):
        sale_item = self.create_sale_item()
        editor = SaleQuoteItemEditor(self.store, sale_item)
        slave = editor.item_slave
        slave.sale.set_label('12345')

        # quantity=1, price=100
        with self.sysparam(ALLOW_HIGHER_SALE_PRICE=False):
            self.assertEqual(slave.total.read(), 100)
            slave.quantity.update(2)
            self.assertEqual(slave.total.read(), 200)
            slave.price.update(150)
            # The price greater than 100 should be invalid.
            self.assertInvalid(slave, ['price'])

    def test_on_confirm_with_discount(self):
        events_before = self.store.find(Event).count()

        sale_item = self.create_sale_item()
        sale_item.sale.identifier = 333123

        current_user = get_current_user(self.store)
        current_user.profile.max_discount = Decimal('5')

        # A manager to authorize the discount
        manager = self.create_user()
        manager.profile.max_discount = Decimal('10')

        editor = SaleQuoteItemEditor(self.store, sale_item)
        slave = editor.item_slave

        # Try applying 9% of discount
        slave.price.update(currency('9.10'))

        # The user is not allowed to give 10% discount
        self.assertNotSensitive(editor.main_dialog, ['ok_button'])

        # Lets call the manager and ask for permission
        with mock.patch('stoqlib.gui.editors.saleeditor.run_dialog') as rd:
            rd.return_value = manager
            slave.price.emit('icon-press', gtk.ENTRY_ICON_PRIMARY, None)

        # Now it should be possible to confirm
        self.click(editor.main_dialog.ok_button)
        events_after = self.store.find(Event).count()
        self.assertEquals(events_after, events_before + 1)

        last_event = self.store.find(Event).order_by(Event.id).last()
        expected = (u'Sale 333123: User username authorized 9.00 % '
                    u'of discount changing\n Description value from $10.00 to $9.10.')
        self.assertEquals(last_event.description, expected)

    def test_on_confirm_without_discount(self):
        events_before = self.store.find(Event).count()

        sale_item = self.create_sale_item()

        current_user = get_current_user(self.store)
        current_user.profile.max_discount = Decimal('5')

        # A manager to authorize the discount
        manager = self.create_user()
        manager.profile.max_discount = Decimal('10')

        editor = SaleQuoteItemEditor(self.store, sale_item)
        slave = editor.item_slave
        # Try applying 10% of discount
        slave.price.update(currency('9.00'))

        # The user is not allowed to give 10% discount
        self.assertNotSensitive(editor.main_dialog, ['ok_button'])

        # Lets call the manager and ask for permission
        with mock.patch('stoqlib.gui.editors.saleeditor.run_dialog') as rd:
            rd.return_value = manager
            slave.price.emit('icon-press', gtk.ENTRY_ICON_PRIMARY, None)

        # Forget about the discount
        slave.price.update(currency('10'))

        # This will not trigger an event
        self.click(editor.main_dialog.ok_button)
        events_after = self.store.find(Event).count()
        # The number of events doesn't changed
        self.assertEquals(events_after, events_before)


class TestSaleClientEditor(GUITest):
    def test_change_client(self):
        zoidberg = self.create_client(u"Zoidberg")
        bender = self.create_client(u"Bender")
        sale = self.create_sale(client=zoidberg)

        sale.identifier = 12345
        sale.status = sale.STATUS_CONFIRMED
        editor = SaleClientEditor(self.store, model=sale)

        self.assertEquals(editor.status_str.get_text(),
                          (u"Confirmed" or u"Ordered"))
        self.assertFalse(editor.salesperson_id.get_sensitive())
        self.assertEquals(zoidberg, editor.model.client)

        editor.fields['client'].set_value(bender)
        self.click(editor.main_dialog.ok_button)
        self.assertEquals(bender, sale.client)

        self.check_editor(editor, 'editor-sale-client-edit')


class TestSalesPersonEditor(GUITest):
    def test_change_salesperson(self):
        salesperson1 = self.create_sales_person(name=u'First sales person')
        salesperson2 = self.create_sales_person(name=u'Second sales person')
        sale = self.create_sale()

        sale.identifier = 1337
        sale.status = sale.STATUS_CONFIRMED
        sale.salesperson = salesperson1

        editor = SalesPersonEditor(self.store, model=sale)
        self.check_editor(editor, 'editor-salesperson-edit')
        self.assertEquals(editor.salesperson_id.get_selected(), salesperson1.id)
        self.assertFalse(editor.client.get_property('visible'))

        editor.salesperson_id.select_item_by_data(salesperson2.id)
        self.click(editor.main_dialog.ok_button)
        self.assertEquals(sale.salesperson, salesperson2)


class TestSaleTokenEditor(GUITest):
    def test_create(self):
        editor = SaleTokenEditor(self.store)
        self.check_editor(editor, 'editor-saletoken-create')

    def test_edit(self):
        token = self.create_sale_token(code=u'sale token 1')
        editor = SaleTokenEditor(self.store, model=token)
        self.check_editor(editor, 'editor-saletoken-edit')

    def test_description_valitation(self):
        self.create_sale_token(code=u'sale token 1')
        editor = SaleTokenEditor(self.store)
        editor.code.set_text(u'sale token 1')
        # We should not be able to register this token, description should be
        # unique
        self.assertNotSensitive(editor.main_dialog, ['ok_button'])

        editor.code.set_text(u'sale token 2')
        self.assertSensitive(editor.main_dialog, ['ok_button'])
