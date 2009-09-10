# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
## Author(s):   George Y. Kussumoto      <george@async.com.br>
##

import sys

import gtk

from kiwi.log import Logger
from stoqlib.database.runtime import get_connection
from stoqlib.domain.events import SaleConfirmEvent
from stoqlib.gui.events import StartApplicationEvent
from stoqlib.lib.translation import stoqlib_gettext

from nfegenerator import NFeGenerator

_ = stoqlib_gettext
log = Logger("stoq-nfe-plugin")


class NFeUI(object):
    def __init__(self):
        self.conn = get_connection()

        SaleConfirmEvent.connect(self._on_SaleConfirm)
        StartApplicationEvent.connect(self._on_StartApplicationEvent)

    #
    # Private
    #

    def _add_ui_menus(self, appname, uimanager):
        if appname == 'sales':
            self._add_sales_menus(uimanager)
        elif appname == 'admin':
            self._add_admin_menus(uimanager)

    def _add_admin_menus(self, uimanager):
        ui_string = """<ui>
          <menubar name="menubar">
            <menu action="settings_menu" name="settings_menu">
            <placeholder name="PluginSettings">
              <menuitem action="ConfigureNFe"/>
            </placeholder>
            </menu>
          </menubar>
        </ui>"""

        ag = gtk.ActionGroup('NFeMenuActions')
        ag.add_actions([
            ('NFeMenu', None, _('NFe')),
            ('ConfigureNFe', None, _('Configure NF-e plugin...'),
             None, None, self._on_ConfigureNFe__activate),
            ])
        uimanager.insert_action_group(ag, 0)
        uimanager.add_ui_from_string(ui_string)

    def _add_sales_menus(self, uimanager):
        #TODO: implementation
        pass

    def _can_create_nfe(self, sale):
        # Improve!
        return sale.client is not None

    def _create_nfe(self, sale, trans):
        if self._can_create_nfe(sale):
            generator = NFeGenerator(sale, trans)
            generator.generate()
            generator.save()

    #
    # Events
    #

    def _on_StartApplicationEvent(self, appname, app):
        self._add_ui_menus(appname, app.main_window.uimanager)

    def _on_SaleConfirm(self, sale, trans):
        self._create_nfe(sale, trans)

    #
    # Callbacks
    #

    def _on_ConfigureNFe__activate(self, action):
        #TODO: implementation
        pass
