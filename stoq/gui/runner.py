# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

import gettext
import operator

import gtk
from kiwi.component import get_utility
from kiwi.log import Logger
from stoqlib.exceptions import LoginError
from stoqlib.gui.events import StartApplicationEvent
from stoqlib.gui.splash import hide_splash
from stoqlib.database.runtime import get_connection, get_current_user
from stoqlib.lib.interfaces import IApplicationDescriptions
from stoqlib.lib.message import error, info
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.pluginmanager import get_plugin_manager
from stoq.gui.launcher import Launcher

log = Logger('stoq.runner')
_ = gettext.gettext
_runner = None

class ApplicationRunner(object):
    """
    This object is responsible for loading and running an application.

    Note that this object is used very early so all imports should
    be delayed to avoid unnecessary imports which are critical for
    good start-up performance
    """
    def __init__(self, options):
        global _runner
        if _runner:
            raise AssertionError("There can only be one runner at a time")
        _runner = self
        self._current_app = None
        self._options = options
        self._appname = None
        self._application_cache = {}
        from stoqlib.gui.login import LoginHelper
        self._login = LoginHelper(username=options.login_username)
        self._user = None
        self._blocked_apps = []
        self._hidden_apps = []

    def _load_app(self, appdesc, launcher):
        module = __import__("stoq.gui.%s" % (appdesc.name, ),
                            globals(), locals(), [''])
        window = appdesc.name.capitalize() + 'App'
        window_class = getattr(module, window, None)
        if window_class is None:
            raise SystemExit("%s app misses a %r attribute" % (
                appdesc.name, window))

        hide_splash()

        embedded = getattr(window_class, 'launcher_embedded', False)
        from stoq.gui.application import App
        app = App(window_class, self._login, self._options, self, embedded,
                  launcher, appdesc.name)

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
        conn = get_connection()
        user = get_current_user(conn)
        return user.username

    # Public API

    def run(self, appdesc, launcher):
        """
        Runs an application
        @param appname: application to run
        @param launcher: a launcher
        """

        if (appdesc.name != 'launcher' and
            not self._user.profile.check_app_permission(appdesc.name)):
            error(_("This user lacks credentials \nfor application %s") %
                  appdesc.name)
            return

        app = self._load_app(appdesc, launcher)
        app.launcher = launcher

        self._current_app = app
        self._appname = appdesc.name

        if appdesc.name in self._blocked_apps:
            launcher.show()
            return

        app.run()

        # Possibly correct window position (livecd workaround for small
        # screens)
        manager = get_plugin_manager()
        if (sysparam(get_connection()).DEMO_MODE
            and manager.is_active('ecf')):
            pos = app.main_window.toplevel.get_position()
            if pos[0] < 220:
                app.main_window.toplevel.move(220, pos[1])


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

def get_runner():
    """
    @returns: the runner
    @rtype: L{ApplicationRunner}
    """
    return _runner
