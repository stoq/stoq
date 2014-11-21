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

from stoqlib.gui.dialogs.importerdialog import ImporterDialog
from stoqlib.gui.test.uitestutils import GUITest


class TestImporterDialog(GUITest):
    @mock.patch('stoqlib.gui.dialogs.progressbardialog.ProcessView.execute_command')
    def test_show(self, execute_command):
        dialog = ImporterDialog('format', 'filename')
        self.check_dialog(dialog, 'dialog-importer-show')

        self.assertEquals(execute_command.call_count, 1)
        args, kwargs = execute_command.call_args

        args = args[0]
        self.assertEquals(args[:8], ['stoq', 'dbadmin', 'import', '-t', 'format',
                                     '--import-filename', 'filename', '-v'])
