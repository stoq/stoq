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
from decimal import Decimal

from kiwi import ValueUnset
from kiwi.currency import currency
from kiwi.datatypes import converter
import mock
import gtk

from stoqlib.api import api
from stoqlib.database.runtime import StoqlibStore
from stoqlib.domain.events import TillOpenEvent
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.sale import Sale
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.service import Service
from stoqlib.domain.till import Till
from stoqlib.domain.views import SellableFullStockView
from stoqlib.gui.editors.deliveryeditor import (_CreateDeliveryModel,
                                                CreateDeliveryEditor)
from stoqlib.gui.editors.serviceeditor import ServiceItemEditor
from stoqlib.gui.editors.tilleditor import TillOpeningEditor
from stoqlib.gui.search.deliverysearch import DeliverySearch
from stoqlib.gui.search.personsearch import ClientSearch
from stoqlib.gui.search.productsearch import ProductSearch
from stoqlib.gui.search.salesearch import (SaleWithToolbarSearch,
                                           SoldItemsByBranchSearch)
from stoqlib.gui.search.sellablesearch import SaleSellableSearch
from stoqlib.gui.search.servicesearch import ServiceSearch
from stoqlib.reporting.booklet import BookletReport

from stoq.gui.pos import PosApp, TemporarySaleItem
from stoq.gui.test.baseguitest import BaseGUITest

__tests__ = 'stoq/gui/pos.py'


