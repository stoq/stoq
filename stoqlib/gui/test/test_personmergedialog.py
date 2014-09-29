# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2014 Async Open Source <http://www.async.com.br>
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

import contextlib
import gtk
import mock

from stoqlib.gui.dialogs.personmergedialog import PersonMergeDialog
from stoqlib.gui.test.uitestutils import GUITest


class TestPersonMergeDialog(GUITest):
    def _create_data(self, name, phone=None, street=None):
        client = self.create_client(name=name)
        if phone:
            client.person.phone_number = phone
        if street:
            address = self.create_address(person=client.person)
            address.street = street

    def _create_sample_data(self):
        self._create_data(name=u'Juca Pinga', phone=u'33710001')
        self._create_data(name=u'Juca da Silva Pinga')
        self._create_data(name=u'Juca', phone=u'33710001')
        self._create_data(name=u'Juca Antônio')

        self._create_data(name=u'José Pinga', street=u'Rua Dos Bobos')
        self._create_data(name=u'Jose Cuervo Pinga', phone=u'33710002',
                          street=u'Av. Dos bobos')
        self._create_data(name=u'José Cuervo Pinga', phone=u'33710003')

    def test_create(self):
        dialog = PersonMergeDialog(self.store)
        self.check_editor(dialog, 'dialog-person-merge-dialog')

    @mock.patch('stoqlib.gui.dialogs.personmergedialog.ProgressDialog')
    def test_search(self, ProgressDialog):
        dialog = PersonMergeDialog(self.store)
        self.click(dialog.search_button)
        ProgressDialog.assert_called_once_with('Searching duplicates',
                                               pulse=False)

    @mock.patch('stoqlib.gui.dialogs.personmergedialog.ProgressDialog')
    def test_search_same_name(self, ProgressDialog):
        self._create_sample_data()
        dialog = PersonMergeDialog(self.store)

        # First, only the exact name
        dialog.model.same_phone = False
        dialog.model.same_street = False
        self.click(dialog.search_button)

        names = set(d.name for d in dialog.dup_tree)
        self.assertEquals(names, set([u'José Cuervo Pinga', u'Jose Cuervo Pinga']))

    @mock.patch('stoqlib.gui.dialogs.personmergedialog.ProgressDialog')
    def test_search_first_name_phone(self, ProgressDialog):
        self._create_sample_data()
        dialog = PersonMergeDialog(self.store)
        dialog.model.method = dialog.model.FIRST_NAME

        # First, only the first name and phone
        dialog.model.same_phone = True
        dialog.model.same_street = False
        self.click(dialog.search_button)

        names = set(d.name for d in dialog.dup_tree)
        self.assertEquals(names, set([u'Juca Pinga', 'Juca']))

    @mock.patch('stoqlib.gui.dialogs.personmergedialog.ProgressDialog')
    def test_search_first_last_name_address(self, ProgressDialog):
        self._create_sample_data()
        dialog = PersonMergeDialog(self.store)
        dialog.model.method = dialog.model.FIRST_LAST_NAME

        # First, only the first name and phone
        dialog.model.same_phone = False
        dialog.model.same_street = True
        self.click(dialog.search_button)

        names = set(d.name for d in dialog.dup_tree)
        self.assertEquals(names, set([u'José Pinga', 'Jose Cuervo Pinga']))

    @mock.patch('stoqlib.gui.dialogs.personmergedialog.ProgressDialog')
    @mock.patch('stoqlib.gui.dialogs.personmergedialog.yesno')
    def test_merge(self, yesno, ProgressDialog):
        self._create_sample_data()
        dialog = PersonMergeDialog(self.store)
        dialog.model.same_phone = False
        dialog.model.same_street = False
        self.click(dialog.search_button)

        for row in dialog.dup_tree:
            if not row.parent:
                root = row
            else:
                # Figure out how to mimic the user clicking the row
                row.merge = True

        self.assertEquals(len(root.get_to_merge()), 2)
        dialog.dup_tree.select(root)

        with contextlib.nested(
                mock.patch('stoq.gui.inventory.api.new_store'),
                mock.patch.object(self.store, 'commit'),
                mock.patch.object(self.store, 'close')) as ctx:
            new_store = ctx[0]
            new_store.return_value = self.store
            self.click(dialog.merge_button)

        yesno.assert_called_once_with(
            'This will merge 2 persons into 1. Are you sure?', gtk.RESPONSE_NO,
            'Merge', "Don't merge")

        # If we search again, there should be no duplicates
        self.click(dialog.search_button)
        self.assertEquals(len(dialog.dup_tree), 0)
