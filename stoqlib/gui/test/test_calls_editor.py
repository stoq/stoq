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

from stoqlib.domain.person import Calls
from stoqlib.lib.dateutils import localtoday
from stoqlib.gui.editors.callseditor import CallsEditor
from stoqlib.gui.test.uitestutils import GUITest


class TestCallsEditor(GUITest):
    def test_create(self):
        person = self.create_person()
        editor = CallsEditor(self.store, None, person, None)
        self.assertTrue(isinstance(editor.model, Calls))
        editor.date.update(localtoday().date())

        self.check_editor(editor, 'editor-calls-create')

    def test_show(self):
        person = self.create_person()
        calls = self.create_call()
        calls.person = person
        editor = CallsEditor(self.store, calls, person, None)

        self.check_editor(editor, 'editor-calls-show')


if __name__ == '__main__':
    from stoqlib.api import api
    c = api.prepare_test()
    unittest.main()