class TestPos(BaseGUITest):
    def test_initial(self):
        app = self.create_app(PosApp, u'pos')
        self.check_app(app, u'pos')

    def _open_till(self, store):
        till = Till(store=store,
                    station=api.get_current_station(store))
        till.open_till()

        TillOpenEvent.emit(till=till)
        self.assertEquals(till, Till.get_current(store))
        return till

    def _pos_open_till(self, pos):
        with mock.patch('stoqlib.gui.fiscalprinter.run_dialog') as run_dialog:
            self.activate(pos.TillOpen)
            self._called_once_with_store(run_dialog, TillOpeningEditor, pos)

    def _get_pos_with_open_till(self):
        app = self.create_app(PosApp, u'pos')
        pos = app
        self._pos_open_till(pos)
        return pos

    def _add_product(self, pos, sellable):
        sale_item = TemporarySaleItem(sellable=sellable, quantity=1)
        pos.add_sale_item(sale_item)
        return sale_item

    def _add_service(self, pos, sellable):
        service = Service(sellable=sellable, store=self.store)
        self._add_product(pos, sellable)
        return service

    def _auto_confirm_sale(self, wizard, app, store, sale,
                           subtotal, total_paid, payment_method):
        # This is in another store and as we want to avoid committing
        # we need to open the till again
        self._open_till(store)

        sale.order()
        total = sale.get_total_sale_amount()
        payment_method.create_payment(Payment.TYPE_IN, sale.group, sale.branch, total)
        self.sale = sale
        return sale

    def _auto_confirm_sale_wizard(self, wizard, app, store, sale,
                                  subtotal, total_paid, current_document):
        payment_method = PaymentMethod.get_by_name(store, u'money')
        return self._auto_confirm_sale(wizard, app, store, sale, subtotal,
                                       total_paid, payment_method)

    def _auto_confirm_sale_wizard_with_bill(self, wizard, app, store, sale,
                                            subtotal, total_paid,
                                            current_document):
        sale.client = self._create_client(store)
        payment_method = PaymentMethod.get_by_name(store, u'bill')
        return self._auto_confirm_sale(wizard, app, store, sale, subtotal,
                                       total_paid, payment_method)

    def _auto_confirm_sale_wizard_with_store_credit(self, wizard, app, store, sale,
                                                    subtotal, total_paid,
                                                    current_document):
        sale.client = self._create_client(store)
        payment_method = PaymentMethod.get_by_name(store, u'store_credit')
        return self._auto_confirm_sale(wizard, app, store, sale, subtotal,
                                       total_paid, payment_method)

    def _auto_confirm_sale_wizard_with_trade(self, wizard, app, store, sale,
                                             subtotal, total_paid,
                                             current_document):
        sale.order()
        total_paid = sale.group.get_total_confirmed_value()
        total = sale.get_total_sale_amount() - total_paid
        payment_method = PaymentMethod.get_by_name(store, u'money')
        payment_method.create_payment(Payment.TYPE_IN, sale.group, sale.branch, total)
        self.sale = sale
        return sale

    def _create_client(self, store):
        from stoqlib.domain.address import Address, CityLocation
        from stoqlib.domain.person import Client, Person

        person = Person(name=u'Person', store=store)
        city = CityLocation.get_default(store)
        Address(store=store,
                street=u'Rua Principal',
                streetnumber=123,
                postal_code=u'12345-678',
                is_main_address=True,
                person=person,
                city_location=city)
        client = Client(person=person, store=store)
        client.credit_limit = currency("1000")
        return client

    def _called_once_with_store(self, func, *expected_args):
        args = func.call_args[0]
        for arg, expected in zip(args, expected_args):
            self.assertEquals(arg, expected)

    @mock.patch('stoqlib.database.runtime.StoqlibStore.confirm')
    def test_till_open(self, confirm):
        app = self.create_app(PosApp, u'pos')
        pos = app
        self._pos_open_till(pos)

        self.check_app(app, u'pos-till-open')

    @mock.patch('stoqlib.database.runtime.StoqlibStore.confirm')
    def test_checkout(self, confirm):
        app = self.create_app(PosApp, u'pos')
        pos = app
        self._pos_open_till(pos)

        pos.barcode.set_text(u'1598756984265')
        self.activate(pos.barcode)

        self.check_app(app, u'pos-checkout-pre')

        # Delay the close calls until after the test is done
        close_calls = []

        def close(store):
            if not store in close_calls:
                close_calls.insert(0, store)

        try:
            with mock.patch.object(StoqlibStore, 'close', new=close):
                with mock.patch('stoqlib.gui.fiscalprinter.run_dialog',
                                self._auto_confirm_sale_wizard):
                    self.activate(pos.ConfirmOrder)
                models = self.collect_sale_models(self.sale)
                self.check_app(app, u'pos-checkout-post',
                               models=models)
        finally:
            for store in close_calls:
                store.close()

    @mock.patch('stoqlib.reporting.boleto.warning')
    def test_checkout_with_bill(self, warning):
        app = self.create_app(PosApp, u'pos')
        pos = app
        self._pos_open_till(pos)
        pos.barcode.set_text(u'1598756984265')
        self.activate(pos.barcode)
        self.check_app(app, u'pos-bill-checkout-pre')
        close_calls = []

        def close(store):
            if not store in close_calls:
                close_calls.insert(0, store)

        try:
            with contextlib.nested(
                mock.patch.object(StoqlibStore, 'confirm'),
                mock.patch.object(StoqlibStore, 'close', new=close),
                mock.patch('stoqlib.gui.fiscalprinter.run_dialog',
                           self._auto_confirm_sale_wizard_with_bill)):

                self.activate(pos.ConfirmOrder)
                description = ("Account 'Imbalance' must be a bank account.\n"
                               "You need to configure the bill payment method in "
                               "the admin application and try again")
                warning.assert_called_once_with('Could not print Bill Report',
                                                description=description)
                models = self.collect_sale_models(self.sale)
                self.check_app(app, u'pos-bill-checkout-post', models=models)
        finally:
            for store in close_calls:
                store.close()

    @mock.patch('stoqlib.gui.fiscalprinter.yesno')
    @mock.patch('stoqlib.gui.fiscalprinter.print_report')
    def test_checkout_with_store_credit(self, print_report, yesno):
        app = self.create_app(PosApp, u'pos')
        pos = app
        self._pos_open_till(pos)
        pos.barcode.set_text(u'1598756984265')
        self.activate(pos.barcode)
        self.check_app(app, u'pos-booklets-checkout-pre')
        close_calls = []

        def close(store):
            if not store in close_calls:
                close_calls.insert(0, store)

        try:
            with contextlib.nested(
                mock.patch.object(StoqlibStore, 'confirm'),
                mock.patch.object(StoqlibStore, 'close', new=close),
                mock.patch('stoqlib.gui.fiscalprinter.run_dialog',
                           self._auto_confirm_sale_wizard_with_store_credit)):
                self.activate(pos.ConfirmOrder)

                yesno.assert_called_once_with(
                    'Do you want to print the booklets for this sale?',
                    gtk.RESPONSE_YES, 'Print booklets', "Don't print")
                payments = list(self.sale.group.get_payments_by_method_name(u'store_credit'))
                print_report.assert_called_once_with(BookletReport, payments)

                models = self.collect_sale_models(self.sale)
                self.check_app(app, u'pos-booklets-checkout-post', models=models)
        finally:
            for store in close_calls:
                store.close()

    @mock.patch('stoq.gui.pos.PosApp.run_dialog')
    @mock.patch('stoq.gui.pos.info')
    def test_checkout_with_trade(self, info, run_dialog):
        pos = self._get_pos_with_open_till()
        trade = self.create_trade(trade_value=287)
        run_dialog.return_value = trade
        self.activate(pos.NewTrade)
        self.assertEquals(run_dialog.call_count, 1)
        self.check_app(pos, u'pos-new-trade')

        # Product value = 198
        pos.barcode.set_text(u'6234564656756')
        self.activate(pos.barcode)
        with contextlib.nested(
                mock.patch.object(StoqlibStore, 'confirm'),
                mock.patch.object(StoqlibStore, 'rollback'),
                mock.patch.object(StoqlibStore, 'close'),
                mock.patch('stoqlib.gui.fiscalprinter.run_dialog',
                           self._auto_confirm_sale_wizard_with_trade)):
            self.activate(pos.ConfirmOrder)
            msg = ("Traded value is greater than the new sale's value. "
                   "Please add more items or return it in Sales app, "
                   "then make a new sale")
            info.assert_called_once_with(msg)

            pos.barcode.set_text(u'6234564656756')
            self.activate(pos.barcode)
            pos._current_store = trade.store
            self.activate(pos.ConfirmOrder)

            payments = self.sale.payments
            total = self.sale.get_total_sale_amount() - trade.returned_total
            self.assertEquals(len(list(payments)), 2)
            self.assertEquals(payments[0].value, trade.returned_total)
            self.assertEquals(payments[1].value, total)

    @mock.patch('stoq.gui.pos.PosApp.run_dialog')
    @mock.patch('stoq.gui.pos.info')
    def test_checkout_with_trade_as_discount(self, info, run_dialog):
        pos = self._get_pos_with_open_till()
        trade = self.create_trade(trade_value=198)
        run_dialog.return_value = trade
        self.activate(pos.NewTrade)
        self.assertEquals(run_dialog.call_count, 1)
        self.check_app(pos, u'pos-new-trade-as-discount')

        # Product value = 198
        pos.barcode.set_text(u'6234564656756')
        self.activate(pos.barcode)
        with contextlib.nested(
                self.sysparam(USE_TRADE_AS_DISCOUNT=True),
                mock.patch.object(StoqlibStore, 'confirm'),
                mock.patch.object(StoqlibStore, 'rollback'),
                mock.patch.object(StoqlibStore, 'close'),
                mock.patch('stoqlib.gui.fiscalprinter.run_dialog',
                           self._auto_confirm_sale_wizard_with_trade)):
            self.activate(pos.ConfirmOrder)
            info.assert_called_once_with(
                "Traded value is equal to the new sale's value. "
                "Please add more items or return it in Sales app, "
                "then make a new sale")
            # Product value = 89
            pos.barcode.set_text(u'6985413595971')
            self.activate(pos.barcode)
            # Product value = 503
            pos.barcode.set_text(u'9586249534513')
            self.activate(pos.barcode)
            pos._current_store = trade.store
            self.activate(pos.ConfirmOrder)

            payments = self.sale.payments
            self.assertEquals(self.sale.discount_value, trade.returned_total)
            self.assertEquals(len(list(payments)), 1)
            self.assertEquals(payments[0].value, self.sale.get_total_sale_amount())

    def test_add_sale_item(self):
        app = self.create_app(PosApp, u'pos')
        pos = app
        self._pos_open_till(pos)

        sale_item = TemporarySaleItem(sellable=self.create_sellable(), quantity=1)
        pos.add_sale_item(sale_item)

        assert(sale_item in pos.sale_items)

        self.check_app(app, u'pos-add-sale-item')

    def test_add_package_sale_item(self):
        app = self.create_app(PosApp, u'pos')
        self._pos_open_till(app)

        package = self.create_product(description=u'Package', is_package=True)
        component1 = self.create_product(stock=5, description=u'Component 1')
        component2 = self.create_product(stock=5, description=u'Component 2')
        self.create_product_component(product=package, component=component1)
        self.create_product_component(product=package, component=component2)

        app._add_product_sellable(package.sellable, 1)
        self.assertEquals(len(list(app.sale_items)), 3)

    def test_add_production_sale_item(self):
        pos = self.create_app(PosApp, u'pos')
        self._pos_open_till(pos)

        production = self.create_product(description=u'Production')
        component1 = self.create_product(stock=5, description=u'Component 1')
        self.create_product_component(product=production, component=component1)
        pos._add_product_sellable(production.sellable, 1)
        self.assertEquals(len(list(pos.sale_items)), 1)

    @mock.patch('stoq.gui.pos.PosApp.run_dialog')
    def test_add_service_sellable(self, run_dialog):
        pos = self.create_app(PosApp, u'pos')
        self._pos_open_till(pos)
        service = self.create_service()

        sale_item = TemporarySaleItem(sellable=service.sellable, quantity=2)
        pos.add_sale_item(sale_item)

        service.sellable.barcode = u'99991234'
        pos.barcode.set_text(u'99991234')
        self.activate(pos.barcode)

    def test_quantity_activate(self):
        pos = self.create_app(PosApp, u'pos')
        self._pos_open_till(pos)
        sellable = self.create_sellable()
        sellable.barcode = u'12345678'
        unit = self.create_sellable_unit(u'UN', False)
        sellable.unit = unit

        pos.barcode.set_text(u'12345678')
        # Clear the quantity field
        pos.quantity.set_text("")
        self.assertTrue(bool(pos.quantity.validate() is ValueUnset))
        self.activate(pos.quantity)
        self.assertEquals(len(pos.sale_items), 0)

        # Quantity less than 0
        pos.quantity.update(-1)
        self.assertTrue(bool(pos.quantity.validate() is ValueUnset))
        self.activate(pos.quantity)
        self.assertEquals(len(pos.sale_items), 0)

        # Quantity equal to 0
        pos.quantity.update(0)
        self.assertTrue(bool(pos.quantity.validate() is ValueUnset))
        self.activate(pos.quantity)
        self.assertEquals(len(pos.sale_items), 0)

        # Quantity greater than 0
        pos.quantity.update(1)
        self.activate(pos.quantity)
        self.assertTrue(bool(pos.quantity.validate() is not ValueUnset))
        self.assertEquals(len(pos.sale_items), 1)

    @mock.patch('stoq.gui.pos.POSConfirmSaleEvent.emit')
    def test_pos_confirm_sale_event(self, emit):
        pos = self._get_pos_with_open_till()

        sellable = self.store.find(Sellable)[0]
        sale_item = self._add_product(pos, sellable)

        def mock_confirm(sale, store, savepoint=None,
                         subtotal=None, total_paid=None):
            return True

        with mock.patch.object(pos._coupon, 'confirm', mock_confirm):
            pos.checkout()

        self.assertEquals(emit.call_count, 1)
        args, kwargs = emit.call_args
        self.assertTrue(isinstance(args[0], Sale))
        self.assertEquals(args[1], [sale_item])

    @mock.patch('stoq.gui.pos.yesno')
    def test_can_change_application(self, yesno):
        app = self.create_app(PosApp, u'pos')
        pos = app

        retval = pos.can_change_application()
        self.assertTrue(retval)
        self.assertEqual(yesno.call_count, 0)

        self._pos_open_till(pos)
        pos.barcode.set_text(u'1598756984265')
        self.activate(pos.barcode)

        yesno.return_value = False
        retval = pos.can_change_application()
        self.assertFalse(retval)
        yesno.assert_called_once_with(
            u'You must finish the current sale before '
            u'you change to another application.', gtk.RESPONSE_NO,
            u'Cancel sale', u'Finish sale')

    @mock.patch('stoq.gui.pos.yesno')
    def test_can_close_application(self, yesno):
        pos = self._get_pos_with_open_till()

        # No sale is open yet. We can close application
        retval = pos.can_close_application()
        self.assertTrue(retval)
        self.assertEqual(yesno.call_count, 0)

        # Add item (and open sale)
        pos.barcode.set_text(u'1598756984265')
        self.activate(pos.barcode)

        # Should not be able to close now
        yesno.return_value = False
        retval = pos.can_close_application()
        self.assertFalse(retval)
        yesno.assert_called_once_with(
            u'You must finish or cancel the current sale before '
            u'you can close the POS application.', gtk.RESPONSE_NO,
            u'Cancel sale', u'Finish sale')

    def test_get_sellable_and_batch(self):
        # Testing BarcodeInfo inserted with scale and price mode
        with self.sysparam(SCALE_BARCODE_FORMAT=0, CONFIRM_QTY_ON_BARCODE_ACTIVATE=True):
            pos = self._get_pos_with_open_till()

            sellable = self.create_sellable()
            sellable.price = 100
            sellable.barcode = u'4628'

            # Set a barcode number on the barcode field and activate it
            pos.barcode.set_text('2' + sellable.barcode + '00200000')
            self.activate(pos.barcode)

            self.assertEqual(2, float(pos.quantity.get_text()))

    def test_set_additional_info(self):
        from stoqlib.domain.product import Product

        # The test that requires qty confirmation before adding a product
        with self.sysparam(CONFIRM_QTY_ON_BARCODE_ACTIVATE=True):
            pos = self._get_pos_with_open_till()

            # Set a barcode number on the barcode field and activate it
            sellable = self.store.find(Product)[0].sellable
            pos.barcode.set_text(sellable.code)
            self.activate(pos.barcode)

            self.assertEquals(pos.sellable_description.get_text(), sellable.description)
            self.assertTrue(pos.quantity.is_focus())

        # The product is directly added
        with self.sysparam(CONFIRM_QTY_ON_BARCODE_ACTIVATE=False):
            pos = self._get_pos_with_open_till()

            # Set a barcode number on the barcode field and activate it
            sellable = self.store.find(Product)[0].sellable
            pos.barcode.set_text(sellable.code)
            self.activate(pos.barcode)

            self.assertFalse(pos.sellable_description.get_visible())
            self.assertFalse(pos.quantity.is_focus())

        # A non existing product is added, focus shall remain in barcode entry
        with self.sysparam(CONFIRM_QTY_ON_BARCODE_ACTIVATE=True):
            pos = self._get_pos_with_open_till()

            # Set a barcode number on the barcode field and activate it
            sellable = self.store.find(Product)[0].sellable
            pos.barcode.set_text('01xzp')
            with mock.patch.object(pos, 'run_dialog') as run_dialog:
                run_dialog.return_value = None
                self.assertEquals(run_dialog.call_count, 0)
                self.activate(pos.barcode)
                self.assertEquals(run_dialog.call_count, 1)

            self.assertTrue(pos.barcode.is_focus())

    def test_advanced_search(self):
        pos = self._get_pos_with_open_till()

        pos.barcode.set_text(u'item')
        with mock.patch.object(pos, 'run_dialog') as run_dialog:
            run_dialog.return_value = None
            self.activate(pos.barcode)
            run_dialog.assert_called_once_with(
                SaleSellableSearch, pos.store,
                search_str=u'item',
                sale_items=pos.sale_items,
                quantity=Decimal('1'),
                info_message=(u"The barcode 'item' does not exist. "
                              u"Searching for a product instead..."))

        with mock.patch.object(pos, 'run_dialog') as run_dialog:
            return_value = self.store.find(SellableFullStockView)[0]
            run_dialog.return_value = return_value
            self.activate(pos.barcode)

            # TODO: Create an public api for this
            self.assertTrue(pos._sale_started)

    @mock.patch('stoq.gui.pos.PosApp.run_dialog')
    def test_edit_sale_item(self, run_dialog):
        pos = self._get_pos_with_open_till()

        sellable = self.create_sellable()
        service = self._add_service(pos, sellable)

        olist = pos.sale_items
        olist.select(olist[0])

        self.click(pos.edit_item_button)
        self.assertEquals(run_dialog.call_count, 1)
        args, kwargs = run_dialog.call_args
        editor, store, item = args
        self.assertEquals(editor, ServiceItemEditor)
        self.assertTrue(store is not None)
        self.assertEquals(item.sellable, sellable)
        self.assertEquals(item.service, service)

    @mock.patch('stoq.gui.pos.PosApp.run_dialog')
    def test_new_trade(self, run_dialog):
        pos = self._get_pos_with_open_till()
        trade = self.create_trade()
        run_dialog.return_value = trade

        self.activate(pos.NewTrade)
        self.assertEquals(run_dialog.call_count, 1)

        with mock.patch('stoq.gui.pos.yesno') as yesno:
            self.activate(pos.NewTrade)
            message = (u"There is already a trade in progress... Do you "
                       u"want to cancel it and start a new one?")
            yesno.assert_called_once_with(message, gtk.RESPONSE_NO,
                                          u"Cancel trade", u"Finish trade")

    @mock.patch('stoq.gui.pos.PosApp.run_dialog')
    def test_cancel_trade(self, run_dialog):
        pos = self._get_pos_with_open_till()
        trade = self.create_trade()
        run_dialog.return_value = trade
        self.activate(pos.NewTrade)

        self.assertIsNotNone(pos._trade_infobar)

        value = converter.as_string(currency, trade.returned_total)
        msg = (("There is a trade with value %s in progress...\n"
                "When checking out, it will be used as part of "
                "the payment.") % value)
        self.assertEquals(pos._trade_infobar.label.get_label(), msg)

        remove_button = pos._trade_infobar.get_action_area().get_children()[0]
        with mock.patch('stoq.gui.pos.yesno') as yesno:
            self.click(remove_button)
            yesno.assert_called_once_with(
                "Do you really want to cancel the trade in progress?",
                gtk.RESPONSE_NO, "Cancel trade", "Don't cancel")

    @mock.patch('stoq.gui.pos.yesno')
    def test_cancel_order(self, yesno):
        pos = self._get_pos_with_open_till()

        sale_item = self._add_product(pos, self.create_sellable())

        olist = pos.sale_items
        olist.select(olist[0])

        self.activate(pos.CancelOrder)
        yesno.assert_called_once_with(u'This will cancel the current order. Are '
                                      u'you sure?', gtk.RESPONSE_NO,
                                      u"Don't cancel", u"Cancel order")

        self.assertEquals(olist[0], sale_item)

    @mock.patch('stoq.gui.pos.PosApp.run_dialog')
    def test_create_delivery(self, run_dialog):
        delivery = _CreateDeliveryModel(Decimal('150'))
        delivery.notes = u'notes about the delivery'
        delivery.client = self.create_client()
        delivery.transporter = self.create_transporter()
        delivery.address = self.create_address()
        run_dialog.return_value = delivery

        pos = self._get_pos_with_open_till()

        sale_item = self._add_product(pos, self.create_sellable())

        olist = pos.sale_items
        olist.select(olist[0])

        self.activate(pos.NewDelivery)
        self.assertEquals(run_dialog.call_count, 1)
        args, kwargs = run_dialog.call_args
        editor, store, delivery = args
        self.assertEquals(editor, CreateDeliveryEditor)
        self.assertTrue(store is not None)
        self.assertEquals(delivery, None)
        self.assertEquals(kwargs[u'sale_items'], [sale_item])

    def test_remove_item(self):
        pos = self._get_pos_with_open_till()

        self._add_product(pos, self.create_sellable())

        olist = pos.sale_items
        olist.select(olist[0])

        self.click(pos.remove_item_button)
        self.assertEquals(len(olist), 0)

    def test_remove_package_item(self):
        pos = self._get_pos_with_open_till()
        package = self.create_product(description=u'Package', is_package=True)
        component = self.create_product(stock=5, description=u'Component')
        self.create_product_component(product=package, component=component)
        pos._add_product_sellable(package.sellable, 1)

        otree = pos.sale_items
        self.assertEquals(len(list(otree)), 2)

        # Selecting the child
        otree.select_paths([(0, 0)])
        # We shouldnt be able to remove children
        self.assertNotSensitive(pos, ['remove_item_button'])

        otree.select(otree[0])
        self.click(pos.remove_item_button)
        # As we remove the parent, we should be removing the children as well
        self.assertEquals(len(list(otree)), 0)

    @mock.patch('stoq.gui.pos.yesno')
    def test_close_till_with_open_sale(self, yesno):
        pos = self._get_pos_with_open_till()

        self._add_product(pos, self.create_sellable())

        with mock.patch.object(pos._printer, 'close_till'):
            self.activate(pos.TillClose)
            yesno.assert_called_once_with(u'You must finish or cancel the current '
                                          u'sale before you can close the till.',
                                          gtk.RESPONSE_NO, u"Cancel sale", u"Finish sale")

    @mock.patch('stoq.gui.pos.PosApp.run_dialog')
    def test_activate_menu_options(self, run_dialog):
        pos = self._get_pos_with_open_till()

        sale_item = self._add_product(pos, self.create_sellable())

        olist = pos.sale_items
        olist.select(olist[0])

        self.activate(pos.Clients)
        self.assertEquals(run_dialog.call_count, 1)
        args, kwargs = run_dialog.call_args
        dialog, store = args
        self.assertEquals(dialog, ClientSearch)
        self.assertTrue(store is not None)

        self.activate(pos.SoldItemsByBranchSearch)
        self.assertEquals(run_dialog.call_count, 2)
        args, kwargs = run_dialog.call_args
        dialog, store = args
        self.assertEquals(dialog, SoldItemsByBranchSearch)
        self.assertTrue(store is not None)

        self.activate(pos.ProductSearch)
        self.assertEquals(run_dialog.call_count, 3)
        args, kwargs = run_dialog.call_args
        dialog, store = args
        self.assertEquals(dialog, ProductSearch)
        self.assertTrue(store is not None)

        self.activate(pos.ServiceSearch)
        self.assertEquals(run_dialog.call_count, 4)
        args, kwargs = run_dialog.call_args
        dialog, store = args
        self.assertEquals(dialog, ServiceSearch)
        self.assertTrue(store is not None)

        self.activate(pos.DeliverySearch)
        self.assertEquals(run_dialog.call_count, 5)
        args, kwargs = run_dialog.call_args
        dialog, store = args
        self.assertEquals(dialog, DeliverySearch)
        self.assertTrue(store is not None)

        with mock.patch('stoq.gui.pos.api', new=self.fake.api):
            self.fake.set_retval(sale_item)
            self.activate(pos.Sales)

            self.assertEquals(run_dialog.call_count, 6)
            args, kwargs = run_dialog.call_args
            dialog, store = args
            self.assertEquals(dialog, SaleWithToolbarSearch)
            self.assertTrue(store is not None)
