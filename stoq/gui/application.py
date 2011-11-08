# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2011 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Base classes for application's GUI """

import datetime
import gettext
import locale

import gtk
from kiwi.component import get_utility
from kiwi.enums import SearchFilterPosition
from kiwi.environ import environ
from kiwi.log import Logger
from stoqlib.database.orm import ORMObjectQueryExecuter
from stoqlib.database.runtime import (new_transaction, get_connection,
                                      get_current_branch)
from stoqlib.lib.interfaces import IAppInfo, IStoqConfig
from stoqlib.lib.message import yesno
from stoqlib.lib.parameters import sysparam, is_developer_mode
from stoqlib.lib.webservice import WebService
from stoqlib.gui.base.application import BaseApp, BaseAppWindow
from stoqlib.gui.base.search import StoqlibSearchSlaveDelegate
from stoqlib.gui.base.infobar import InfoBar
from stoqlib.gui.dialogs.csvexporterdialog import CSVExporterDialog
from stoqlib.gui.help import show_contents, show_section
from stoqlib.gui.printing import print_report
from stoqlib.gui.introspection import introspect_slaves
from stoqlib.domain.inventory import Inventory

import stoq

log = Logger('stoq.application')
_ = gettext.gettext


class App(BaseApp):

    def __init__(self, window_class, config, options, runner):
        self.config = config
        self.options = options
        self.runner = runner
        self.window_class = window_class
        BaseApp.__init__(self, window_class)


