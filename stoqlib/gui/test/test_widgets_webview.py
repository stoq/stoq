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

from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.widgets.webview import WebView


class TestWebView(GUITest):
    @mock.patch('stoqlib.gui.widgets.webview.run_dialog')
    @mock.patch('stoqlib.gui.widgets.webview.api.new_store')
    def test_dialog_payment_details(self, new_store, run_dialog):
        new_store.return_value = self.store

        payment = self.create_payment()
        web_view = WebView()
        web_view.app = None
        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                web_view._dialog_payment_details(id=payment.id)

    @mock.patch('stoqlib.gui.widgets.webview.run_dialog')
    @mock.patch('stoqlib.gui.widgets.webview.api.new_store')
    def test_dialog_purchase(self, new_store, run_dialog):
        new_store.return_value = self.store

        purchase = self.create_purchase_order()
        web_view = WebView()
        web_view.app = None
        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                web_view._dialog_purchase(id=purchase.id)

    @mock.patch('stoqlib.gui.widgets.webview.run_dialog')
    @mock.patch('stoqlib.gui.widgets.webview.api.new_store')
    def test__dialog_call(self, new_store, run_dialog):
        new_store.return_value = self.store
        call = self.create_call()
        web_view = WebView()
        web_view.app = None
        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                web_view._dialog_purchase(id=call.id)
