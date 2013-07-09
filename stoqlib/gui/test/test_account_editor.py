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

import unittest

from stoqlib.domain.account import Account
from stoqlib.gui.editors.accounteditor import AccountEditor
from stoqlib.gui.test.uitestutils import GUITest


class TestAccountEditor(GUITest):
    def test_create(self):
        editor = AccountEditor(self.store)
        self.check_editor(editor, 'editor-account-create')

    def test_confirm(self):
        editor = AccountEditor(self.store)
        self.assertFalse(editor.validate_confirm())
        editor.description.update('Account name')
        self.assertTrue(editor.validate_confirm())
        editor.main_dialog.confirm()
        self.check_editor(editor, 'editor-account-confirm',
                          [editor.retval])

    def test_show(self):
        account = self.create_account()
        editor = AccountEditor(self.store, account)
        # Created account must not be in accounts tree of editor.
        self.assertFalse(editor.parent_accounts.get_account_by_id(account.id))
        self.check_editor(editor, 'editor-account-show')

    def test_show_banco_do_brasil(self):
        account = self.create_account()
        account.account_type = Account.TYPE_BANK
        editor = AccountEditor(self.store, account)
        editor.bank_type.select_item_by_data(1)
        self.assertFalse(editor.parent_accounts.get_account_by_id(account.id))
        self.check_editor(editor, 'editor-account-show-banco-do-brasil')

    def test_show_banrisul(self):
        account = self.create_account()
        account.account_type = Account.TYPE_BANK
        editor = AccountEditor(self.store, account)
        editor.bank_type.select_item_by_data(41)
        self.assertFalse(editor.parent_accounts.get_account_by_id(account.id))
        self.check_editor(editor, 'editor-account-show-banrisul')

    def test_show_bradesco(self):
        account = self.create_account()
        account.account_type = Account.TYPE_BANK
        editor = AccountEditor(self.store, account)
        editor.bank_type.select_item_by_data(237)
        self.assertFalse(editor.parent_accounts.get_account_by_id(account.id))
        self.check_editor(editor, 'editor-account-show-bradesco')

    def test_show_caixa(self):
        account = self.create_account()
        account.account_type = Account.TYPE_BANK
        editor = AccountEditor(self.store, account)
        editor.bank_type.select_item_by_data(104)
        self.assertFalse(editor.parent_accounts.get_account_by_id(account.id))
        self.check_editor(editor, 'editor-account-show-caixa')

    def test_show_itau(self):
        account = self.create_account()
        account.account_type = Account.TYPE_BANK
        editor = AccountEditor(self.store, account)
        editor.bank_type.select_item_by_data(341)
        self.assertFalse(editor.parent_accounts.get_account_by_id(account.id))
        self.check_editor(editor, 'editor-account-show-itau')

    def test_show_real(self):
        account = self.create_account()
        account.account_type = Account.TYPE_BANK
        editor = AccountEditor(self.store, account)
        editor.bank_type.select_item_by_data(356)
        self.assertFalse(editor.parent_accounts.get_account_by_id(account.id))
        self.check_editor(editor, 'editor-account-show-real')

    def test_show_santander(self):
        account = self.create_account()
        account.account_type = Account.TYPE_BANK
        editor = AccountEditor(self.store, account)
        editor.bank_type.select_item_by_data(33)
        self.assertFalse(editor.parent_accounts.get_account_by_id(account.id))
        self.check_editor(editor, 'editor-account-show-santander')


if __name__ == '__main__':
    from stoqlib.api import api
    c = api.prepare_test()
    unittest.main()