class AppWindow(BaseAppWindow):
    """ Base class for the main window of applications.

    @cvar app_name: This attribute is used when generating titles for
                    applications.  It's also useful if we get a list of
                    available applications with the application names
                    translated. This list is going to be used when
                    creating new user profiles.

    """

    app_name = None
    app_icon_name = None
    search = None

    def __init__(self, app):
        self._config = get_utility(IStoqConfig)
        self.conn = new_transaction()
        self.uimanager = gtk.UIManager()
        self.accel_group = self.uimanager.get_accel_group()

        # Create actions, this must be done before the constructor
        # is called, eg when signals are autoconnected
        self.create_actions()
        if app.options.debug:
            self.add_debug_ui()

        BaseAppWindow.__init__(self, app)
        toplevel = self.get_toplevel()
        toplevel.add_accel_group(self.uimanager.get_accel_group())
        self.create_ui()
        self.setup_focus()
        self._check_demo_mode()
        self._check_version()
        self._usability_hacks()

        if not stoq.stable and not is_developer_mode():
            self._display_unstable_version_message()

    def _display_unstable_version_message(self):
        msg = _(
            'You are currently using an <b>unstable version</b> of Stoq that '
            'is under development,\nbe aware that it may behave incorrectly, '
            'crash or even loose your data.\n<b>Do not use in production.</b>')
        self.add_info_bar(gtk.MESSAGE_WARNING, msg)

    def _display_open_inventory_message(self):
        msg = _(u'There is an inventory process open at the moment.\n'
                'While that inventory is open, you will be unable to do '
                'operations that modify your stock.')
        self.inventory_bar = self.add_info_bar(gtk.MESSAGE_WARNING, msg)

    def _usability_hacks(self):
        """Adds some workarounds to improve stoq usability.

        Currently, all it does is change the toolbar style to display both
        icon and label (ubuntu defaults to show only icons)
        """
        if not hasattr(self, 'main_toolbar'):
            return

        self.main_toolbar.set_style(gtk.TOOLBAR_BOTH)

    def _check_demo_mode(self):
        if not sysparam(self.conn).DEMO_MODE:
            return

        if self._config.get('UI', 'hide_demo_warning') == 'True':
            return

        button_label = _('Enable production mode')
        title = _('You are using Stoq in demonstration mode.')
        desc = (_("Some features are limited due to fiscal reasons. "
                  "Click on '%s' to remove the limitations and finish the demonstration.")
                % button_label)
        label = gtk.Label('<b>%s</b>\n%s' % (title, desc))
        label.set_use_markup(True)
        label.set_line_wrap(True)
        label.set_width_chars(100)

        button = gtk.Button(button_label)
        button.connect('clicked', self._on_enable_production__clicked)

        bar = InfoBar()
        bar.get_content_area().add(label)
        bar.add_action_widget(button, 0)
        bar.set_message_type(gtk.MESSAGE_WARNING)
        bar.show_all()

        self.main_vbox.pack_start(bar, False, False, 0)
        self.main_vbox.reorder_child(bar, 1)

    def _check_version(self):
        if not sysparam(self.conn).ONLINE_SERVICES:
            return
        self._version_checker = VersionChecker(self.conn, self)
        self._version_checker.check_new_version()

    def _read_resource(self, domain, name):
        try:
            license = environ.find_resource(domain, name)
            return file(license)
        except EnvironmentError:
            import gzip
            license = environ.find_resource(domain, name + '.gz')
            return gzip.GzipFile(license)

    def _run_about(self, *args):
        info = get_utility(IAppInfo)
        about = gtk.AboutDialog()
        about.set_name(info.get("name"))
        about.set_version(info.get("version"))
        about.set_website(stoq.website)
        release_date = stoq.release_date
        about.set_comments('Release Date: %s' %
                           datetime.datetime(*release_date).strftime('%x'))
        about.set_copyright('Copyright (C) 2005-2011 Async Open Source')

        # Logo
        icon_file = environ.find_resource('pixmaps', 'stoq_logo.svg')
        logo = gtk.gdk.pixbuf_new_from_file(icon_file)
        about.set_logo(logo)

        # License

        if locale.getlocale()[0] == 'pt_BR':
            filename = 'COPYING.pt_BR'
        else:
            filename = 'COPYING'
        fp = self._read_resource('docs', filename)
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

    def _show_uri(self, uri):
        toplevel = self.get_toplevel()
        gtk.show_uri(toplevel.get_screen(), uri, gtk.gdk.CURRENT_TIME)

    def print_report(self, report_class, *args, **kwargs):
        filters = self.search.get_search_filters()
        if filters:
            kwargs['filters'] = filters

        print_report(report_class, *args, **kwargs)

    #
    # Overridables
    #

    def create_actions(self):
        """This is called before the BaseWindow constructor, so we
        can create actions that can be autoconnected."""

    def create_ui(self):
        """This is called when the UI such as GtkWidgets should be
        created"""

    def setup_focus(self):
        """Define this method on child when it's needed."""

    def activate(self):
        """This is called when you switch to an application, can
        be overridden in a subclass"""

    def get_title(self):
        # This method must be redefined in child when it's needed
        return _('Stoq - %s') % self.app_name

    def can_change_application(self):
        """Define if we can change the current application or not.

        @returns: True if we can change the application, False otherwise.
        """
        return True

    def can_close_application(self):
        """Define if we can close the current application or not.

        @returns: True if we can close the application, False otherwise.
        """
        return True

    def set_open_inventory(self):
        """ Subclasses should overide this if they call
        check_open_inventory.

        This method will be called it there is an open inventory, so the
        application can disable some funcionalities
        """
        raise NotImplementedError

    #
    # Public API
    #

    def add_ui_actions(self, ui_string, actions, name='Actions'):
        ag = gtk.ActionGroup(name)
        ag.add_actions(actions)
        self.uimanager.insert_action_group(ag, 0)
        self.uimanager.add_ui_from_string(ui_string)
        for action in ag.list_actions():
            setattr(self, action.get_name(), action)

    def add_help_ui(self, help_label=None, help_section=None):
        ui_string = """<ui>
          <menubar action="menubar">
            <menu action="HelpMenu">
              <menuitem action="HelpContents"/>
              <separator name="HelpSeparator"/>
              <menuitem action="HelpSupport"/>
              <menuitem action="HelpTranslate"/>
              <separator name="HelpSeparator2"/>
              <menuitem action="HelpAbout"/>
            </menu>
          </menubar>
        </ui>"""
        def on_HelpHelp__activate(action):
            show_section(help_section)

        help_actions = [
            ("HelpMenu", None, _("_Help")),
            ("HelpContents", gtk.STOCK_HELP, _("Contents"), '<Shift>F1'),
            ("HelpTranslate", None, _("Translate Stoq..."), None,
             _("Translate this application online")),
            ("HelpSupport", None, _("Get support online..."), None,
             _("Get support for Stoq online")),
            ("HelpAbout", gtk.STOCK_ABOUT),
            ]
        self.add_ui_actions(ui_string, help_actions, 'HelpActions')

        if help_label is not None:
            ui_string = """<ui>
            <menubar action="menubar">
              <menu action="HelpMenu">
                <menuitem action="HelpHelp"/>
              </menu>
            </menubar>
        </ui>"""
            help_help_actions = [
                ("HelpHelp", None, help_label, 'F1',
                 _("Show help for this Application"),
                 on_HelpHelp__activate),
                ]
            self.add_ui_actions(ui_string, help_help_actions, 'HelpHelpActions')

    def add_debug_ui(self):
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

        self.add_ui_actions(ui_string, actions, 'DebugActions')

    def has_open_inventory(self):
        return Inventory.has_open(self.conn, get_current_branch(self.conn))

    def check_open_inventory(self):
        inventory_bar = getattr(self, 'inventory_bar', None)

        if self.has_open_inventory():
            if inventory_bar:
                inventory_bar.show()
            else:
                self._display_open_inventory_message()

            self.set_open_inventory()
        elif inventory_bar:
            inventory_bar.hide()

    def add_info_bar(self, message_type, label, action_widget=None):
        """Show an information bar to the user.
        @param message_type: message type, a gtk.MessageType
        @param label: label to display
        @param action_widget: optional, most likely a button
        @returns: the infobar
        """
        label = gtk.Label(label)
        label.set_use_markup(True)
        label.show()

        bar = InfoBar()
        bar.get_content_area().add(label)
        if action_widget:
            bar.add_action_widget(action_widget, 0)
        bar.set_message_type(message_type)
        bar.show()

        self.main_vbox.pack_start(bar, False, False, 0)
        self.main_vbox.reorder_child(bar, 1)

        return bar

    #
    # BaseAppWindow
    #

    def shutdown_application(self, *args):
        if self.can_close_application():
            if self.search:
                self.search.save_columns()
            self.app.main_window.hide()
        # We must return True here or the window will be hidden.
        return False

    #
    # Callbacks
    #

    def on_Quit__activate(self, action):
        self.shutdown_application()

    # Help

    def on_HelpContents__activate(self, action):
        show_contents()

    def on_HelpTranslate__activate(self, action):
        self._show_uri("https://translations.launchpad.net/stoq")

    def on_HelpSupport__activate(self, action):
        self._show_uri("http://www.stoq.com.br/support")

    def on_HelpAbout__activate(self, action):
        self._run_about()

    # Debug

    def on_Introspect_activate(self, action):
        window = self.get_toplevel()
        introspect_slaves(window)

    def _on_enable_production__clicked(self, button):
        if not self.can_close_application():
            return
        if yesno(_("This will enable production mode and finish the demonstration. "
                   "Are you sure?"),
                 gtk.RESPONSE_NO,
                 _("Continue testing"),
                 _("Enable production mode")):
            return

        from stoq.main import restart_stoq_atexit
        restart_stoq_atexit()
        self._config.set('Database', 'enable_production', 'True')
        self._config.flush()
        self.shutdown_application()


