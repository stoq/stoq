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


import mock
import gtk
from kiwi.ui.widgets.entry import ProxyEntry

from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.widgets.searchentry import SearchEntryGadget
from stoqlib.gui.search.personsearch import ClientSearch
from stoqlib.gui.search.fiscalsearch import CfopSearch
from stoqlib.gui.editors.personeditor import ClientEditor
from stoqlib.gui.editors.fiscaleditor import CfopEditor


class TestSearchEntryGadget(GUITest):

    def _create_interface(self):
        self.sale = self.create_sale()

        self.window = gtk.Window()
        self.entry = ProxyEntry()
        self.window.add(self.entry)
        self.client_gadget = SearchEntryGadget(
            self.entry, self.store, model=self.sale, model_property='client',
            search_columns=['name'], search_class=ClientSearch,
            parent=self.window)

    def test_create(self):
        window = gtk.Window()
        box = gtk.VBox()
        window.add(box)
        entry = ProxyEntry()
        box.pack_start(entry)
        self.check_dialog(window, 'search-entry-before-replace')

        sale = self.create_sale()
        SearchEntryGadget(entry, self.store, model=sale,
                          model_property='client', search_columns=['name'],
                          search_class=ClientSearch, parent=window)
        self.check_dialog(window, 'search-entry-after-replace')

    @mock.patch('stoqlib.gui.widgets.searchentry.run_dialog')
    def test_run_search(self, run_dialog):
        self._create_interface()
        run_dialog.return_value = None
        self.click(self.client_gadget.find_button)
        run_dialog.assert_called_once_with(
            ClientSearch, self.window, self.store, initial_string='',
            double_click_confirm=True)

    @mock.patch('stoqlib.gui.widgets.searchentry.api.new_store')
    @mock.patch('stoqlib.gui.widgets.searchentry.run_person_role_dialog')
    def test_run_editor(self, run_dialog, new_store):
        new_store.return_value = self.store
        self._create_interface()
        client = self.create_client(name=u'Fulano de Tal')
        run_dialog.return_value = client
        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.click(self.client_gadget.edit_button)
                run_dialog.assert_called_once_with(
                    ClientEditor, self.window, self.store, None)

        self.assertEquals(self.entry.read(), client.id)
        self.assertEquals(self.entry.get_text(), u'Fulano de Tal')

    @mock.patch('stoqlib.gui.widgets.searchentry.api.new_store')
    @mock.patch('stoqlib.gui.widgets.searchentry.run_dialog')
    def test_entry_activate(self, run_dialog, new_store):
        new_store.return_value = self.store
        self._create_interface()

        fulano = self.create_client(u'Fulano de Tal')
        ciclano = self.create_client(u'Cicrano de Tal')

        # There should be only one match for Fulano, then the entry should be
        # updated with this only match
        self.entry.set_text('Fulano')
        self.entry.activate()

        self.assertEquals(self.entry.get_text(), 'Fulano de Tal')
        self.assertEquals(self.entry.read(), fulano.id)

        # Now when we use 'de tal', there are two clients that match. The
        # search should be displayed
        run_dialog.return_value = ciclano

        self.entry.set_text('de tal')
        self.entry.activate()

        run_dialog.assert_called_once_with(
            ClientSearch, self.window, self.store, initial_string='de tal',
            double_click_confirm=True)

        self.assertEquals(self.entry.get_text(), 'Cicrano de Tal')
        self.assertEquals(self.entry.read(), ciclano.id)

    @mock.patch('stoqlib.gui.widgets.searchentry.api.new_store')
    @mock.patch('stoqlib.gui.widgets.searchentry.run_dialog')
    def test_with_cfop(self, run_dialog, new_store):
        new_store.return_value = self.store
        window = gtk.Window()
        entry = ProxyEntry()
        window.add(entry)

        sale = self.create_sale()
        gadget = SearchEntryGadget(
            entry, self.store, model=sale, model_property='cfop',
            search_columns=['name'], search_class=CfopSearch, parent=window)

        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                run_dialog.return_value = None
                self.click(gadget.edit_button)
                run_dialog.assert_called_once_with(
                    CfopEditor, window, self.store, sale.cfop)
