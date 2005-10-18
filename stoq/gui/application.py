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
##  Author(s):      Evandro Vale Miquelito  <evandro@async.com.br>
##
"""
gui/application.py:

    Base classes for application's GUI
"""

import os
import datetime
import gettext

import gtk
from stoqlib.gui.application import BaseApp, BaseAppWindow

from stoq.lib.stoqconfig import hide_splash
from stoq.lib.runtime import get_current_user
from stoq.lib.environ import get_docs_dir, get_pixmaps_dir

_ = gettext.gettext

__program_name__    = "Stoq"
__website__         = 'http://www.stoq.com.br'
__version__         = "0.3.0"
__release_date__    = (2005, 10, 7)
    

class App(BaseApp):

    def __init__(self, window_class, appconfig):
        self.config = appconfig
        self.window_class = window_class
        BaseApp.__init__(self, window_class)

    def shutdown(self, *args):
        BaseApp.shutdown(self, *args)

    def revalidate_user(self, *args):
        self.shutdown()
        self.config.clear_cookie()
        # validate_user raises SystemExit if things go wrong
        self.config.validate_user()
        self.reinit()
        self.run()

class AppWindow(BaseAppWindow):
    """ Base class for the main window of applications."""

    # This attribute is used when generating titles for applications. 
    # It's also useful if we get a list of available applications with the
    # application names translated. This list is going to be used when
    # creating new user profiles.
    app_name = None

    def __init__(self, app):
        self.app = app
        self.widgets = self.widgets[:] + ('users_menu', 'help_menu')
        BaseAppWindow.__init__(self, app)
        user_menu_label = get_current_user().username.capitalize()
        self.users_menu.set_property('label', user_menu_label)
        self.toplevel.connect('map_event', hide_splash)
        if not self.app_name:
            raise ValueError('Child classes must define an app_name '
                             'attribute')
        self.toplevel.set_title(self.get_title())

    def get_title(self):
        # This method must be redefined in child when it's needed
        return _('Stoq - %s') % self.app_name
        
    def _store_cookie(self, *args):
        u = get_current_user()
        # XXX: with password criptografy, we need to ask it again
        self.app.config.store_cookie(u.username, u.password)
        if hasattr(self, 'user_menu'):
            self._reset_user_menu()

    def _clear_cookie(self, *args):
        self.app.config.clear_cookie()
        if hasattr(self, 'user_menu'):
            self._reset_user_menu()

    def _reset_user_menu(self):
        assert self.user_menu
#         label = self.user_menu.children()[0]
#         username = runtime.get_current_user().username
#         if self.app.config.check_cookie():
#             self.clear_cookie_menuitem.set_sensitive(1)
#             self.save_cookie_menuitem.set_sensitive(0)
#             star = " [$]"
#         else:
#             # A fixed width to avoid changes in the menu width
#             star = "    "
#             self.clear_cookie_menuitem.set_sensitive(0)
#             self.save_cookie_menuitem.set_sensitive(1)
#         label.set_text("user: %s%s" % (username, star))

    def _run_about(self, *args):
        docs = get_docs_dir()
        pixmaps = get_pixmaps_dir()

        about = gtk.AboutDialog()
        about.set_name(__program_name__)
        about.set_version(__version__)

        author_lines = file(os.path.join(docs, 'AUTHORS')).readlines()
        authors = [a.strip() for a in author_lines]
        # separate authors from contributors
        authors.append('') 
        contr_lines = file(os.path.join(docs, 'CONTRIBUTORS')).readlines()
        contributors = [c.strip() for c in contr_lines]
        authors.extend(contributors)
        about.set_authors(authors)

        icon_file = os.path.join(pixmaps, 'stoq_logo.png')
        logo = gtk.gdk.pixbuf_new_from_file(icon_file)
        about.set_logo(logo)
            
        license = file(os.path.join(docs, 'COPYING')).read()
        about.set_license(license)
        about.set_website(__website__)
        release_date = datetime.datetime(*__release_date__).strftime('%x')
        about.set_comments('Release Date: %s' % release_date)
        copyright = 'Copyright (C) 2005 Async Open Source'
        about.set_copyright(copyright)
        about.run()
        about.destroy()



    #
    # Hooks
    #



    def filter_results(self, objects):
        """A hook method for stoqlib SearchBar"""
        return objects

    def get_extra_query(self):
        """A hook method for stoqlib SearchBar"""
    


    #
    # Callbacks
    #



    def _on_quit_action__clicked(self, *args):
        self.app.shutdown()