class SearchableAppWindow(AppWindow):
    """
    Base class for applications which main interface consists of a list

    @cvar search_table: The we will query on to perform the search
    @cvar search_label: Label left of the search entry
    """

    search_table = None
    search_label = _('Search:')

    def __init__(self, app):
        if self.search_table is None:
            raise TypeError("%r must define a search_table attribute" % self)

        self.executer = ORMObjectQueryExecuter(get_connection())
        self.executer.set_table(self.search_table)

        self.search = StoqlibSearchSlaveDelegate(self.get_columns(),
                                     restore_name=self.__class__.__name__)
        self.search.enable_advanced_search()
        self.search.set_query_executer(self.executer)
        self.results = self.search.search.results
        self.set_text_field_label(self.search_label)

        AppWindow.__init__(self, app)

        self.attach_slave('search_holder', self.search)

        self.create_filters()

        self.search.focus_search_entry()

    #
    # Public API
    #

    def set_searchtable(self, search_table):
        """
        @param search_table:
        """
        self.executer.set_table(search_table)
        self.search_table = search_table

    def add_filter(self, search_filter, position=SearchFilterPosition.BOTTOM,
                   columns=None, callback=None):
        """
        See L{SearchSlaveDelegate.add_filter}
        """
        self.search.add_filter(search_filter, position, columns, callback)

    def set_text_field_columns(self, columns):
        """
        See L{SearchSlaveDelegate.set_text_field_columns}
        """
        self.search.set_text_field_columns(columns)

    def set_text_field_label(self, label):
        """
        @param label:
        """
        search_filter = self.search.get_primary_filter()
        search_filter.set_label(label)

    def disable_search_entry(self):
        self.search.disable_search_entry()

    def refresh(self):
        """
        See L{kiwi.ui.search.SearchSlaveDelegate.refresh}
        """
        self.search.refresh()

    def clear(self):
        """
        See L{kiwi.ui.search.SearchSlaveDelegate.clear}
        """
        self.search.clear()

    def export_csv(self):
        """Runs a dialog to export the current search results to a CSV file.
        """
        self.run_dialog(CSVExporterDialog, self, self.search_table,
                        self.results)

    #
    # Hooks
    #

    def create_filters(self):
        pass
    #
    # Callbacks
    #

    def on_ExportCSV__activate(self, action):
        self.export_csv()


