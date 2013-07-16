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

import datetime
import mock
import unittest
from stoqlib.gui.editors.accounteditor import AccountEditor

from stoqlib.gui.editors.accounttransactioneditor import AccountTransactionEditor
from stoqlib.gui.test.uitestutils import GUITest


class TestAccountTransactionEditor(GUITest):
    def test_create(self):
        account = self.create_account()
        editor = AccountTransactionEditor(self.store, None, account)

        editor.date.update(datetime.date.today())
        self.check_editor(editor, 'editor-transaction-create')

    def test_show(self):
        account = self.create_account()
        transaction = self.create_account_transaction(account)
        editor = AccountTransactionEditor(self.store, transaction, account)
        editor.date.update(datetime.date.today())

        self.check_editor(editor, 'editor-transaction-show')

    def test_confirm(self):
        account = self.create_account()
        editor = AccountTransactionEditor(self.store, None, account)

        self.assertFalse(editor.validate_confirm())

        editor.description.update('description')
        editor.code.update(15)
        editor.value.update(150)

        self.assertTrue(editor.validate_confirm())

        editor.main_dialog.confirm()
        self.check_editor(editor, 'editor-transaction-confirm',
                          [editor.retval, account])

    @mock.patch('stoqlib.gui.editors.accounttransactioneditor.api.new_store')
    @mock.patch('stoqlib.gui.editors.accounttransactioneditor.run_dialog')
    def test_add_account(self, run_dialog, new_store):
        new_account = self.create_account()
        new_store.return_value = self.store
        run_dialog.return_value = new_account
        editor = AccountTransactionEditor(self.store, None, new_account)
        parent_account = editor._get_account()

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.click(editor.add_account)
                run_dialog.assert_called_once_with(AccountEditor, editor,
                                                   self.store,
                                                   parent_account=parent_account)


if __name__ == '__main__':
    from stoqlib.api import api
    c = api.prepare_test()
    unittest.main()
