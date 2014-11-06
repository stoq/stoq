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
from stoqlib.gui.base.messagebar import MessageBar
from stoqlib.gui.test.uitestutils import GUITest

import stoq
from stoq.gui.shell.shellapp import ShellApp
from stoq.gui.shell.shellwindow import ShellWindow

gtk.set_interactive(False)


class MockShellWindow(ShellWindow):
    in_ui_test = True

    def add_info_bar(self, message_type, label, action_widget=None):
        infobar = MessageBar(label, message_type)
        assert infobar is not None

        if action_widget:
            infobar.add_action_widget(action_widget, 0)
            action_widget.show()
        infobar.show()

        self.main_vbox.pack_start(infobar, False, False, 0)
        self.main_vbox.reorder_child(infobar, 2)

        return infobar


class BaseGUITest(GUITest):
    def setUp(self):
        original_refresh = ShellApp.refresh
        # We need to do do this mock since the store here doesn't get
        # confirmed, so an action to an item that results in the results
        # getting refreshed would make the results disapear
        self._refresh_mock = mock.patch(
            'stoq.gui.shell.shellapp.ShellApp.refresh',
            new=lambda s, rollback=False: original_refresh(s, rollback=False))

        self._refresh_mock.start()
        super(BaseGUITest, self).setUp()

    def tearDown(self):
        super(BaseGUITest, self).tearDown()
        self._refresh_mock.stop()

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
        self.window = MockShellWindow(self.options, self.shell, store=self.store)
        self.window.in_ui_test = True
        self.window.statusbar.push(0, u'Test Statusbar test')

        shell_app = self.window.run_application(app_name)
        assert shell_app is not None
        return shell_app
