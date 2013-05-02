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
from stoqlib.domain.profile import ProfileSettings
from stoqlib.gui.uitestutils import GUITest
from stoq.gui.shell.shellwindow import ShellWindow

import stoq

gtk.set_interactive(False)


class BaseGUITest(GUITest):
    def create_app(self, window_class, app_name):
        self.user = api.get_current_user(self.store)
        # FIXME: Perhaps we should just ignore permission checking, it'll
        #        save quite a few selects
        settings = self.store.find(ProfileSettings, app_dir_name=app_name,
                                   user_profile=self.user.profile).one()
        if settings is None:
            settings = self.create_profile_settings(self.user.profile, app_name)

        api.user_settings.set(u'actual-version', stoq.stoq_version)
        self.shell = mock.Mock()
        self.options = mock.Mock(spec=[u'debug'])
        self.options.debug = False
        self.window = ShellWindow(self.options, self.shell, store=self.store)
        self.window.in_ui_test = True
        self.window.add_info_bar = lambda *x: None
        self.window.statusbar.push(0, u'Test Statusbar test')

        shell_app = self.window.run_application(app_name)
        return shell_app
