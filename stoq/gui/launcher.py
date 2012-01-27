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
from stoqlib.api import api
from stoqlib.gui.base.dialogs import add_current_toplevel
from stoqlib.lib.interfaces import IApplicationDescriptions
from stoq.gui.application import AppWindow
from stoq.lib.applist import Application

_ = gettext.gettext
(COL_LABEL,
 COL_PIXBUF,
 COL_APP) = range(3)


class LauncherApp(object):
    def __init__(self, launcher, options):
        self.launcher = launcher
        self.shell = launcher.shell
        self.embedded = False
        self.main_window = launcher
        self.options = options
        self.name = 'launcher'


class Launcher(AppWindow):

    app_name = _('Stoq')
    gladefile = 'launcher'

    def __init__(self, options, shell):
        self.shell = shell
        app = LauncherApp(self, options)
        AppWindow.__init__(self, app)

    #
    # AppWindow
    #

    def get_title(self):
        return self.app_name

    def create_ui(self):
        toplevel = self.get_toplevel().get_toplevel()
        add_current_toplevel(toplevel)
        self.model.set_sort_column_id(COL_LABEL, gtk.SORT_ASCENDING)
        self.iconview.set_markup_column(COL_LABEL)
        self.iconview.set_pixbuf_column(COL_PIXBUF)
        if hasattr(self.iconview, "set_item_orientation"):
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
    # Public API
    #

    def show_app(self, app, app_window, params=None):
        self.iconview_vbox.hide()
        super(Launcher, self).show_app(app, app_window, params)

    def hide_app(self):
        super(Launcher, self).hide_app()
        self.iconview_vbox.show()
        self.iconview.grab_focus()

    def run_app_by_name(self, app_name, params=None):
        self.hide_app()
        app = self._get_app_by_name(app_name)
        if app is None:
            raise ValueError(app_name)
        return self.shell.run_embedded(app, self, params)

    #
    # Private
    #

    def _get_app_by_name(self, app_name):
        for row in self.model:
            if row[COL_APP].name == app_name:
                return row[COL_APP]

    def _run_app(self, app):
        self.shell.run_embedded(app, self)

    def _get_available_applications(self):
        user = api.get_current_user(self.conn)

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

    def on_iconview__item_activated(self, iconview, path):
        app = self.model[path][COL_APP]
        self._run_app(app)
