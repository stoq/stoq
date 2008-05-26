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
##  Author(s):      Johan Dahlin  <jdahlin@async.com.br>
##

import gettext
import operator

import gtk
from kiwi.log import Logger
from stoqlib.exceptions import LoginError
from stoqlib.gui.events import StartApplicationEvent
from stoqlib.database.runtime import get_connection, get_current_user
from stoqlib.lib.interfaces import IApplicationDescriptions
from stoqlib.lib.message import error, info
from kiwi.component import get_utility


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
        self._login = LoginHelper()
        self._user = None

    def _import(self, appname):
        module = __import__("stoq.gui.%s.app" % appname,
                            globals(), locals(), [''])
        if not hasattr(module, "main"):
            raise RuntimeError(
                "Application %s must have a app.main() function")
        return module

    def _show_splash(self):
        from stoqlib.gui.splash import SplashScreen
        from kiwi.environ import environ

        log.debug('displaying splash screen')
        splash = SplashScreen(environ.find_resource("pixmaps", "splash.jpg"))
        splash.show()

        return splash

    def _load_app(self, appdesc):
        splash = None
        # Only show the splash screen the first time
        if not self._current_app:
            splash = self._show_splash()

        module = self._import(appdesc.name)
        window_class = module.main(self._login)

        from stoq.gui.application import App
        app = App(window_class, self._login, self._options, self)

        if splash:
            import gobject
            gobject.idle_add(splash.hide)

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
            if permissions[name]:
                available_applications.append(
                    Application(name, full, icon, descr))

        return available_applications

    def _get_current_username(self):
        conn = get_connection()
        user = get_current_user(conn)
        return user.username

    # Public API

    def choose(self):
        """
        Displays a list of applications
        @returns: selected application or None if nothing was selected
        """

        available_applications = self._get_available_applications()
        if len(available_applications) == 1:
            return available_applications[0]

        from stoqlib.gui.base.dialogs import run_dialog
        from stoqlib.gui.login import SelectApplicationsDialog

        return run_dialog(SelectApplicationsDialog(self._appname,
                                                   available_applications))


    def run(self, appdesc):
        """
        Runs an application
        @param appname: application to run
        """
        if not self._user.profile.check_app_permission(appdesc.name):
            error(_("This user lacks credentials \nfor application %s") %
                  appdesc.name)
            return

        if self._current_app:
            self._current_app.hide()

        app = self._application_cache.get(appdesc.name)
        if app is None:
            app = self._load_app(appdesc)
            self._application_cache[appdesc.name] = app

        self._current_app = app
        self._appname = appdesc.name

        app.run()

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
            self._current_app.shutdown()
            return

        # If the username is the same
        if (old_user == self._get_current_username() and
            self._current_app):
            self._current_app.show()
            return

        appname = self.choose()
        if not appname:
            self._current_app.shutdown()
            return

        self.run(appname)

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

def get_runner():
    """
    @returns: the runner
    @rtype: L{ApplicationRunner}
    """
    return _runner
