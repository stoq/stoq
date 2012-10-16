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

import datetime
import mock

from stoqlib.api import api

from stoq.gui.purchase import PurchaseApp
from stoq.gui.test.baseguitest import BaseGUITest


class TestPurchase(BaseGUITest):
    def testInitial(self):
        api.sysparam(self.trans).update_parameter('SMART_LIST_LOADING', '0')
        app = self.create_app(PurchaseApp, 'purchase')
        for purchase in app.main_window.results:
            purchase.open_date = datetime.datetime(2012, 1, 1)
        self.check_app(app, 'purchase')

    @mock.patch('stoq.gui.purchase.PurchaseApp.run_dialog')
    def testNewQuote(self, run_dialog):
        api.sysparam(self.trans).update_parameter('SMART_LIST_LOADING', '0')
        purchase = self.create_purchase_order()

        app = self.create_app(PurchaseApp, 'purchase')
        for purchase in app.main_window.results:
            purchase.open_date = datetime.datetime(2012, 1, 1)
        olist = app.main_window.results
        olist.select(olist[0])

        with mock.patch('stoq.gui.purchase.api', new=self.fake.api):
            self.fake.set_retval(purchase)
            self.activate(app.main_window.NewQuote)
