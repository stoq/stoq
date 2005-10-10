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
lib/config.py:

    Configuration file for stoq applications
"""
    
import gettext
import os
import sys
import binascii
import time

import gtk
import gobject
from stoqlib.exceptions import (DatabaseError, _warn, UserProfileError,
                                LoginError)
from stoqlib.database import set_model_connection_func
from stoqlib.gui.dialogs import notify_dialog
from stoqlib.gui.search import set_max_search_results
from stoqlib.gui.gtkadds import register_iconsets

from stoq.gui.components.login import LoginDialog
from stoq.lib.configparser import StoqConfigParser
from stoq.lib.parameters import sysparam
from stoq.lib.runtime import (new_transaction, set_current_user,
                              get_connection)
from stoq.domain.person import PersonAdaptToUser
from stoq.domain.tables import check_tables

_ = gettext.gettext
SPLASH_TIMEOUT = 4000


class AppConfig:
    """AppConfig provides features for:
       - Getting the application list
       - Initializing the framework for an application
       - Managing user cookies and driving authentication
    """

    splash = 0
    _applications = None
    
    def __init__(self, domain):
        self.domain = domain
        self.config_data = StoqConfigParser(self.domain)

    def init_log(self):
        sys.stderr.write("-"*76 + "\n")
       
    def log(self, s):
        sys.stderr.write("%s: %s\n" % (log_header(), s))



    #
    # Application list accessors
    #



    def check_dir_and_create(self, dir):
        if not os.path.isdir(dir):
            if os.path.exists(dir):
                self.config_data.check_permissions(dir, executable=True)
                os.remove(dir)
                _warn('A %s file already exist and was removed.' % dir)
            os.mkdir(dir)
            return
        self.config_data.check_permissions(dir, executable=True)



    #
    # Application setup. 
    #




    def setup_app(self, appname, splash=False):
        try:
            check_tables()
        except DatabaseError, e:
            self.abort_mission(str(e), _('Database Error'))
        
        self.appname = appname
        self.splash = splash

        # Ensure user's application directory is created
        domain = self.domain
        homepath = self.config_data.get_homepath()
        self.check_dir_and_create(homepath)

        env_log = os.environ.get('%s_LOGFILE' % domain.upper())
        if env_log:
            sys.stderr = open(env_log, 'a', 0)
        elif self.config_data.has_option("logfile"):
            option = self.config_data.get_option("logfile")
            logfile = os.path.expanduser(option)
            sys.stderr = open(logfile, 'a', 0)

        # Log startup time
        self.init_log()
        self.log("Stoq: initializing application %s" % appname)

        # Registering some new important stock icons
        register_iconsets()

        conn = get_connection()
        max_search_results = sysparam(conn).MAX_SEARCH_RESULTS
        set_max_search_results(max_search_results)

        set_model_connection_func(new_transaction)
        assert self.validate_user()



    #
    # User validation and AppHelper setup
    #



    def _lookup_user(self, username, password):
        # This function is really just a post-validation item. 
        table = PersonAdaptToUser
        res = table.select(table.q.username == '%s' % username)

        msg = _("Invalid user or password")
        if not res.count():
            raise LoginError(msg)
            
        if res.count() != 1:
            raise DatabaseInconsistency("It should exists only one instance "
                                        "in database for this username, got "
                                        "%d instead" % res.count())
        user = res[0]
        if not user.password == password:
            raise LoginError(msg)

        if not user.profile.check_app_permission(self.appname):
            msg = _("This user lacks credentials \nfor application %s")
            raise UserProfileError(msg % self.appname)
        return user
    
    def check_user(self, username, password):
        user = self._lookup_user(username, password) 
        set_current_user(user)

    def validate_user(self):
        # Loop for logins
        retry = 0
        retry_msg = None
        dialog = None
        while retry < 3:
            # Try and grab credentials from cookie or dialog
            ret = self.check_cookie()
                
            if ret:
                msg = "Logging in using cookie credentials"
                self.log(msg)
            else:
                self.splash = 0 
                if not dialog:
                    dialog = LoginDialog(_("Access Control"))

                ret = dialog.run(msg=retry_msg)

            # user cancelled (escaped) the login dialog
            if not ret:
                self.abort_mission()

            # Use credentials
            username, password = ret
            if not username:
                retry_msg = _("specify an username")
                continue
                
            try:
                self.check_user(username, password)
            except (LoginError, UserProfileError), e:
                # We don't hide the dialog here; it's kept open so the
                # next loop we just can call run() and display the error
                self.clear_cookie()
                retry += 1
                retry_msg = str(e)
            except DatabaseError, e:
                if dialog:
                    dialog.destroy()
                self.abort_mission(str(e))
            else:
                self.log("Authenticated user %s" % username)
                if dialog:
                    dialog.destroy()
                return True

        if dialog:
            dialog.destroy()
        self.abort_mission("Depleted attempts of authentication")
        return False
        

    #
    # Cookie handling
    #



    def get_cookiefile(self):
        cookiefile = os.path.join(self.config_data.get_homepath(), "cookie")
        if os.path.exists(cookiefile):
            self.config_data.check_permissions(cookiefile, writable=True)
        return cookiefile

    def clear_cookie(self):
        cookiefile = self.get_cookiefile()
        if os.path.exists(cookiefile):
            os.remove(cookiefile)

    def store_cookie(self, username, password):
        cookiefile = self.get_cookiefile()
        self._store_cookie(cookiefile, username, password)

    def check_cookie(self):
        cookiefile = self.get_cookiefile()
        if not os.path.exists(cookiefile):
            return

        cookiedata = open(cookiefile).read()
        try:
            username, text = cookiedata.split(":")
            password = binascii.a2b_base64(text)
            return username, password
        except (ValueError, binascii.Error):
            print "Warning: invalid cookie file, erasing"
            os.remove(cookiefile)
            return

    def _store_cookie(self, cookiefile, username, password):
        fd = open(cookiefile, "w")
        # obfuscate password to avoid it being easily identified when
        # editing file on screen. this is *NOT* encryption!
        text = binascii.b2a_base64(password)
        fd.write("%s:%s" % (username, text))
        fd.close()



    #
    # Exit strategies
    #



    def abort_mission(self, msg=None, title=None):
        if msg:
            notify_dialog(msg, title)
        raise SystemExit




#
# Splash screen code
#



def show_splash(splash_path):
    msg = "The stoq directory %s doesn't exists." % splash_path
    assert os.path.isdir(splash_path), msg

    # Interestingly enough, loading an XPM is slower than a JPG here
    f = os.path.join(splash_path, "splash.jpg")

    gtkimage = gtk.Image()
    gtkimage.set_from_file(f)

    w = gtk.Window()
    w.set_title('Stoq')
    w.add(gtkimage)
    w.set_position(gtk.WIN_POS_CENTER)
    w.show_all()

    time.sleep(0.01)
    while gtk.events_pending():
        time.sleep(0.01)
        gtk.main_iteration()
    gobject.timeout_add(SPLASH_TIMEOUT, hide_splash)

    global splash_win
    splash_win = w

    
def hide_splash(*args):
    global splash_win
    if splash_win:
        splash_win.hide()

splash_win = None



#
# Exception and log stuff
#



def log_header():
    now = time.strftime("%Y-%m-%d %H:%M")
    return "%s (%s)" % (now, os.getpid())

def excepthook(tp, v, t):
    # Reimplement the module formatting PyErr_Display does, more or less
    if tp.__module__ == "exceptions":
        tp = str(tp)[11:]
    elif tp.__module__ is None:
        tp = "<unknown> %s" % str(tp)
    sys.__excepthook__("%s: %s" % (log_header(), tp), v, t)

sys.excepthook = excepthook
