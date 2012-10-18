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

from stoqlib.api import api
from stoqlib.gui.uitestutils import GUITest
from stoq.gui.application import App
from stoq.gui.launcher import Launcher

import stoq

gtk.set_interactive(False)


class BaseGUITest(GUITest):
    def create_app(self, app, app_name):
        api.user_settings.set('actual-version', stoq.stoq_version)
        self.user = api.get_current_user(self.trans)
        self.profile = self.create_profile_settings(self.user.profile, app_name)
        self.shell = mock.Mock()
        self.options = mock.Mock(spec=['debug'])
        self.options.debug = False
        self.launcher = Launcher(self.options, self.shell, conn=self.trans)
        self.launcher.app.in_ui_test = True
        self.launcher.add_info_bar = lambda *x: None
        self.launcher.statusbar.push(0, 'Test Statusbar test')
        self.launcher.main_vbox.remove(self.launcher.iconview_vbox)
        app = App(app, None, self.options, self.shell, True,
                  self.launcher, app_name, conn=self.trans)
        app.show()
        return app
