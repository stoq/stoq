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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s):      Evandro Vale Miquelito  <evandro@async.com.br>
##
""" Base classes for application's GUI """

import datetime
import gettext

import gtk
from kiwi.component import get_utility
from kiwi.environ import environ
from stoqlib.database.database import rollback_and_begin
from stoqlib.database.runtime import get_current_user, new_transaction
from stoqlib.exceptions import UserProfileError
from stoqlib.lib.defaults import ALL_ITEMS_INDEX
from stoqlib.lib.interfaces import ICookieFile
from stoqlib.gui.base.application import BaseApp, BaseAppWindow
from stoqlib.gui.base.dialogs import print_report
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.search import SearchBar
from stoqlib.gui.introspection import introspect_slaves
from stoqlib.gui.slaves.filterslave import FilterSlave

import stoq
from stoq.gui.login import SelectApplicationsDialog


_ = gettext.gettext


class App(BaseApp):

    def __init__(self, window_class, appconfig):
        self.config = appconfig
        self.options = appconfig.options
        self.window_class = window_class
        BaseApp.__init__(self, window_class)

    def revalidate_user(self, *args):
        self.shutdown()
        get_utility(ICookieFile).clear()
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

    app_icon_name = None
    klist_name = 'klist'
    klist_selection_mode = gtk.SELECTION_BROWSE

    def __init__(self, app):
        self.conn = new_transaction()
        BaseAppWindow.__init__(self, app)
        self.user_menu_label = get_current_user(self.conn
                                    ).username.capitalize()
        self._klist = getattr(self, self.klist_name)
        self._klist.set_columns(self.get_columns())
        self._klist.set_selection_mode(self.klist_selection_mode)
        if app.options.debug:
            self._create_debug_menu()
        self._create_user_menu()
        self.setup_focus()

    def _store_cookie(self, *args):
        u = get_current_user(self.conn)
        # XXX: encrypt and ask for password it again
        get_utility(ICookieFile).store(u.username, u.password)
        if hasattr(self, 'user_menu'):
            self._reset_user_menu()

    def _clear_cookie(self, *args):
        get_utility(ICookieFile).clear()
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

    def _read_resource(self, domain, name):
        try:
            license = environ.find_resource(domain, name)
            return file(license)
        except EnvironmentError:
            import gzip
            license = environ.find_resource(domain, name + '.gz')
            return gzip.GzipFile(license)

    def _run_about(self, *args):
        about = gtk.AboutDialog()
        about.set_name(stoq.program_name)
        about.set_version(stoq.version)
        about.set_website(stoq.website)
        release_date = stoq.release_date
        about.set_comments('Release Date: %s' %
                           datetime.datetime(*release_date).strftime('%x'))
        about.set_copyright('Copyright (C) 2005, 2006 Async Open Source')

        # Logo
        icon_file = environ.find_resource('pixmaps', 'stoq_logo.png')
        logo = gtk.gdk.pixbuf_new_from_file(icon_file)
        about.set_logo(logo)

        # License

        fp = self._read_resource('docs', 'COPYING')
        about.set_license(fp.read())

        # Authors & Contributors
        fp = self._read_resource('docs', 'AUTHORS')
        lines = [a.strip() for a in fp.readlines()]
        lines.append('') # separate authors from contributors
        fp = self._read_resource('docs', 'CONTRIBUTORS')
        lines.extend([c.strip() for c in fp.readlines()])
        about.set_authors(lines)

        about.run()
        about.destroy()

    def _create_user_menu(self):
        ui_string = """<ui>
          <menubar name="Menubar">
            <menu action="UserMenu">
              <menuitem action="StoreCookie"/>
              <menuitem action="ClearCookie"/>
              <separator/>
              <menuitem action="ChangeUser"/>
              <menuitem action="ChangeApplication"/>
            </menu>
          </menubar>
        </ui>"""
        actions = [
            ('UserMenu', None, self.user_menu_label),
            ('StoreCookie', gtk.STOCK_SAVE, _('_Store'), '<control>k',
             _('Store a cookie'), self.on_StoreCookie__activate),
            ('ClearCookie',     gtk.STOCK_CLEAR, _('_Clear'), '<control>e',
             _('Clear the cookie'), self.on_ClearCookie__activate),
            ('ChangeUser',    gtk.STOCK_REFRESH, _('C_hange User'), '<control>h',
             _('Change user'), self.on_ChangeUser__activate),
            ('ChangeApplication',    gtk.STOCK_REFRESH, _('Change Application'),
             'F11', _('Change application'), self._on_ChangeApplication__activate),
            ]
        ag = gtk.ActionGroup('UsersMenuActions')
        ag.add_actions(actions)
        self._ui = gtk.UIManager()
        self._ui.insert_action_group(ag, 0)
        self._ui.add_ui_from_string(ui_string)
        window = self.get_toplevel()
        window.add_accel_group(self._ui.get_accel_group())
        menubar = self._ui.get_widget('/Menubar')
        self.menu_hbox.pack_start(menubar, expand=False)
        menubar.show_all()

    def _create_debug_menu(self):
        ui_string = """<ui>
          <menubar name="menubar">
            <menu action="DebugMenu">
              <menuitem action="Introspect"/>
            </menu>
          </menubar>
        </ui>"""
        actions = [
            ('DebugMenu', None, _('Debug')),
            ('Introspect', None, _('Introspect slaves'),
             None, None, self.on_Introspect_activate),
            ]

        ag = gtk.ActionGroup('DebugMenuActions')
        ag.add_actions(actions)
        self.uimanager.insert_action_group(ag, 0)
        self.uimanager.add_ui_from_string(ui_string)

    def print_report(self, report_class, *args, **kwargs):
        print_report(report_class, *args, **kwargs)

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

    def _on_ChangeApplication__activate(self, action):
        toplevel = self.get_toplevel()

        appname = run_dialog(SelectApplicationsDialog(self.app.config.appname),
                             parent=toplevel)
        if appname is None:
            return

        user = get_current_user(self.conn)
        if not user.profile.check_app_permission(appname):
            raise UserProfileError(
                _("This user lacks credentials \nfor application %s")
                % appname)

        toplevel.hide()
        self.app.shutdown()

        module = __import__("stoq.gui.%s.app" % appname, globals(), locals(), [''])
        if not hasattr(module, "main"):
            raise RuntimeError(
                "Application %s must have a app.main() function")
        self.app.config.appname = appname

        module.main(self.app.config)

        gtk.main()

    def on_Introspect_activate(self, action):
        window = self.get_toplevel()
        introspect_slaves(window)

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
        self.searchbar.set_result_strings(*self.searchbar_result_strings)
        self.searchbar.set_searchbar_labels(*self.searchbar_labels)
        self.searchbar.connect('before-search-activate',
                               self.on_searchbar_before_activate)
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
        selected = self.get_filterslave_default_selected_item()
        self.filter_slave = FilterSlave(items, selected)
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

    def set_searchtable(self, search_table):
        self.searchbar_table = search_table
        self.searchbar.set_searchtable(search_table)

    def set_searchbar_columns(self, columns):
        self.searchbar.set_columns(columns)

    def search_items(self):
        self.searchbar.search_items()

    #
    # Hooks
    #

    def get_filterslave_default_selected_item(self):
        return ALL_ITEMS_INDEX

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
