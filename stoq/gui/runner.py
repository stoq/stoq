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

from kiwi.log import Logger
from stoqlib.lib.message import error

log = Logger('stoq.runner')
_ = gettext.gettext

class ApplicationRunner(object):
    """
    This object is responsible for loading and running an application.

    Note that this object is used very early so all imports should
    be delayed to avoid unnecessary imports which are critical for
    good start-up performance
    """
    def __init__(self, config, options):
        self._current_app = None
        self._config = config
        self._options = options
        self._appname = None
        self._application_cache = {}

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

    def _load_app(self, appname):
        splash = None
        # Only show the splash screen the first time
        if not self._current_app:
            splash = self._show_splash()

        module = self._import(appname)
        window_class = module.main(self._config)

        from stoq.gui.application import App
        app = App(window_class, self._config, self._options, self)

        if splash:
            import gobject
            gobject.idle_add(splash.hide)

        return app

    # Public API

    def choose(self):
        """
        Displays a list of applications
        @param: selected application or None if nothing was selected
        """
        from stoqlib.gui.base.dialogs import run_dialog
        from stoq.gui.login import SelectApplicationsDialog
        return run_dialog(SelectApplicationsDialog(self._appname))

    def run(self, appname):
        """
        Runs an application
        @param appname: application to run
        """
        if not self._config.user.profile.check_app_permission(appname):
            error(_("This user lacks credentials \nfor application %s") %
                  appname)
            return

        if self._current_app:
            self._current_app.hide()

        app = self._application_cache.get(appname)
        if app is None:
            app = self._load_app(appname)
            self._application_cache[appname] = app

        self._current_app = app
        self._appname = appname

        app.run()
