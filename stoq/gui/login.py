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
##              Johan Dahlin <jdahlin@async.com.br>
##
""" Login dialog for user authentication"""

import gettext

import gtk
from kiwi.component import get_utility, provide_utility
from kiwi.log import Logger
from kiwi.python import Settable
from kiwi.ui.delegates import GladeSlaveDelegate
from kiwi.ui.widgets.list import Column
from stoqlib.database.interfaces import ICurrentUser
from stoqlib.database.runtime import get_connection
from stoqlib.exceptions import DatabaseError, LoginError, UserProfileError
from stoqlib.domain.interfaces import IUser
from stoqlib.domain.person import Person
from stoqlib.gui.login import LoginDialog
from stoqlib.lib.interfaces import (IApplicationDescriptions,
                                    CookieError, ICookieFile)
from stoqlib.lib.message import warning


_ = gettext.gettext
RETRY_NUMBER = 3
log = Logger('stoq.config')


class StoqLoginDialog(LoginDialog):
    def __init__(self, title=None, choose_applications=True):
        LoginDialog.__init__(self, title)
        self.choose_applications = choose_applications
        if self.choose_applications:
            self.slave = SelectApplicationsSlave()
            self.attach_slave('applist_holder', self.slave)
            self.size = 450, 250
            self.get_toplevel().set_size_request(*self.size)


    def get_app_name(self):
        if self.choose_applications:
            selected = self.slave.klist.get_selected()
            return selected.app_name
        return None


class SelectApplicationsSlave(GladeSlaveDelegate):
    gladefile = "SelectApplicationsSlave"

    def __init__(self):
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)
        self._setup_applist()

    def _setup_applist(self):
        self.klist.get_treeview().set_headers_visible(False)
        self.klist.set_columns(self._get_columns())

        descriptions = get_utility(IApplicationDescriptions).get_descriptions()
        # sorting by app_full_name
        apps = [(full_name, name, icon_name)
                    for name, full_name, icon_name in descriptions]
        apps.sort()
        for app_full_name, app_name, app_icon_name in apps:
            model = Settable(app_name=app_name, app_full_name=app_full_name,
                             icon_name=app_icon_name)
            self.klist.append(model)
        if not len(self.klist):
            raise ValueError('Application list should have items at '
                             'this point')
        self.klist.select(self.klist[0])
        self.app_list.show()

    def _get_columns(self):
        return [Column('icon_name', use_stock=True,
                       justify=gtk.JUSTIFY_LEFT, expand=True,
                       icon_size=gtk.ICON_SIZE_LARGE_TOOLBAR),
                Column('app_full_name', data_type=str,
                       expand=True)]

class LoginHelper:

    def __init__(self, appname, options):
        self.appname = appname
        self.options = options

        if not self.validate_user():
            raise LoginError('Could not authenticate in the system')

    def _check_user(self, username, password):
        # This function is really just a post-validation item.
        user = Person.iselectOneBy(IUser, username=username,
                                   connection=get_connection())

        if not user:
            raise LoginError(_("Invalid user or password"))

        if not user.is_active:
            raise LoginError(_('This user is inactive'))

        if user.password is not None and user.password != password:
            raise LoginError(_("Invalid user or password"))

        if not user.profile.check_app_permission(self.appname):
            msg = _("This user lacks credentials \nfor application %s")
            raise UserProfileError(msg % self.appname)

        # ICurrentUser might already be provided which is the case when
        # creating a new database, thus we need to replace it.
        provide_utility(ICurrentUser, user, replace=True)

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
                dialog = StoqLoginDialog(_("Access Control"),
                                         choose_applications)
            ret = dialog.run(username, password, msg=retry_msg)

            # user cancelled (escaped) the login dialog
            if not ret:
                self._abort()

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
                self._abort(str(e))
            else:
                log.info("Authenticated user %s" % username)
                if dialog:
                    dialog.destroy()
                return True

        if dialog:
            dialog.destroy()
        self._abort("Depleted attempts of authentication")
        return False

    #
    # Exit strategies
    #

    def _abort(self, msg=None, title=None):
        if msg:
            warning(msg)
        raise SystemExit

