# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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

import gettext
import operator

import gtk
from kiwi.component import get_utility
from stoqlib.database.runtime import (new_transaction, finish_transaction,
                                      get_current_user)
from stoqlib.gui.splash import hide_splash
from stoqlib.lib.interfaces import IApplicationDescriptions

from stoq.gui.application import AppWindow
from stoq.lib.applist import Application

_ = gettext.gettext
(COL_LABEL,
 COL_PIXBUF,
 COL_APP) = range(3)

class Launcher(AppWindow):

    app_name = _('v1.0 [localhost]')
    gladefile = 'launcher'

    def __init__(self, app, runner):
        self.runner = runner
        AppWindow.__init__(self, app)
        self.get_toplevel().connect('destroy', self._shutdown)
        hide_splash()

    #
    # AppWindow overrides
    #

    def activate(self):
        pass

    #
    # Private
    #

    def create_actions(self):
        ui_string = """<ui>
          <menubar action="menubar">
            <menu action="StoqMenu">
              <menuitem action="ChangePassword"/>
              <menuitem action="SignOut"/>
              <separator name="sep"/>
              <menuitem action="Quit"/>
            </menu>
          </menubar>
        </ui>"""

        actions = [
            ('menubar', None, ''),

            ('StoqMenu', None, _("_Stoq")),
            ('ChangePassword', None, _('Change password...'), None),
            ('SignOut', None, _('Sign out...')),
            ("Quit", gtk.STOCK_QUIT),

            ]
        self.add_ui_actions(ui_string, actions)
        self.add_help_ui()

    def create_ui(self):
        menubar = self.uimanager.get_widget('/menubar')
        self.main_vbox.pack_start(menubar, False, False)
        self.main_vbox.reorder_child(menubar, 0)

        self.model.set_sort_column_id(COL_LABEL, gtk.SORT_ASCENDING)
        self.iconview.set_markup_column(COL_LABEL)
        self.iconview.set_pixbuf_column(COL_PIXBUF)
        self.iconview.set_item_orientation(gtk.ORIENTATION_HORIZONTAL)
        self.iconview.set_item_width(300)
        self.iconview.set_selection_mode(gtk.SELECTION_BROWSE)
        self.iconview.set_spacing(10)

        for app in self._get_available_applications():
            pixbuf = self.get_toplevel().render_icon(app.icon, gtk.ICON_SIZE_DIALOG)
            text = '<b>%s</b>\n<small>%s</small>' % (app.fullname, app.description)
            self.model.append([text, pixbuf, app])

        # FIXME: last opened application
        self.iconview.select_path(self.model[0].path)
        self.iconview.grab_focus()

    #
    # Private
    #

    def _shutdown(self, *args):
        self.shutdown_application()
        raise SystemExit

    def _get_available_applications(self):
        user = get_current_user(self.conn)

        permissions = {}
        for settings in user.profile.profile_settings:
            permissions[settings.app_dir_name] = settings.has_permission

        descriptions = get_utility(IApplicationDescriptions).get_descriptions()

        available_applications = []

        # sorting by app_full_name
        for name, full, icon, descr in sorted(descriptions,
                                              key=operator.itemgetter(1)):
            #FIXME:
            #if name in self._hidden_apps:
            #    continue
            # and name not in self._blocked_apps:
            if permissions.get(name):
                available_applications.append(
                    Application(name, full, icon, descr))

        return available_applications

    #
    # Kiwi callbacks
    #

    def on_ChangePassword__activate(self, action):
        from stoqlib.gui.slaves.userslave import PasswordEditor
        trans = new_transaction()
        user = get_current_user(trans)
        retval = self.run_dialog(PasswordEditor, trans, user)
        finish_transaction(trans, retval)

    def on_SignOut__activate(self, action):
        from stoqlib.lib.interfaces import ICookieFile
        get_utility(ICookieFile).clear()
        self.get_toplevel().hide()
        self.app.runner.relogin()

    def on_Quit__activate(self, action):
        self._shutdown()

    def on_iconview__item_activated(self, iconview, path):
        app = self.model[path][COL_APP]
        self.runner.run(app)
