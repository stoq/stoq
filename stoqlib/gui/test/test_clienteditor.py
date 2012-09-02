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
from nose.exc import SkipTest

from stoqlib.domain.person import Person
from stoqlib.gui.uitestutils import GUITest, GUIDumper
from stoqlib.gui.editors.personeditor import ClientEditor


class TestClientEditor(GUITest):
    def testCreateIndividual(self):
        editor = ClientEditor(self.trans, role_type=Person.ROLE_INDIVIDUAL)
        self.check_editor(editor, 'editor-client-individual-create')

    def testCreateCompany(self):
        editor = ClientEditor(self.trans, role_type=Person.ROLE_COMPANY)
        self.check_editor(editor, 'editor-client-company-create')

    @mock.patch('stoqlib.gui.templates.persontemplate.warning')
    def testEditWithoutAddress(self, warning):
        client = self.create_client()
        editor = ClientEditor(self.trans, client,
                              role_type=Person.ROLE_INDIVIDUAL)
        self.click(editor.get_person_slave().address_button)

        warning.assert_called_once_with(
            'You must define a valid main address before\n'
            'adding additional addresses')

    @mock.patch('stoqlib.gui.templates.persontemplate.warning')
    def testEditAddress(self, warning):
        raise SkipTest("http://bugs.async.com.br/show_bug.cgi?id=5203")
        client = Person.selectBy(name="Franciso Elisio de Lima Junior",
                                 connection=self.trans)[0].client
        editor = ClientEditor(self.trans, client,
                              role_type=Person.ROLE_INDIVIDUAL)

        dump = GUIDumper()
        dump.dump_editor(editor)

        def run_dialog2(dialog, parent, *args, **kwargs):
            d = dialog(*args, **kwargs)
            dump.dump_dialog(d)
            return d.model

        def run_dialog(dialog, parent, *args, **kwargs):
            d = dialog(*args, **kwargs)
            dump.dump_dialog(d)
            with mock.patch('stoqlib.gui.base.lists.run_dialog',
                            new=run_dialog2):
                self.click(d.list_slave.listcontainer.add_button)
            return d.retval

        with mock.patch('stoqlib.gui.templates.persontemplate.run_dialog',
                        new=run_dialog):
            self.click(editor.get_person_slave().address_button)

        self.check_filename(dump, 'editor-client-edit-address')
