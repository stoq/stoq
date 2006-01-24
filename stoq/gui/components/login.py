#!/usr/bin/env python
# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
"""
gui/components/login.py:

   Login dialog for users authentication.
"""

import gettext

import gtk
from kiwi.environ import environ
from kiwi.ui.delegates import Delegate
from kiwi.ui.widgets.list import Column
from kiwi.python import Settable
from stoqlib.gui.dialogs import RunnableView

from stoq.lib.applist import get_app_descriptions

_ = gettext.gettext


class LoginDialog(Delegate, RunnableView):
    toplevel_name = gladefile = "LoginDialog"
    size = (280, 230)
    
    def __init__(self, title=None, choose_applications=True):
        self.keyactions = { gtk.keysyms.Escape : self.on_escape_pressed }
        Delegate.__init__(self, gladefile=self.gladefile, 
                          widgets=self.widgets, 
                          keyactions=self.keyactions,
                          delete_handler=gtk.main_quit)
        if title:
            self.set_title(title)
        self.choose_applications = choose_applications
        if self.choose_applications:
            self.size = 450, 250
            self.setup_applist()
        self.setup_widgets()

    def _get_columns(self):
        return [Column('icon_name', use_stock=True, 
                       justify=gtk.JUSTIFY_LEFT, expand=True,
                       icon_size=gtk.ICON_SIZE_LARGE_TOOLBAR),
                Column('app_full_name', data_type=str, 
                       expand=True)]

    def setup_applist(self):
        self.klist.get_treeview().set_headers_visible(False)
        self.klist.set_columns(self._get_columns())

        apps = get_app_descriptions()
        # sorting by app_full_name
        apps = [(app_full_name, app_name, app_icon_name) 
                    for app_name, app_full_name, app_icon_name in apps]
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

    def setup_widgets(self):
        self.get_toplevel().set_size_request(*self.size)
        self.notification_label.set_text('')
        self.notification_label.set_color('black')
        filename = environ.find_resource("pixmaps", "stoq_logo.png")
        
        gtkimage = gtk.Image()
        gtkimage.set_from_file(filename)

        self.logo_container.add(gtkimage)
        self.logo_container.show_all()

    def _initialize(self, username=None, password=None):
        self.username.set_text(username or "")
        self.password.set_text(password or "")
        self.retval = None
        self.username.grab_focus()

    def on_escape_pressed(self, window, event, extra):
        self.close()
        
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
        if self.choose_applications:
            selected = self.klist.get_selected()
            app_name = selected.app_name
        else:
            app_name = None
        self.retval = username, password, app_name
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

