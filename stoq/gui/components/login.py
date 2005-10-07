#!/usr/bin/env python
# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
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
import gobject
from kiwi.ui.delegates import Delegate
from kiwi.environ import environ
from stoqlib.gui.dialogs import RunnableView

_ = gettext.gettext

class LoginDialog(Delegate, RunnableView):
    toplevel_name = gladefile = "LoginDialog"
    widgets = ('logo_container',
               'username',
               'password',
               'ok_button',
               'cancel_button',
               'notification_label')
    
    def __init__(self, title=None):
        self.keyactions = { gtk.keysyms.Escape : self.on_escape_pressed }
        Delegate.__init__(self, gladefile=self.gladefile, 
                          widgets=self.widgets, 
                          keyactions=self.keyactions,
                          delete_handler=self.close)
        if title:
            self.set_title(title)
        self.setup_widgets()

    def setup_widgets(self):
        self.notification_label.set_text('')
        self.notification_label.set_color('black')
        # Interestingly enough, loading an XPM is slower than a JPG here
        filename = environ.find_resource("pixmap", "logo.xpm")
        
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
        if username and password:
            gobject.idle_add(self._do_login)
        gtk.main()
        return self.retval

