# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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

from stoq.gui.test.baseguitest import BaseGUITest
from plugins.ecf.paulistainvoicedialog import PaulistaInvoiceDialog


class TestPaulistaInvoiceDialog(BaseGUITest):
    def test_show(self):
        editor = PaulistaInvoiceDialog(self.store, model=None)
        self.check_editor(editor, 'editor-paulista-invoice-cpf-show')

        self.click(editor.cnpj)
        self.check_editor(editor, 'editor-paulista-invoice-cnpj-show')

    def test_on_document__validate_cpf(self):
        editor = PaulistaInvoiceDialog(self.store, model=None)
        editor.document.update(u"123.123.123-12")
        self.assertInvalid(editor, ['document'])

    def test_on_document__validate_cnpj(self):
        editor = PaulistaInvoiceDialog(self.store, model=None)
        self.click(editor.cnpj)
        editor.document.update(u"11.222.333/4444-55")
        self.assertInvalid(editor, ['document'])

    def test_confirm(self):
        editor = PaulistaInvoiceDialog(self.store, model=None)
        with mock.patch('plugins.ecf.paulistainvoicedialog.info') as info:
            self.click(editor.main_dialog.ok_button)
            info.assert_called_once_with('The CPF cannot be empty')
