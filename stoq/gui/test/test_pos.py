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

from decimal import Decimal
import mock
import gtk


from stoqlib.api import api
from stoqlib.database.runtime import StoqlibTransaction
from stoqlib.domain.events import TillOpenEvent
from stoqlib.domain.payment.method import PaymentMethod
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
from stoqlib.gui.search.sellablesearch import SellableSearch
from stoqlib.gui.search.servicesearch import ServiceSearch

from stoq.gui.pos import PosApp, TemporarySaleItem
from stoq.gui.test.baseguitest import BaseGUITest


class TestPos(BaseGUITest):
    def testInitial(self):
        app = self.create_app(PosApp, 'pos')
        self.check_app(app, 'pos')

    def _open_till(self, trans):
        till = Till(connection=trans,
                    station=api.get_current_station(trans))
        till.open_till()

        TillOpenEvent.emit(till=till)
        self.assertEquals(till, Till.get_current(trans))
        return till

    def _pos_open_till(self, pos):
        with mock.patch('stoqlib.gui.fiscalprinter.run_dialog') as run_dialog:
            self.activate(pos.TillOpen)
            self._called_once_with_trans(run_dialog, TillOpeningEditor, pos)

    def _get_pos_with_open_till(self):
        app = self.create_app(PosApp, 'pos')
        pos = app.main_window
        self._pos_open_till(pos)
        return pos

    def _add_product(self, pos, sellable):
        sale_item = TemporarySaleItem(sellable=sellable, quantity=1)
        pos.add_sale_item(sale_item)
        return sale_item

    def _add_service(self, pos, sellable):
        service = Service(sellable=sellable, connection=self.trans)
        self._add_product(pos, sellable)
        return service

    def _auto_confirm_sale_wizard(self, wizard, app, trans, sale):
        # This is in another transaction and as we want to avoid committing
        # we need to open the till again
        self._open_till(trans)

        sale.order()
        money_method = PaymentMethod.get_by_name(trans, 'money')
        total = sale.get_total_sale_amount()
        money_method.create_inpayment(sale.group, sale.branch, total)
        self.sale = sale
        return sale

    def _called_once_with_trans(self, func, *expected_args):
        args = func.call_args[0]
        for arg, expected in zip(args, expected_args):
            self.assertEquals(arg, expected)

    @mock.patch.object(api, 'finish_transaction')
    def testTillOpen(self, finish_transaction):
        app = self.create_app(PosApp, 'pos')
        pos = app.main_window
        self._pos_open_till(pos)

        self.check_app(app, 'pos-till-open')

    @mock.patch.object(api, 'finish_transaction')
    def testCheckout(self, finish_transaction):
        app = self.create_app(PosApp, 'pos')
        pos = app.main_window
        self._pos_open_till(pos)

        pos.barcode.set_text('1598756984265')
        self.activate(pos.barcode)

        self.check_app(app, 'pos-checkout-pre')

        # Delay the close calls until after the test is done
        close_calls = []

        def close(trans):
            if not trans in close_calls:
                close_calls.insert(0, trans)

        try:
            with mock.patch.object(StoqlibTransaction, 'close', new=close):
                with mock.patch('stoqlib.gui.fiscalprinter.run_dialog',
                                self._auto_confirm_sale_wizard):
                    self.activate(pos.ConfirmOrder)
                models = self.collect_sale_models(self.sale)
                self.check_app(app, 'pos-checkout-post',
                               models=models)
        finally:
            for trans in close_calls:
                trans.close()

    def testAddSaleItem(self):
        app = self.create_app(PosApp, 'pos')
        pos = app.main_window
        self._pos_open_till(pos)

        sale_item = TemporarySaleItem(sellable=self.create_sellable(), quantity=1)
        pos.add_sale_item(sale_item)

        assert(sale_item in pos.sale_items)

        self.check_app(app, 'pos-add-sale-item')

    @mock.patch('stoq.gui.pos.POSConfirmSaleEvent.emit')
    def testPOSConfirmSaleEvent(self, emit):
        pos = self._get_pos_with_open_till()

        sellable = Sellable.select(connection=self.trans)[0]
        sale_item = self._add_product(pos, sellable)

        def mock_confirm(sale, trans):
            return True

        with mock.patch.object(pos._coupon, 'confirm', mock_confirm):
            pos.checkout()

        self.assertEquals(emit.call_count, 1)
        args, kwargs = emit.call_args
        self.assertTrue(isinstance(args[0], Sale))
        self.assertEquals(args[1], [sale_item])

    @mock.patch('stoq.gui.pos.yesno')
    def test_can_change_application(self, yesno):
        app = self.create_app(PosApp, 'pos')
        pos = app.main_window

        retval = pos.can_change_application()
        self.assertTrue(retval)
        self.assertEqual(yesno.call_count, 0)

        self._pos_open_till(pos)
        pos.barcode.set_text('1598756984265')
        self.activate(pos.barcode)

        yesno.return_value = False
        retval = pos.can_change_application()
        self.assertFalse(retval)
        yesno.assert_called_once_with('You must finish the current sale before '
            'you change to another application.', gtk.RESPONSE_NO, 'Cancel sale', 'Finish sale')

    @mock.patch('stoq.gui.pos.yesno')
    def test_can_close_application(self, yesno):
        pos = self._get_pos_with_open_till()

        # No sale is open yet. We can close application
        retval = pos.can_close_application()
        self.assertTrue(retval)
        self.assertEqual(yesno.call_count, 0)

        # Add item (and open sale)
        pos.barcode.set_text('1598756984265')
        self.activate(pos.barcode)

        # Should not be able to close now
        yesno.return_value = False
        retval = pos.can_close_application()
        self.assertFalse(retval)
        yesno.assert_called_once_with('You must finish or cancel the current sale before '
            'you can close the POS application.', gtk.RESPONSE_NO, 'Cancel sale', 'Finish sale')

    def test_advanced_search(self):
        pos = self._get_pos_with_open_till()

        pos.barcode.set_text('item')
        with mock.patch.object(pos, 'run_dialog') as run_dialog:
            run_dialog.return_value = None
            self.activate(pos.barcode)
            run_dialog.assert_called_once_with(SellableSearch, pos.conn,
                    selection_mode=gtk.SELECTION_BROWSE,
                    search_str='item',
                    sale_items=pos.sale_items,
                    quantity=Decimal('1'),
                    double_click_confirm=True,
                    info_message=("The barcode 'item' does not exist. "
                                  "Searching for a product instead..."))

        with mock.patch.object(pos, 'run_dialog') as run_dialog:
            return_value = SellableFullStockView.select(connection=self.trans)[0]
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
        editor, trans, item = args
        self.assertEquals(editor, ServiceItemEditor)
        self.assertTrue(trans is not None)
        self.assertEquals(item.sellable, sellable)
        self.assertEquals(item.service, service)

    @mock.patch('stoq.gui.pos.yesno')
    def test_cancel_order(self, yesno):
        pos = self._get_pos_with_open_till()

        sale_item = self._add_product(pos, self.create_sellable())

        olist = pos.sale_items
        olist.select(olist[0])

        self.activate(pos.CancelOrder)
        yesno.assert_called_once_with('This will cancel the current order. Are '
                                      'you sure?', gtk.RESPONSE_NO,
                                      "Don't cancel", "Cancel order")

        self.assertEquals(olist[0], sale_item)

    @mock.patch('stoq.gui.pos.PosApp.run_dialog')
    def test_create_delivery(self, run_dialog):
        delivery = _CreateDeliveryModel(Decimal('150'))
        delivery.notes = 'notes about the delivery'
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
        editor, trans, delivery = args
        self.assertEquals(editor, CreateDeliveryEditor)
        self.assertTrue(trans is not None)
        self.assertEquals(delivery, None)
        self.assertEquals(kwargs['sale_items'], [sale_item])

    def test_remove_item(self):
        pos = self._get_pos_with_open_till()

        self._add_product(pos, self.create_sellable())

        olist = pos.sale_items
        olist.select(olist[0])

        self.click(pos.remove_item_button)
        self.assertEquals(len(olist), 0)

    @mock.patch('stoq.gui.pos.yesno')
    def test_close_till_with_open_sale(self, yesno):
        pos = self._get_pos_with_open_till()

        self._add_product(pos, self.create_sellable())

        with mock.patch.object(pos._printer, 'close_till'):
            self.activate(pos.TillClose)
            yesno.assert_called_once_with('You must finish or cancel the current '
                                          'sale before you can close the till.',
                                          gtk.RESPONSE_NO, "Cancel sale", "Finish sale")

    @mock.patch('stoq.gui.pos.PosApp.run_dialog')
    def test_activate_menu_options(self, run_dialog):
        pos = self._get_pos_with_open_till()

        sale_item = self._add_product(pos, self.create_sellable())

        olist = pos.sale_items
        olist.select(olist[0])

        self.activate(pos.Clients)
        self.assertEquals(run_dialog.call_count, 1)
        args, kwargs = run_dialog.call_args
        dialog, trans = args
        self.assertEquals(dialog, ClientSearch)
        self.assertTrue(trans is not None)

        self.activate(pos.SoldItemsByBranchSearch)
        self.assertEquals(run_dialog.call_count, 2)
        args, kwargs = run_dialog.call_args
        dialog, trans = args
        self.assertEquals(dialog, SoldItemsByBranchSearch)
        self.assertTrue(trans is not None)

        self.activate(pos.ProductSearch)
        self.assertEquals(run_dialog.call_count, 3)
        args, kwargs = run_dialog.call_args
        dialog, trans = args
        self.assertEquals(dialog, ProductSearch)
        self.assertTrue(trans is not None)

        self.activate(pos.ServiceSearch)
        self.assertEquals(run_dialog.call_count, 4)
        args, kwargs = run_dialog.call_args
        dialog, trans = args
        self.assertEquals(dialog, ServiceSearch)
        self.assertTrue(trans is not None)

        self.activate(pos.DeliverySearch)
        self.assertEquals(run_dialog.call_count, 5)
        args, kwargs = run_dialog.call_args
        dialog, trans = args
        self.assertEquals(dialog, DeliverySearch)
        self.assertTrue(trans is not None)

        with mock.patch('stoq.gui.pos.api', new=self.fake.api):
            self.fake.set_retval(sale_item)
            self.activate(pos.Sales)

            self.assertEquals(run_dialog.call_count, 6)
            args, kwargs = run_dialog.call_args
            dialog, trans = args
            self.assertEquals(dialog, SaleWithToolbarSearch)
            self.assertTrue(trans is not None)
