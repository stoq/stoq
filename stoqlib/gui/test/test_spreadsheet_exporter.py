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

import gtk
import mock

from kiwi.ui.objectlist import ObjectList

from stoqlib.api import api
from stoqlib.gui.dialogs.spreadsheetexporterdialog import SpreadSheetExporter
from stoqlib.gui.test.uitestutils import GUITest


class TestXLSExporter(GUITest):

    def _run_exporter(self, sse):
        objectlist = ObjectList()
        path = 'stoqlib.gui.dialogs.spreadsheetexporterdialog.gio.app_info_get_default_for_type'
        with mock.patch(path) as gio:
            app_info = mock.Mock()
            app_info.get_name.return_value = 'App Name'
            gio.return_value = app_info
            sse.export(object_list=objectlist,
                       name='Title', filename_prefix='name-prefix')

    def test_export_open(self):
        api.user_settings.set('spreadsheet-action', 'open')

        sse = SpreadSheetExporter()
        with mock.patch.object(sse, '_open_application') as _open:
            self._run_exporter(sse)
            self.assertTrue(_open.call_count, 1)

    @mock.patch('stoqlib.gui.dialogs.spreadsheetexporterdialog.yesno')
    def test_export_ask(self, yesno):
        # XXX: We should not be using yesno for a save/open question
        yesno.return_value = False

        api.user_settings.set('spreadsheet-action', 'ask')

        sse = SpreadSheetExporter()
        with mock.patch.object(sse, '_open_application') as _open:
            self._run_exporter(sse)
            self.assertTrue(_open.call_count, 1)

        yesno.assert_called_once_with(
            ('A spreadsheet has been created, what do '
             'you want to do with it?'), gtk.RESPONSE_NO, 'Save it to disk',
            'Open with App Name')
