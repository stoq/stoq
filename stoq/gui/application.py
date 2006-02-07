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

import datetime
import gettext

import gtk
from kiwi.environ import app, environ
from stoqlib.gui.application import BaseApp, BaseAppWindow
from stoqlib.gui.search import SearchBar
from stoqlib.database import rollback_and_begin

from stoq.lib.stoqconfig import hide_splash
from stoq.lib.runtime import get_current_user, new_transaction
from stoq.lib.defaults import ALL_ITEMS_INDEX
from stoq.gui.slaves.filter import FilterSlave


_ = gettext.gettext

__program_name__    = "Stoq"
__website__         = 'http://www.stoq.com.br'
__version__         = "0.6.0"
__release_date__    = (2006, 1, 27)


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
    """ Base class for the main window of applications.

    @cvar app_name: This attribute is used when generating titles for
                    applications.  It's also useful if we get a list of
                    available applications with the application names
                    translated. This list is going to be used when
                    creating new user profiles.

    @cvar klist_name: The name of the kiwi list instance used by our
                       application
    @cvar klist_selection_mode: The selection mode for the kiwi list

    """

    app_name = None
    app_icon_name = None
    klist_name = 'klist'
    klist_selection_mode = gtk.SELECTION_BROWSE

    def __init__(self, app):
        self.app = app
        BaseAppWindow.__init__(self, app)
        self.widgets = self.widgets + ['users_menu', 'help_menu',
                                       'StoreCookie', 'ClearCookie',
                                       'ChangeUser']
        user_menu_label = get_current_user().username.capitalize()
        self.users_menu.set_property('label', user_menu_label)
        self.toplevel.connect('map_event', hide_splash)
        if not self.app_name:
            raise ValueError('Child classes must define an app_name '
                             'attribute')
        self.toplevel.set_title(self.get_title())
        self.setup_focus()
        self.conn = new_transaction()
        self._klist = getattr(self, self.klist_name)
        self._klist.set_columns(self.get_columns())
        self._klist.set_selection_mode(self.klist_selection_mode)

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
        about = gtk.AboutDialog()
        about.set_name(__program_name__)
        about.set_version(__version__)
        about.set_website(__website__)
        about.set_comments('Release Date: %s' %
                           datetime.datetime(*__release_date__).strftime('%x'))
        about.set_copyright('Copyright (C) 2005 Async Open Source')

        # Logo
        icon_file = environ.find_resource('pixmaps', 'stoq_logo.png')
        logo = gtk.gdk.pixbuf_new_from_file(icon_file)
        about.set_logo(logo)

        # License
        license = app.find_resource('docs', 'COPYING')
        about.set_license(file(license).read())

        # Authors & Contributors
        authors = app.find_resource('docs', 'AUTHORS')
        lines = [a.strip() for a in file(authors).readlines()]
        lines.append('') # separate authors from contributors
        contributors = app.find_resource('docs', 'CONTRIBUTORS')
        lines.extend([c.strip() for c in file(contributors).readlines()])
        about.set_authors(lines)

        about.run()
        about.destroy()

    #
    # Public API
    #

    def get_columns(self):
        raise NotImplementedError('You should define this method on parent')

    def setup_focus(self):
        """Define this method on child when it's needed."""
        pass

    def get_title(self):
        # This method must be redefined in child when it's needed
        return _('Stoq - %s') % self.app_name

    #
    # Callbacks
    #

    def _on_quit_action__clicked(self, *args):
        self.app.shutdown()

    def on_StoreCookie__activate(self, action):
        self._store_cookie()

    def on_ClearCookie__activate(self, action):
        self._clear_cookie()

    def on_ChangeUser__activate(self, action):
        # Implement a change user dialog here
        raise NotImplementedError


class SearchableAppWindow(AppWindow):
    """ Base class for searchable applications.

    @cvar searchbar_table: The we will query on to perform the search
    @cvar searchbar_use_dates: Do we also need to search by date ?
    @cvar searchbar_result_strings: Plural and singular forms for search
                                     bar results
    @cvar searchbar_labels: A label that will be showed in the search bar
    @cvar filter_slave_label: A label for the filter_slave attached in
                               searchbar

    """

    searchbar_table = None
    searchbar_use_dates = False
    searchbar_result_strings = ()
    searchbar_labels = ()
    filter_slave_label = None

    def __init__(self, app):
        AppWindow.__init__(self, app)
        self._create_searchbar()

    def _create_searchbar(self):
        if not self.searchbar_table:
            return
        filter_slave = self._get_filter_slave()
        self.searchbar = SearchBar(self.conn, self.searchbar_table,
                                   self.get_columns(),
                                   filter_slave=filter_slave,
                                   searching_by_date=self.searchbar_use_dates,
                                   query_args=self.get_query_args())
        extra_query = self.get_extra_query
        if extra_query:
            self.searchbar.register_extra_query_callback(extra_query)
        self.searchbar.register_filter_results_callback(self.filter_results)
        self.searchbar.set_result_strings(*self.searchbar_result_strings)
        self.searchbar.set_searchbar_labels(*self.searchbar_labels)
        self.searchbar.connect('before-search-activate', self.on_searchbar_before_activate)
        self.searchbar.connect('search-activate', self.on_searchbar_activate)
        if filter_slave:
            filter_slave.connect('status-changed',
                                 self.get_on_filter_slave_status_changed())
        self.attach_slave('searchbar_holder', self.searchbar)
        self.searchbar.set_focus()


    def _get_filter_slave(self):
        items = self.get_filter_slave_items()
        if not items:
            return
        self.filter_slave = FilterSlave(items, selected=ALL_ITEMS_INDEX)
        if not self.filter_slave_label:
            raise ValueError('You must define a valid filter_slave_label '
                             'attribute')
        self.filter_slave.set_filter_label(self.filter_slave_label)
        return self.filter_slave

    #
    # Callbacks
    #

    def on_searchbar_before_activate(self, *args):
        rollback_and_begin(self.conn)

    def on_searchbar_activate(self, slave, objs):
        """Use this callback with SearchBar search-activate signal"""
        self._klist.add_list(objs, clear=True)

    #
    # Public API
    #

    def filter_results(self, objects):
        """A hook method for stoqlib SearchBar
        @returns: a python list of objects that will be added in kiwi list
        """
        return objects

    def get_extra_query(self):
        """A hook method for stoqlib SearchBar
        @returns: a sqlbuilder operator that will be added in the searchbar
                  main query
        """


    def get_filter_slave_items(self):
        """Define this method on parent when a FilterSlave is needed to be
        joined in a SearchBar
        @returns: a python list of objects that will be added in a combo. IT
                  must be a list of touples
        """
    def get_query_args(self):
        """Define this method on parent when an extra querry arguments is
        needed.
        @returns: a dictionary with sqlobject select method extra arguments
        """

    def get_on_filter_slave_status_changed(self):
        """Overwride this method on parent when it's needed
        @returns: a method that will be called by filter slave
        """
        return self.searchbar.search_items
