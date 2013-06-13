# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
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

import logging

import gtk

from stoqlib.database.runtime import get_default_store
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.producteditor import ProductEditor
from stoqlib.gui.events import (StartApplicationEvent, StopApplicationEvent,
                                EditorSlaveCreateEvent)
from stoqlib.gui.utils.keybindings import add_bindings, get_accels
from stoqlib.lib.translation import stoqlib_gettext

from books.bookssearch import ProductBookSearch
from books.booksslave import ProductBookSlave
from books.publishersearch import PublisherSearch

_ = stoqlib_gettext
log = logging.getLogger(__name__)


class BooksUI(object):
    def __init__(self):
        self._ui = None
        self.default_store = get_default_store()
        StartApplicationEvent.connect(self._on_StartApplicationEvent)
        StopApplicationEvent.connect(self._on_StopApplicationEvent)
        EditorSlaveCreateEvent.connect(self._on_EditorSlaveCreateEvent)
        add_bindings([
            ('plugin.books.search_books', '<Primary><Alt>B'),
            ('plugin.books.search_publishers', '<Primary><Alt>P'),
        ])

    #
    # Private
    #

    def _get_menu_ui_string(self):
        return """<ui>
            <menubar name="menubar">
                <placeholder name="ExtraMenubarPH">
                    <menu action="BooksMenu">
                    %s
                    </menu>
                </placeholder>
            </menubar>
        </ui>"""

    def _add_purchase_menus(self, uimanager):
        menu_items_str = '''<menuitem action="BookSearch"/>
                            <menuitem action="Publishers"/>'''
        ui_string = self._get_menu_ui_string() % menu_items_str

        group = get_accels('plugin.books')
        ag = gtk.ActionGroup('BooksMenuActions')
        ag.add_actions([
            ('BooksMenu', None, _(u'Books')),
            ('BookSearch', None, _(u'Book Search'),
             group.get('search_books'), None,
             self._on_BookSearch__activate),
            ('Publishers', None, _(u'Publishers ...'),
             group.get('search_publishers'), None,
             self._on_Publishers__activate),
        ])

        uimanager.insert_action_group(ag, 0)
        self._ui = uimanager.add_ui_from_string(ui_string)

    def _add_sale_menus(self, uimanager):
        menu_items_str = '<menuitem action="BookSearch"/>'
        ui_string = self._get_menu_ui_string() % menu_items_str

        group = get_accels('plugin.books')
        ag = gtk.ActionGroup('BooksMenuActions')
        ag.add_actions([
            ('BooksMenu', None, _(u'Books')),
            ('BookSearch', None, _(u'Book Search'),
             group.get('search_books'), None,
             self._on_BookSearchView__activate),
        ])

        uimanager.insert_action_group(ag, 0)
        self._ui = uimanager.add_ui_from_string(ui_string)

    def _add_pos_menus(self, uimanager):
        menu_items_str = '<menuitem action="BookSearch"/>'
        ui_string = self._get_menu_ui_string() % menu_items_str

        group = get_accels('plugin.books')
        ag = gtk.ActionGroup('BooksMenuActions')
        ag.add_actions([
            ('BooksMenu', None, _(u'Books')),
            ('BookSearch', None, _(u'Book Search'),
             group.get('search_books'), None,
             self._on_BookSearchView__activate),
        ])

        uimanager.insert_action_group(ag, 0)
        self._ui = uimanager.add_ui_from_string(ui_string)

    def _remove_app_ui(self, uimanager):
        if not self._ui:
            return
        uimanager.remove_ui(self._ui)
        self._ui = None

    def _add_product_slave(self, editor, model, store):
        editor.add_extra_tab(ProductBookSlave.title,
                             ProductBookSlave(store, model))

    #
    # Events
    #

    def _on_StartApplicationEvent(self, appname, app):
        if appname == 'purchase':
            self._add_purchase_menus(app.window.uimanager)
        elif appname == 'sales':
            self._add_sale_menus(app.window.uimanager)
        elif appname == 'pos':
            self._add_pos_menus(app.window.uimanager)

    def _on_StopApplicationEvent(self, appname, app):
        self._remove_app_ui(app.window.uimanager)

    def _on_EditorSlaveCreateEvent(self, editor, model, store, *args):
        # Use type() instead of isinstance so tab does
        # not appear on production product editor
        if not type(editor) is ProductEditor:
            return

        self._add_product_slave(editor, model, store)

    #
    # Callbacks
    #

    def _on_BookSearch__activate(self, action):
        run_dialog(ProductBookSearch, None, self.default_store, hide_price_column=True)

    def _on_BookSearchView__activate(self, action):
        run_dialog(ProductBookSearch, None, self.default_store, hide_cost_column=True,
                   hide_toolbar=True)

    def _on_Publishers__activate(self, action):
        run_dialog(PublisherSearch, None, self.default_store, hide_footer=True)