class VersionChecker(object):
    DAYS_BETWEEN_CHECKS = 7

    #
    #   Private API
    #

    def __init__(self, conn, app):
        self.conn = conn
        self.app = app

    def _display_new_version_message(self, latest_version):
        # Only display version message in admin app
        if 'AdminApp' not in self.app.__class__.__name__:
            return
        button = gtk.LinkButton(
            'http://www.stoq.com.br/pt-br/more/whatsnew',
            _(u'Learn More...'))
        msg = _('<b>There is a new Stoq version available (%s)</b>') % (
            latest_version, )
        self.app.add_info_bar(gtk.MESSAGE_INFO, msg, action_widget=button)

    def _check_details(self, latest_version):
        current_version = tuple(stoq.version.split('.'))
        if tuple(latest_version.split('.')) > current_version:
            self._display_new_version_message(latest_version)
        else:
            log.debug('Using latest version %r, not showing message' % (
                stoq.version, ))

    def _download_details(self):
        log.debug('Downloading new version information')
        api = WebService()
        response = api.version(self.conn, stoq.version)
        response.addCallback(self._on_response_done)

    def _on_response_done(self, details):
        self._check_details(details['version'])
        config = get_utility(IStoqConfig)
        config.set('General', 'last-version-check',
                   datetime.date.today().strftime('%Y-%m-%d'))
        config.set('General', 'latest-version', details['version'])
        config.flush()

    #
    #   Public API
    #

    def check_new_version(self):
        if is_developer_mode():
            return
        log.debug('Checking version')
        config = get_utility(IStoqConfig)
        date = config.get('General', 'last-version-check')
        if date:
            check_date = datetime.datetime.strptime(date, '%Y-%m-%d')
            diff = datetime.date.today() - check_date.date()
            if diff.days >= self.DAYS_BETWEEN_CHECKS:
                return self._download_details()
        else:
            return self._download_details()

        latest_version = config.get('General', 'latest-version')
        if latest_version:
            self._check_details(latest_version)
