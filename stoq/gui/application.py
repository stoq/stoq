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
gui/application.py:

    Base classes for application's GUI
"""
import gtk

from stoqlib.gui.application import BaseApp, BaseAppWindow
from stoqlib.gui.reload import reload_world

# TODO To be implemented
# from components.registry import About
from stoq.lib.stoqconfig import hide_splash
from stoq.lib.runtime import get_current_user

SYNC_TIME = 60000


# TODO we need to find a better way(the right way) about how to this
# kiwi.ui.views.set_decimal_separator(",")

# TODO waiting for kiwi suport
# kiwi.ui.views.enable_sane_editables()


#TODO: To be implemented
# kiwi.basic.set_autocombo_min_char(5)

class App(BaseApp):
    def __init__(self, window_class, appconfig):
        self.config = appconfig
        self.window_class = window_class
        BaseApp.__init__(self, window_class, SYNC_TIME)

    def reinit(self):
        BaseApp.__init__(self, self.window_class, SYNC_TIME)

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

    def __init__(self, app):
        self.app = app
        self.widgets = self.widgets[:] + ('users_menu',)




        self.keyactions = { gtk.keysyms.F10: self.inspect, 
                            gtk.keysyms.F9: self.reload_world }
        BaseAppWindow.__init__(self, app, keyactions=self.keyactions)
        if hasattr(self, 'about_menuitem'):
            self.about_menuitem.connect('activate', self.run_about)

        user_menu_label = get_current_user().username.capitalize()
        self.users_menu.set_property('label', user_menu_label)

        self.toplevel.connect('map_event', hide_splash)
        
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


    def run_about(self, *args):
        """ Open the window about. """
        # TODO To be implemented
        # self.run_dialog(About)
    
    def reload_world(self, *args, **kwargs):
        reload_world()
        # If the application has a sync(), it's time to call it
        if hasattr(self, "sync"):
            print "Syncing database connection..."
            self.sync()
            print "done"

    def inspect(self, *args, **kwargs):
        scope = globals().copy()
        scope.update(locals())
        if kwargs.has_key('scope'):
            scope.update(kwargs['scope'])

        import code
        try:
            import readline
        except ImportError:
            print "Module readline not available."
        else:
            import rlcompleter
            # pyflakes
            assert rlcompleter
            readline.parse_and_bind("tab: complete")
        print scope.keys()
        print "DR. WATSON v1.0"

        code.interact(local=scope)

    def sync(self):
        # Applications that want to synchronize periodically must define a
        # sync method.
        pass



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
