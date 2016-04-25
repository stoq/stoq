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

from stoqlib.gui.dialogs.branchdialog import BranchDialog
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.api import api


class TestBranchDialog(GUITest):
    @mock.patch('stoqlib.gui.dialogs.branchdialog.create_main_branch')
    def test_create(self, create_main_branch):
        create_main_branch.return_value = api.get_current_branch(self.store)

        editor = BranchDialog(self.store)
        self.check_editor(editor, 'dialog-branch-create',
                          models=[editor.model])

    @mock.patch('stoqlib.gui.dialogs.branchdialog.create_main_branch')
    def test_confirm(self, create_main_branch):
        create_main_branch.return_value = api.get_current_branch(self.store)
        editor = BranchDialog(self.store)
        editor.name.set_text('minha empresa')
        editor.cnpj.set_text('00.000.000/0000-00')
        self.click(editor.main_dialog.ok_button)

    @mock.patch('stoqlib.gui.dialogs.branchdialog.create_main_branch')
    def test_validators(self, create_main_branch):
        create_main_branch.return_value = api.get_current_branch(self.store)
        editor = BranchDialog(self.store)
        editor.name.set_text('minha empresa')
        editor.cnpj.set_text('00.000.000/0000-01')
        self.assertNotSensitive(editor.main_dialog, ['ok_button'])

        editor.cnpj.set_text('00.000.000/0000-00')
        self.assertSensitive(editor.main_dialog, ['ok_button'])
