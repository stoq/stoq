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

from kiwi.component import provide_utility
import mock
from twisted.trial.unittest import SkipTest

from stoqlib.api import api
from stoqlib.gui.uitestutils import GUITest
from stoqlib.lib.interfaces import  IApplicationDescriptions
from stoq.gui.application import App
from stoq.gui.launcher import Launcher
from stoq.gui.payable import PayableApp
from stoq.lib.applist import ApplicationDescriptions

provide_utility(IApplicationDescriptions, ApplicationDescriptions(), replace=True)


class TestPayable(GUITest):
    def create_app(self, app_name):
        self.user = api.get_current_user(self.trans)
        self.profile = self.create_profile_settings(self.user.profile, app_name)
        self.shell = mock.Mock()
        self.options = mock.Mock(spec=['debug'])
        self.options.debug = False
        self.launcher = Launcher(self.options, self.shell, conn=self.trans)
        self.launcher.app.in_ui_test = True
        self.launcher.add_info_bar = lambda *x: None
        app = App(PayableApp, None, self.options, self.shell, True,
                  self.launcher, app_name)
        app.show()
        return app

    def testInitial(self):
        raise SkipTest("running this test on anthem via xvfb doesn't work") 
        api.sysparam(self.trans).update_parameter('SMART_LIST_LOADING', '0')
        app = self.create_app('payable')
        self.launcher.statusbar.push(0, 'Test Statusbar test')
        self.check_dialog(app.main_window, 'app-payable')
