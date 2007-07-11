# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s):  Evandro Vale Miquelito  <evandro@async.com.br>
##              Johan Dahlin <jdahlin@async.com.br>
##
""" Login dialog for users authentication"""

import gtk
from kiwi.component import get_utility, provide_utility
from kiwi.environ import environ
from kiwi.log import Logger
from kiwi.ui.delegates import GladeDelegate, GladeSlaveDelegate
from kiwi.ui.widgets.list import Column

from stoqlib.database.interfaces import ICurrentUser
from stoqlib.database.runtime import get_connection
from stoqlib.exceptions import DatabaseError, LoginError, UserProfileError
from stoqlib.domain.interfaces import IUser
from stoqlib.domain.person import Person
from stoqlib.gui.base.dialogs import (BasicWrappingDialog, run_dialog,
                                      RunnableView)
from stoqlib.lib.interfaces import CookieError, ICookieFile
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

RETRY_NUMBER = 3
log = Logger('stoq. config')

class LoginDialog(GladeDelegate, RunnableView):
    toplevel_name = gladefile = "LoginDialog"
    size = (280, 230)

    def __init__(self, title=None):
        self.keyactions = { gtk.keysyms.Escape : self.on_escape_pressed }
        GladeDelegate.__init__(self, gladefile=self.gladefile,
                          keyactions=self.keyactions,
                          delete_handler=gtk.main_quit)
        if title:
            self.set_title(title)
        self.setup_widgets()

    def setup_widgets(self):
        self.get_toplevel().set_size_request(*self.size)
        self.notification_label.set_text('')
        self.notification_label.set_color('black')
        filename = environ.find_resource("pixmaps", "stoq_logo.png")

        gtkimage = gtk.Image()
        gtkimage.set_from_file(filename)

        self.logo_container.add(gtkimage)
        self.logo_container.show_all()

    def force_username(self, username):
        self.username.set_text(username)
        self.username.set_sensitive(False)
        self.password.grab_focus()

    def _initialize(self, username=None, password=None):
        self.username.set_text(username or "")
        self.password.set_text(password or "")
        self.retval = None
        self.username.grab_focus()

    def on_escape_pressed(self):
        gtk.main_quit()

    def on_delete_event(self, window, event):
        self.close()

    def on_ok_button__clicked(self, button):
        self._do_login()

    def on_cancel_button__clicked(self, button):
        gtk.main_quit()

    def on_username__activate(self, entry):
        self.password.grab_focus()

    def on_password__activate(self, entry):
        self._do_login()

    def set_field_sensitivity(self, sensitive=True):
        for widget in (self.username, self.password, self.ok_button,
                       self.cancel_button):
            widget.set_sensitive(sensitive)

    def _do_login(self):
        username = self.username.get_text().strip()
        password = self.password.get_text().strip()
        self.retval = username, password
        self.set_field_sensitivity(False)
        self.notification_label.set_color('black')
        msg = _(" Authenticating user...")
        self.notification_label.set_text(msg)
        while gtk.events_pending():
            gtk.main_iteration()
        gtk.main_quit()
        self.set_field_sensitivity(True)

    def run(self, username=None, password=None, msg=None):
        if msg:
            self.notification_label.set_color('red')
            self.notification_label.set_text(msg)
        self._initialize(username, password)
        self.show()
        gtk.main()
        return self.retval

class SelectApplicationsDialog(GladeSlaveDelegate):
    gladefile = "SelectApplicationsSlave"
    title = _('Choose application')
    size = (-1, 350)

    def __init__(self, appname=None, applications=None):
        """
        @param appname: application name to select
        @param applications: applications to show
        @type applications: list of Application
        """
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)

        self.logo.set_from_file(environ.find_resource("pixmaps",
                                                      "stoq_logo.png"))

        self.main_dialog = BasicWrappingDialog(self, self.title,
                                               size=self.size)
        toplevel = self.main_dialog.get_toplevel()
        icon = toplevel.render_icon('stoq-warehouse-app', gtk.ICON_SIZE_MENU)
        toplevel.set_icon(icon)

        self.applications = applications
        self._setup_applist()

        # O(n), but not so important, we have few apps.
        for model in self.klist:
            if model.name == appname:
                self.klist.select(model)
                break

    def get_toplevl(self):
        return self.main_dialog.get_toplevel()

    def _setup_applist(self):
        self.klist.get_treeview().set_headers_visible(False)
        self.klist.set_columns(self._get_columns())
        self.klist.set_size_request(200, -1)
        self.klist.extend(self.applications)

        if not len(self.klist):
            raise ValueError('Application list should have items at '
                             'this point')
        self.klist.select(self.klist[0])
        self.app_list.show()

    def _get_columns(self):
        return [Column('icon', use_stock=True,
                       justify=gtk.JUSTIFY_LEFT,
                       icon_size=gtk.ICON_SIZE_LARGE_TOOLBAR),
                Column('fullname', data_type=str,
                       expand=True, searchable=True)]

    def on_confirm(self):
        return self.klist.get_selected()

    def on_cancel(self):
        return None

    def validate_confirm(self):
        return True

    def on_klist__selection_changed(self, klist, model):
        if model:
            self.description.set_text(model.description)

    def on_klist__row_activated(self, klist, model):
        self.main_dialog.confirm()

    def run(self):
        return run_dialog(self())

class LoginHelper:

    def __init__(self, username=None):
        self.user = None
        self._force_username = username

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

        # ICurrentUser might already be provided which is the case when
        # creating a new database, thus we need to replace it.
        provide_utility(ICurrentUser, user, replace=True)
        return user

    def cookie_login(self):
        try:
            username, password = get_utility(ICookieFile).get()
        except CookieError:
            log.info("Not using cookie based login")
            return

        try:
            user = self._check_user(username, password)
        except (LoginError, UserProfileError, DatabaseError), e:
            log.info("Cookie login failed: %r" % e)
            return

        log.info("Logging in using cookie credentials")
        return user

    def validate_user(self):
        """
        @returns: a user object
        """
        log.info("Showing login dialog")
        # Loop for logins
        retry = 0
        retry_msg = None
        dialog = None
        while retry < RETRY_NUMBER:
            username = self._force_username
            password = None

            if not dialog:
                dialog = LoginDialog(_("Access Control"))
                if self._force_username:
                    dialog.force_username(username)

            ret = dialog.run(username, password, msg=retry_msg)

            # user cancelled (escaped) the login dialog
            if not ret:
                return

            # Use credentials
            if not (isinstance(ret, (tuple, list)) and len(ret) == 2):
                raise ValueError('Invalid return value, got %s'
                                 % str(ret))

            username, password = ret

            if not username:
                retry_msg = _("specify an username")
                continue

            try:
                user = self._check_user(username, password)
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

                return user

        if dialog:
            dialog.destroy()
        raise LoginError("Depleted attempts of authentication")

    #
    # Exit strategies
    #

    def _abort(self, msg=None, title=None):
        if msg:
            warning(msg)
        raise SystemExit

