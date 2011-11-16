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

class LauncherApp(object):
    def __init__(self, launcher):
        self.launcher = launcher
        self.runner = launcher.runner
        self.embedded = False
        self.main_window = launcher
        self.options = launcher.options


class Launcher(AppWindow):

    app_name = _('v1.0 [localhost]')
    gladefile = 'launcher'
    launchers = []

    def __init__(self, options, runner):
        import stoq.gui.purchase
        import stoq.gui.payable
        import stoq.gui.receivable
        import stoq.gui.financial
        import stoq.gui.admin
        self.runner = runner
        self.options = options
        self.current_app = None
        app = LauncherApp(self)
        AppWindow.__init__(self, app)
        self.get_toplevel().connect('destroy', self._shutdown)
        hide_splash()
        Launcher.launchers.append(self)

    #
    # AppWindow overrides
    #

    def activate(self):
        self.hide_app()

    #
    # Private
    #

    def create_actions(self):
        ui_string = """<ui>
          <menubar action="menubar">
            <menu action="StoqMenu">
              <menu action="NewMenu">
                <placeholder name="NewMenuItemPH"/>
              </menu>
              <menuitem action="NewWindow"/>
              <separator/>
              <placeholder name="StoqMenuPH"/>
              <separator/>
              <menuitem action="ChangePassword"/>
              <menuitem action="SignOut"/>
              <separator/>
              <menuitem action="Close"/>
              <menuitem action="Quit"/>
            </menu>
            <menu action="EditMenu">
              <menuitem action="Cut"/>
              <menuitem action="Copy"/>
              <menuitem action="Paste"/>
              <separator/>
              <placeholder name="EditMenuPH"/>
              <separator/>
              <menuitem action="Preferences"/>
            </menu>
            <menu action="ViewMenu">
              <menuitem action="ToggleToolbar"/>
              <menuitem action="ToggleStatusbar"/>
              <separator/>
              <menuitem action="ToggleFullscreen"/>
            </menu>
            <placeholder name="AppMenubarPH"/>
            <placeholder name="ExtraMenubarPH"/>
          </menubar>
          <toolbar action="toolbar">
            <placeholder name="NewToolItemPH">
              <toolitem action="NewToolItem">
                <menu action="NewMenu">
                </menu>
              </toolitem>
            </placeholder>
            <placeholder name="AppToolbarPH"/>
          </toolbar>
        </ui>"""

        actions = [
            ('menubar', None, ''),

            ('StoqMenu', None, _("_File")),
            ('StoqMenuNew', None, _("_New")),
            ('NewWindow', None, _("New _window")),
            ('Close', None, _('Close'), '<control>w'),
            ('ChangePassword', None, _('Change password...'), None),
            ('SignOut', None, _('Sign out...')),
            ("Quit", gtk.STOCK_QUIT, _('Quit'), '<control>q',
             _('Exit the application')),

            ('EditMenu', None, _("_Edit")),
            ('Cut', None, _("Cu_t")),
            ('Copy', None, _("Copy")),
            ('Paste', None, _("_Paste")),
            ('Preferences', None, _("_Preferences")),

            ('ViewMenu', None, _("_View")),

            ('toolbar', None, ''),
            ("NewMenu", None, _("New")),
            ]
        self.add_ui_actions(ui_string, actions)
        self.Cut.set_sensitive(False)
        self.Copy.set_sensitive(False)
        self.Paste.set_sensitive(False)
        toogle_actions = [
            ('ToggleToolbar', None, _("_Toolbar"), '',
             _('Show or hide the toolbar')),
            ('ToggleStatusbar', None, _("_Statusbar"), '',
             _('Show or hide the statusbar')),
            ('ToggleFullscreen', None, _("_Fullscreen"), 'F11',
             _('Enter or leave fullscreen mode')),
            ]
        self.add_ui_actions('', toogle_actions, 'ToogleActions',
                            'toogle')
        self.ToggleToolbar.props.active = True
        self.ToggleStatusbar.props.active = True

        self.add_tool_menu_actions([
            ("NewToolItem", _("New"), '', gtk.STOCK_ADD),
            ])
        self.NewToolItem.props.is_important = True

        self.add_help_ui()

    def create_ui(self):
        self.uimanager.connect('connect-proxy',
            self._on_uimanager__connect_proxy)
        self.uimanager.connect('disconnect-proxy',
            self._on_uimanager__disconnect_proxy)
        menubar = self.uimanager.get_widget('/menubar')
        self.main_vbox.pack_start(menubar, False, False)
        self.main_vbox.reorder_child(menubar, 0)

        toolbar = self.uimanager.get_widget('/toolbar')
        self.main_vbox.pack_start(toolbar, False, False)
        self.main_vbox.reorder_child(toolbar, 1)

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

    def show_app(self, app, app_window):
        app_window.reparent(self.application_box)
        self.application_box.set_child_packing(app_window, True, True, 0,
                                               gtk.PACK_START)
        app_window.show_all()
        self.iconview_vbox.hide()
        self.application_box.show()
        self.current_app = app
        self.current_widget = app_window
        self.Close.set_sensitive(True)
        self.ChangePassword.set_visible(False)
        self.SignOut.set_visible(False)

    def hide_app(self):
        self.application_box.hide()
        if self.current_app:
            self.current_app.deactivate()
            self.current_widget.destroy()
        self.Close.set_sensitive(False)
        self.ChangePassword.set_visible(True)
        self.SignOut.set_visible(True)
        self.iconview.grab_focus()
        self.iconview_vbox.show()

    #
    # Private
    #

    def _shutdown(self, *args):
        Launcher.launchers.remove(self)
        if not Launcher.launchers:
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

    def _on_menu_item__select(self, menuitem, tooltip):
        self.statusbar.push(-1, tooltip)

    def _on_menu_item__deselect(self, menuitem):
        self.statusbar.pop(-1)

    def _on_uimanager__connect_proxy(self, uimgr, action, widget):
        tooltip = action.get_property('tooltip')
        if isinstance(widget, gtk.MenuItem) and tooltip:
            cid = widget.connect(
             'select', self._on_menu_item__select, tooltip)
            cid2 = widget.connect(
             'deselect', self._on_menu_item__deselect)
            widget.set_data('app::connect-ids', (cid, cid2))

    def _on_uimanager__disconnect_proxy(self, uimgr, action, widget):
        cids = widget.get_data('app::connect-ids') or ()
        for cid in cids:
            widget.disconnect(cid)

    def on_NewToolItem__activate(self, action):
        if self.current_app:
            self.current_app.new_activate()
        else:
            print 'FIXME'

    def on_NewWindow__activate(self, action):
        launcher = Launcher(self.options, self.runner)
        launcher.show()

    def on_Preferences__activate(self, action):
        pass

    def on_ToggleToolbar__toggled(self, action):
        toolbar = self.uimanager.get_widget('/toolbar')
        toolbar.set_visible(action.get_active())

    def on_ToggleStatusbar__toggled(self, action):
        self.statusbar.set_visible(action.get_active())

    def on_ToggleFullscreen__toggled(self, action):
        self.toggle_fullscreen()

    def on_Close__activate(self, action):
        self.hide_app()

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
        self.runner.run(app, self)
