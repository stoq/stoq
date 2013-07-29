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

import mock

from stoq.gui.launcher import LauncherApp, COL_APP
from stoq.gui.test.baseguitest import BaseGUITest


class TestLauncher(BaseGUITest):
    def test_initial(self):
        app = self.create_app(LauncherApp, u'launcher')
        self.check_app(app, u'launcher')

    def test_open_admin(self):
        self._test_open_app('admin')

    def test_open_payable(self):
        self._test_open_app('payable')

    def test_open_receivable(self):
        self._test_open_app('receivable')

    def test_open_services(self):
        self._test_open_app('services')

    def test_open_financial(self):
        self._test_open_app('financial')

    def test_open_stock(self):
        self._test_open_app('stock')

    # FIXME: override localnow()
    #def test_open_sales(self):
    #    self._test_open_app('sales')

    # FIXME: override localnow()
    #def test_open_purchase(self):
    #    self._test_open_app('purchase')

    def test_open_production(self):
        self._test_open_app('production')

    def test_open_inventory(self):
        self._test_open_app('inventory')

    def test_open_till(self):
        self._test_open_app('till')

    def test_open_pos(self):
        self._test_open_app('pos')

    # FIXME: This should open a random port
    #def test_open_calendar(self):
    #    self._test_open_app('calendar')

    def _test_open_app(self, app_name):
        app = self.create_app(LauncherApp, u'launcher')
        emitname = 'stoq.gui.shell.shellwindow.StartApplicationEvent.emit'
        for row in app.model:
            if row[COL_APP].name == app_name:
                with mock.patch(emitname) as emit:
                    app.iconview.item_activated(row.path)
                    self.check_app(app, u'launcher-app-' + app_name)
                break
        else:
            raise AssertionError

        emit.assert_called_once_with(self.window.current_app.app_name,
                                     self.window.current_app)
