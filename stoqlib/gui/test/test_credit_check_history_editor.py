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

from stoqlib.domain.person import CreditCheckHistory
from stoqlib.gui.editors.creditcheckhistoryeditor import CreditCheckHistoryEditor
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localtoday


class TestCreditCheckHistoryEditor(GUITest):
    def test_create(self):
        client = self.create_client()
        editor = CreditCheckHistoryEditor(self.store, None, client)
        self.assertTrue(isinstance(editor.model, CreditCheckHistory))
        editor.check_date.update(localtoday().date())
        editor.identifier.update('identifier123')

        self.check_editor(editor, 'editor-creditcheckhistory-create')

    def test_show(self):
        client = self.create_client()
        clienthistory = self.create_credit_check_history(client=client)
        editor = CreditCheckHistoryEditor(self.store, clienthistory, client)

        self.check_editor(editor, 'editor-creditcheckhistory-show')


if __name__ == '__main__':
    from stoqlib.api import api
    c = api.prepare_test()
    unittest.main()
