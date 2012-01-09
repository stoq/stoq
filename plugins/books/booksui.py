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

import gtk

from kiwi.log import Logger

from stoqlib.database.runtime import get_connection
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.events import StartApplicationEvent
from stoqlib.gui.keybindings import add_bindings, get_accels
from stoqlib.lib.translation import stoqlib_gettext

from bookssearch import ProductBookSearch
from booksslave import ProductBookSlave
from publishersearch import PublisherSearch

_ = stoqlib_gettext
log = Logger("stoq-books-plugin")


class BooksUI(object):
    def __init__(self):
        self.conn = get_connection()
        StartApplicationEvent.connect(self._on_StartApplicationEvent)
        add_bindings([
            ('plugin.books.search_books', '<Control><Alt>B'),
            ('plugin.books.search_publishers', '<Control><Alt>P'),
            ])

    #
    # Private
    #

    def _get_menu_ui_string(self):
        return """<ui>
            <menubar name="menubar">
                <placeholder name="ExtraMenu">
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
        uimanager.add_ui_from_string(ui_string)

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
        uimanager.add_ui_from_string(ui_string)

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
        uimanager.add_ui_from_string(ui_string)

    #
    # Accessors
    #

    def get_book_slave(self):
        """Returns the slave class for product book details UI."""
        return ProductBookSlave

    #
    # Events
    #

    def _on_StartApplicationEvent(self, appname, app):
        if appname == 'purchase':
            self._add_purchase_menus(app.main_window.uimanager)
        elif appname == 'sales':
            self._add_sale_menus(app.main_window.uimanager)
        elif appname == 'pos':
            self._add_pos_menus(app.main_window.uimanager)

    #
    # Callbacks
    #

    def _on_BookSearch__activate(self, action):
        run_dialog(ProductBookSearch, None, self.conn, hide_price_column=True)

    def _on_BookSearchView__activate(self, action):
        run_dialog(ProductBookSearch, None, self.conn, hide_cost_column=True,
                   hide_toolbar=True)

    def _on_Publishers__activate(self, action):
        run_dialog(PublisherSearch, None, self.conn, hide_footer=True)
