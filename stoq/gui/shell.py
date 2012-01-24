# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2011 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

import gettext
import operator

import gtk
from kiwi.component import get_utility
from kiwi.log import Logger
from stoqlib.api import api
from stoqlib.exceptions import LoginError
from stoqlib.gui.events import StartApplicationEvent
from stoqlib.gui.login import LoginHelper
from stoqlib.gui.splash import hide_splash
from stoqlib.lib.interfaces import IApplicationDescriptions
from stoqlib.lib.message import error, info
from stoqlib.lib.pluginmanager import get_plugin_manager
from twisted.internet import reactor

from stoq.gui.launcher import Launcher

_ = gettext.gettext
_shell = None
log = Logger('stoq.shell')
PRIVACY_STRING = _(
    "One of the new features of Stoq 1.0 is support for online "
    "services. Features using the online services include automatic "
    "bug report and update notifications. More services are under development."
    "To be able to provide a better service and properly identify the user "
    "we will collect the CNPJ of the primary branch and the ip address.\n\n"
    "<b>We will not disclose the collected information and we are committed "
    "to keeping your privacy intact.</b>")


class Shell(object):
    def __init__(self, options, appname=None):
        global _shell
        _shell = self
        self._current_app = None
        self._appname = None
        self._application_cache = {}
        self._user = None
        self._blocked_apps = []
        self._hidden_apps = []
        self._options = options
        self._login = LoginHelper(username=options.login_username)
        self.ran_wizard = False

        try:
            if not self.login():
                return
        except LoginError, e:
            error(e)
        self._check_param_main_branch()
        self._check_param_online_services()
        self._maybe_show_welcome_dialog()
        if appname:
            appdesc = self.get_app_by_name(appname)
            self.run(appdesc)
        else:
            self.run()

    def _check_param_main_branch(self):
        from stoqlib.database.runtime import (get_connection, new_transaction,
                                              get_current_station)
        from stoqlib.domain.person import Person
        from stoqlib.domain.interfaces import IBranch, ICompany
        from stoqlib.lib.parameters import sysparam
        conn = get_connection()
        compaines = Person.iselect(ICompany, connection=conn)
        if (compaines.count() == 0 or
            not sysparam(conn).MAIN_COMPANY):
            from stoqlib.gui.base.dialogs import run_dialog
            from stoqlib.gui.dialogs.branchdialog import BranchDialog
            if self.ran_wizard:
                info(_("You need to register a company before start using Stoq"))
            else:
                info(_("Could not find a company. You'll need to register one "
                       "before start using Stoq"))
            trans = new_transaction()
            person = run_dialog(BranchDialog, None, trans)
            if not person:
                raise SystemExit
            branch = IBranch(person)
            sysparam(trans).MAIN_COMPANY = branch.id
            get_current_station(trans).branch = branch
            trans.commit()

    def _check_param_online_services(self):
        from stoqlib.database.runtime import new_transaction
        from stoqlib.lib.parameters import sysparam

        trans = new_transaction()
        sparam = sysparam(trans)
        val = sparam.ONLINE_SERVICES
        if val is None:
            from kiwi.ui.dialogs import HIGAlertDialog
            # FIXME: All of this is to avoid having to set markup as the default
            #        in kiwi/ui/dialogs:HIGAlertDialog.set_details, after 1.0
            #        this can be simplified when we fix so that all descriptions
            #        sent to these dialogs are properly escaped
            dialog = HIGAlertDialog(
                parent=None,
                flags=gtk.DIALOG_MODAL,
                type=gtk.MESSAGE_WARNING)
            dialog.add_button(_("Not right now"), gtk.RESPONSE_NO)
            dialog.add_button(_("Enable online services"), gtk.RESPONSE_YES)

            dialog.set_primary(_('Do you want to enable Stoq online services?'))
            dialog.set_details(PRIVACY_STRING, use_markup=True)
            dialog.set_default_response(gtk.RESPONSE_YES)
            response = dialog.run()
            dialog.destroy()
            sparam.ONLINE_SERVICES = int(bool(response == gtk.RESPONSE_YES))
        trans.commit()

    def _maybe_show_welcome_dialog(self):
        if not api.user_settings.get('show-welcome-dialog', True):
            return
        api.user_settings.set('show-welcome-dialog', False)

        from stoq.gui.welcomedialog import WelcomeDialog
        from stoqlib.gui.base.dialogs import run_dialog
        run_dialog(WelcomeDialog)

    def _load_app(self, appdesc, app_window):
        module = __import__("stoq.gui.%s" % (appdesc.name, ),
                            globals(), locals(), [''])
        window = appdesc.name.capitalize() + 'App'
        window_class = getattr(module, window, None)
        if window_class is None:
            raise SystemExit("%s app misses a %r attribute" % (
                appdesc.name, window))

        hide_splash()

        embedded = getattr(window_class, 'embedded', False)
        from stoq.gui.application import App
        app = App(window_class, self._login, self._options, self, embedded,
                  app_window, appdesc.name)

        toplevel = app.main_window.get_toplevel()
        icon = toplevel.render_icon(appdesc.icon, gtk.ICON_SIZE_MENU)
        toplevel.set_icon(icon)

        StartApplicationEvent.emit(appdesc.name, app)

        return app

    def _get_available_applications(self):
        from stoq.lib.applist import Application

        permissions = {}
        for settings in self._user.profile.profile_settings:
            permissions[settings.app_dir_name] = settings.has_permission

        descriptions = get_utility(IApplicationDescriptions).get_descriptions()

        available_applications = []

        # sorting by app_full_name
        for name, full, icon, descr in sorted(descriptions,
                                              key=operator.itemgetter(1)):
            if name in self._hidden_apps:
                continue
            if permissions.get(name) and name not in self._blocked_apps:
                available_applications.append(
                    Application(name, full, icon, descr))

        return available_applications

    def _get_current_username(self):
        conn = api.get_connection()
        user = api.get_current_user(conn)
        return user.username

    # Public API

    def login(self, try_cookie=True):
        """
        Do a login
        @param try_cookie: Try to use a cookie if one is available
        @returns: True if login succeed, otherwise false
        """
        user = None
        if try_cookie:
            user = self._login.cookie_login()

        if not user:
            try:
                user = self._login.validate_user()
            except LoginError, e:
                info(e)

        if user:
            self._user = user
        return bool(user)

    def relogin(self):
        """
        Do a relogin, eg switch users
        """
        if self._current_app:
            self._current_app.hide()

        old_user = self._get_current_username()

        if not self.login(try_cookie=False):
            return

        # If the username is the same
        if (old_user == self._get_current_username() and
            self._current_app):
            self._current_app.show()
            return

        # clear the cache, since we switched users
        self._application_cache.clear()

        launcher = Launcher(self._options, self)
        launcher.show()

    def get_app_by_name(self, appname):
        """
        @param appname: a string
        @returns: a L{Application} object
        """
        from stoq.lib.applist import Application
        descriptions = get_utility(IApplicationDescriptions).get_descriptions()
        for name, full, icon, descr in descriptions:
            if name == appname:
                return Application(name, full, icon, descr)

    def get_current_app_name(self):
        """
        Get the name of the currently running application
        @returns: the name
        @rtype: str
        """
        return self._appname

    def block_application(self, appname):
        """Blocks an application to be loaded.
        @param appname: the name of the application. Raises ValueError if the
                        application was already blocked.
        """
        if appname not in self._blocked_apps:
            self._blocked_apps.append(appname)
        else:
            raise ValueError('%s was already blocked.' % appname)

    def unblock_application(self, appname):
        """Unblocks a previously blocked application.
        @param appname: the name of the blocked application. Raises ValueError
                        if the application was not previously blocked.
        """
        if appname in self._blocked_apps:
            self._blocked_apps.remove(appname)
        else:
            raise ValueError('%s was not blocked.' % appname)

    def run(self, appdesc=None):
        from stoq.gui.launcher import Launcher
        app_window = Launcher(self._options, self)
        app_window.show()

        # A GtkWindowGroup controls grabs (blocking mouse/keyboard interaction),
        # by default all windows are added to the same window group.
        # We want to avoid setting modallity on other windows
        # when running a dialog using gtk_dialog_run/run_dialog.
        window_group = gtk.WindowGroup()
        window_group.add_window(app_window.get_toplevel())

        if not appdesc:
            return
        if (appdesc.name != 'launcher' and
            not self._user.profile.check_app_permission(appdesc.name)):
            error(_("This user lacks credentials \nfor application %s") %
                  appdesc.name)
            return

        self.run_embedded(appdesc, app_window)

    def run_embedded(self, appdesc, app_window, params=None):
        app = self._load_app(appdesc, app_window)
        app.launcher = app_window

        self._current_app = app
        self._appname = appdesc.name

        if appdesc.name in self._blocked_apps:
            app_window.show()
            return

        app.run(params)

        # Possibly correct window position (livecd workaround for small
        # screens)
        manager = get_plugin_manager()
        if (api.sysparam(api.get_connection()).DEMO_MODE
            and manager.is_active('ecf')):
            pos = app.main_window.toplevel.get_position()
            if pos[0] < 220:
                app.main_window.toplevel.move(220, pos[1])

        return app

    def run_loop(self):
        if not reactor.running:
            log.debug("Entering reactor")
            reactor.run()
            log.info("Leaving reactor")


def get_shell():
    return _shell
