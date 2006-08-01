# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
##  Author(s):  Evandro Vale Miquelito  <evandro@async.com.br>
##
""" Configuration file for stoq applications """

import gettext
import time

import gtk
from kiwi.component import get_utility, provide_utility
from kiwi.log import Logger
from kiwi.environ import environ
from stoqlib.exceptions import (DatabaseError, UserProfileError,
                                LoginError, DatabaseInconsistency)
from stoqlib.lib.interfaces import CookieError, ICookieFile, ICurrentUser
from stoqlib.lib.message import warning
from stoqlib.lib.runtime import get_connection
from stoqlib.domain.person import PersonAdaptToUser

from stoq.gui.login import StoqLoginDialog

RETRY_NUMBER = 3

_ = gettext.gettext
log = Logger('stoq.config')

class AppConfig:
    """AppConfig provides features for:
       - Initializing the framework for an application
    """


    def __init__(self, appname):
        self.appname = appname

        if not self.validate_user():
            raise LoginError('Could not authenticate in the system')


    #
    # User validation and AppHelper setup
    #

    def _check_user(self, username, password):
        # This function is really just a post-validation item.
        table = PersonAdaptToUser
        conn = get_connection()
        res = table.select(table.q.username == '%s' % username,
                           connection=conn)

        msg = _("Invalid user or password")
        count = res.count()
        if not count:
            raise LoginError(msg)

        if count != 1:
            raise DatabaseInconsistency("It should exists only one instance "
                                        "in database for this username, got "
                                        "%d instead" % count)
        user = res[0]
        if not user.is_active:
            raise LoginError(_('This user is inactive'))

        if not user.password == password:
            raise LoginError(msg)

        if not user.profile.check_app_permission(self.appname):
            msg = _("This user lacks credentials \nfor application %s")
            raise UserProfileError(msg % self.appname)

        provide_utility(ICurrentUser, user)

    def _cookie_login(self):
        try:
            username, password = get_utility(ICookieFile).get()
        except CookieError:
            log.info("Not using cookie based login")
            return False

        try:
            self._check_user(username, password)
        except (LoginError, UserProfileError, DatabaseError), e:
            log.info("Cookie login failed: %r" % e)
            return False

        log.info("Logging in using cookie credentials")
        return True

    def validate_user(self):
        if self._cookie_login():
            return True

        log.info("Showing login dialog")
        # Loop for logins
        retry = 0
        retry_msg = None
        dialog = None
        choose_applications = self.appname is None
        while retry < RETRY_NUMBER:
            username = password = appname = None

            if not dialog:
                hide_splash()
                dialog = StoqLoginDialog(_("Access Control"),
                                         choose_applications)
            ret = dialog.run(username, password, msg=retry_msg)

            # user cancelled (escaped) the login dialog
            if not ret:
                self.abort_mission()

            # Use credentials
            if not (isinstance(ret, (tuple, list)) and len(ret) == 3):
                raise ValueError('Invalid return value, got %s'
                                 % str(ret))

            username, password, appname = ret

            if choose_applications:
                self.appname =  appname

            if not username:
                retry_msg = _("specify an username")
                continue

            try:
                self._check_user(username, password)
            except (LoginError, UserProfileError), e:
                # We don't hide the dialog here; it's kept open so the
                # next loop we just can call run() and display the error
                get_utility(ICookieFile).clear()
                retry += 1
                retry_msg = str(e)
            except DatabaseError, e:
                if dialog:
                    dialog.destroy()
                self.abort_mission(str(e))
            else:
                log.info("Authenticated user %s" % username)
                if dialog:
                    dialog.destroy()
                return True

        if dialog:
            dialog.destroy()
        self.abort_mission("Depleted attempts of authentication")
        return False

    #
    # Exit strategies
    #

    def abort_mission(self, msg=None, title=None):
        if msg:
            warning(msg)
        raise SystemExit

    #
    # Splash screen code
    #

def show_splash():
    gtkimage = gtk.Image()
    gtkimage.set_from_file(environ.find_resource("pixmaps", "splash.jpg"))
    gtkimage.show()
    w = gtk.Window()
    f = gtk.Frame()
    f.set_property('shadow-type', gtk.SHADOW_OUT)
    w.add(f)
    f.show()
    w.set_decorated(False)
    f.add(gtkimage)
    w.set_position(gtk.WIN_POS_CENTER)
    w.show_now()
    time.sleep(0.01)
    while gtk.events_pending():
        time.sleep(0.01)
        gtk.main_iteration()
    global splash_win
    splash_win = w


def hide_splash(*args):
    global splash_win
    if splash_win:
        splash_win.destroy()
        splash_win = None

splash_win = None
