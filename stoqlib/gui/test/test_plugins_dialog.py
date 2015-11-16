# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

import mock
import gtk

from stoqlib.gui.dialogs.pluginsdialog import PluginManagerDialog
from stoqlib.gui.test.uitestutils import GUITest


class TestPluginManagerDialog(GUITest):
    @mock.patch('stoqlib.gui.dialogs.pluginsdialog.info')
    @mock.patch('stoqlib.gui.dialogs.pluginsdialog.yesno')
    def test_confirm(self, yesno, info):
        yesno.return_value = True

        dialog = PluginManagerDialog(self.store)
        oficial_plugins = self.get_oficial_plugins_names()
        # Only list the oficial plugins (the ones on this repository), since
        # plugins on the same checkout dir will be identified too
        # and listed here, making the test fail with a false positive
        for item in dialog.klist[:]:
            if item.name not in oficial_plugins:
                dialog.klist.remove(item)

        # Make sure all oficial plugins and only them are on the list
        self.assertEqual(set(i.name for i in dialog.klist), oficial_plugins)
        dialog.klist.select(dialog.klist[0])
        self.check_dialog(dialog, 'dialog-plugin-manager-confirm')

        with mock.patch.object(dialog._manager, 'install_plugin') as install:
            with mock.patch.object(dialog._manager, 'activate_plugin') as activate:
                self.click(dialog.ok_button)
                install.assert_called_once_with(dialog.klist[0].name)
                activate.assert_called_once_with(dialog.klist[0].name)

        yesno.assert_called_once_with('Are you sure you want activate this '
                                      'plugin?\nPlease note that, once '
                                      'activated you will not be able to '
                                      'disable it.', gtk.RESPONSE_NO,
                                      'Activate plugin', 'Not now')
