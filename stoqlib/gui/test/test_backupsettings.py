# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013-2015 Async Open Source <http://www.async.com.br>
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
from kiwi.python import Settable
import mock

from stoqlib.gui.editors.backupsettings import BackupSettingsEditor
from stoqlib.gui.test.uitestutils import GUITest


class TestWorkOrderEditor(GUITest):
    def test_create(self):
        editor = BackupSettingsEditor(self.store, Settable(key='123456'))
        self.check_editor(editor, 'editor-backup-settings')

    def test_validate_confirm(self):
        editor = BackupSettingsEditor(self.store, Settable(key='123456'))

        with mock.patch('stoqlib.gui.editors.backupsettings.yesno') as yesno:
            self.assertTrue(editor.validate_confirm())
            self.assertNotCalled(yesno)

        with mock.patch('stoqlib.gui.editors.backupsettings.yesno') as yesno:
            editor.model.key = '321'
            yesno.return_value = False
            self.assertFalse(editor.validate_confirm())
            self.assertCalledOnceWith(
                yesno,
                ("Changing the backup key will make any backup done with "
                 "the previous key unrecoverable. Are you sure?"),
                gtk.RESPONSE_NO, "Change", "Keep old key")

        with mock.patch('stoqlib.gui.editors.backupsettings.yesno') as yesno:
            editor.model.key = '321'
            yesno.return_value = True
            self.assertTrue(editor.validate_confirm())
            self.assertCalledOnceWith(
                yesno,
                ("Changing the backup key will make any backup done with "
                 "the previous key unrecoverable. Are you sure?"),
                gtk.RESPONSE_NO, "Change", "Keep old key")

    def test_key_validate(self):
        editor = BackupSettingsEditor(
            self.store, Settable(key='1234567890'))
        self.assertValid(editor, ['key'])

        editor.key.update('123')
        self.assertInvalid(editor, ['key'])

        editor.key.update('0987654321')
        self.assertValid(editor, ['key'])
