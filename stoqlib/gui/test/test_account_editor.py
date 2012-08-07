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
from stoqlib.gui.uitestutils import GUITest


class TestAccountEditor(GUITest):
    def testCreate(self):
        editor = AccountEditor(self.trans)
        self.check_editor(editor, 'editor-account-create')

    def testConfirm(self):
        editor = AccountEditor(self.trans)
        self.assertFalse(editor.validate_confirm())
        editor.description.update('Account name')
        self.assertTrue(editor.validate_confirm())
        editor.main_dialog.confirm()
        self.check_editor(editor, 'editor-account-confirm',
                          [editor.retval])

    def testShow(self):
        account = self.create_account()
        editor = AccountEditor(self.trans, account)
        self.check_editor(editor, 'editor-account-show')

    def testShowBancoDoBrasil(self):
        account = self.create_account()
        account.account_type = Account.TYPE_BANK
        editor = AccountEditor(self.trans, account)
        editor.bank_type.select_item_by_data(1)
        self.check_editor(editor, 'editor-account-show-banco-do-brasil')

    def testShowBanrisul(self):
        account = self.create_account()
        account.account_type = Account.TYPE_BANK
        editor = AccountEditor(self.trans, account)
        editor.bank_type.select_item_by_data(41)
        self.check_editor(editor, 'editor-account-show-banrisul')

    def testShowBradesco(self):
        account = self.create_account()
        account.account_type = Account.TYPE_BANK
        editor = AccountEditor(self.trans, account)
        editor.bank_type.select_item_by_data(237)
        self.check_editor(editor, 'editor-account-show-bradesco')

    def testShowCaixa(self):
        account = self.create_account()
        account.account_type = Account.TYPE_BANK
        editor = AccountEditor(self.trans, account)
        editor.bank_type.select_item_by_data(104)
        self.check_editor(editor, 'editor-account-show-caixa')

    def testShowItau(self):
        account = self.create_account()
        account.account_type = Account.TYPE_BANK
        editor = AccountEditor(self.trans, account)
        editor.bank_type.select_item_by_data(341)
        self.check_editor(editor, 'editor-account-show-itau')

    def testShowReal(self):
        account = self.create_account()
        account.account_type = Account.TYPE_BANK
        editor = AccountEditor(self.trans, account)
        editor.bank_type.select_item_by_data(356)
        self.check_editor(editor, 'editor-account-show-real')

    def testShowSantander(self):
        account = self.create_account()
        account.account_type = Account.TYPE_BANK
        editor = AccountEditor(self.trans, account)
        editor.bank_type.select_item_by_data(33)
        self.check_editor(editor, 'editor-account-show-santander')


if __name__ == '__main__':
    from stoqlib.api import api
    c = api.prepare_test()
    unittest.main()
