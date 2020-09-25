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
from gi.repository import Gtk
from kiwi.ui.widgets.entry import ProxyEntry

from stoqlib.domain.person import ClientView
from stoq.lib.gui.test.uitestutils import GUITest
from stoq.lib.gui.widgets.searchentry import SearchEntryGadget
from stoq.lib.gui.search.personsearch import ClientSearch
from stoq.lib.gui.search.fiscalsearch import CfopSearch
from stoq.lib.gui.editors.personeditor import ClientEditor
from stoq.lib.gui.editors.fiscaleditor import CfopEditor


class TestSearchEntryGadget(GUITest):

    def _create_interface(self, run_editor=None):
        self.sale = self.create_sale()

        self.window = Gtk.Window()
        self.entry = ProxyEntry()
        self.window.add(self.entry)
        self.client_gadget = SearchEntryGadget(
            self.entry, self.store, model=self.sale, model_property='client',
            search_columns=['name'], search_class=ClientSearch,
            parent=self.window, run_editor=run_editor)
        self.client_gadget.get_model_obj = lambda obj: obj and obj.client

    def test_create(self):
        window = Gtk.Window()
        box = Gtk.VBox()
        window.add(box)
        entry = ProxyEntry()
        box.pack_start(entry, True, True, 0)
        self.check_dialog(window, 'search-entry-before-replace')

        sale = self.create_sale()
        SearchEntryGadget(entry, self.store, model=sale,
                          model_property='client', search_columns=['name'],
                          search_class=ClientSearch, parent=window)
        self.check_dialog(window, 'search-entry-after-replace')

    @mock.patch('stoq.lib.gui.widgets.searchentry.run_dialog')
    def test_run_search(self, run_dialog):
        self._create_interface()
        run_dialog.return_value = None
        self.click(self.client_gadget.find_button)
        run_dialog.assert_called_once_with(
            ClientSearch, self.window, self.store, initial_string='',
            double_click_confirm=True)

    @mock.patch('stoq.lib.gui.widgets.searchentry.api.new_store')
    @mock.patch('stoq.lib.gui.widgets.searchentry.run_person_role_dialog')
    def test_run_editor(self, run_dialog, new_store):
        new_store.return_value = self.store
        self._create_interface()
        client = self.create_client(name=u'Fulano de Tal')
        run_dialog.return_value = self.store.find(
            ClientView, ClientView.id == client.id).one()
        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.click(self.client_gadget.edit_button)
                run_dialog.assert_called_once_with(
                    ClientEditor, self.window, self.store, None)

        self.assertEqual(self.entry.read(), client)
        self.assertEqual(self.entry.get_text(), u'Fulano de Tal')

    @mock.patch('stoq.lib.gui.widgets.searchentry.api.new_store')
    def test_run_editor_override(self, new_store):
        new_store.return_value = self.store
        run_editor = mock.MagicMock()
        run_editor.return_value = None
        self.assertEqual(run_editor.call_count, 0)
        self._create_interface(run_editor=run_editor)
        with mock.patch.object(self.store, 'commit'):
            with mock.patch.object(self.store, 'close'):
                self.click(self.client_gadget.edit_button)

        self.assertEqual(run_editor.call_count, 1)

    @mock.patch('stoq.lib.gui.widgets.searchentry.api.new_store')
    @mock.patch('stoq.lib.gui.widgets.searchentry.run_dialog')
    def test_entry_activate(self, run_dialog, new_store):
        new_store.return_value = self.store
        self._create_interface()

        fulano = self.create_client(u'Fulano de Tal')
        ciclano = self.create_client(u'Cicrano de Tal')

        # There should be only one match for Fulano, then the entry should be
        # updated with this only match
        self.entry.set_text('Fulano')
        self.entry.activate()

        self.assertEqual(self.entry.get_text(), 'Fulano de Tal')
        self.assertEqual(self.entry.read(), fulano)

        # Now when we use 'de tal', there are two clients that match. The
        # search should be displayed
        run_dialog.return_value = self.store.find(
            ClientView, ClientView.id == ciclano.id).one()

        self.entry.set_text('de tal')
        self.entry.activate()

        run_dialog.assert_called_once_with(
            ClientSearch, self.window, self.store, initial_string='de tal',
            double_click_confirm=True)

        self.assertEqual(self.entry.get_text(), 'Cicrano de Tal')
        self.assertEqual(self.entry.read(), ciclano)

    @mock.patch('stoq.lib.gui.widgets.searchentry.api.new_store')
    @mock.patch('stoq.lib.gui.widgets.searchentry.run_dialog')
    def test_with_cfop(self, run_dialog, new_store):
        new_store.return_value = self.store
        window = Gtk.Window()
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
