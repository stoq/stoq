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

import mock

from stoqlib.domain.person import Client
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.fields import PersonField
from stoqlib.gui.editors.personeditor import ClientEditor


class TestPersonField(GUITest):

    def test_run_dialog(self):
        client = self.create_client()

        field = PersonField(person_type=Client)
        field.form = None

        with mock.patch('stoqlib.gui.wizards.personwizard.run_dialog') as run_dialog:
            field.run_dialog(self.store, client)
            run_dialog.assert_called_once_with(ClientEditor, None, self.store, client,
                                               visual_mode=False)
