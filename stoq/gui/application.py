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

import gobject
import gtk
from kiwi.enums import SearchFilterPosition
from kiwi.environ import environ
from kiwi.log import Logger
from kiwi.ui.delegates import GladeDelegate
from stoqlib.api import api
from stoqlib.database.orm import ORMObjectQueryExecuter
from stoqlib.lib.message import yesno
from stoqlib.lib.webservice import WebService
from stoqlib.gui.base.dialogs import (get_dialog, run_dialog,
                                      add_current_toplevel)
from stoqlib.gui.base.infobar import InfoBar
from stoqlib.gui.base.search import StoqlibSearchSlaveDelegate
from stoqlib.gui.dialogs.csvexporterdialog import CSVExporterDialog
from stoqlib.gui.help import show_section
from stoqlib.gui.printing import print_report
from stoqlib.gui.introspection import introspect_slaves
from stoqlib.domain.inventory import Inventory
from twisted.internet import reactor

import stoq

log = Logger('stoq.application')
_ = gettext.gettext


class ToolMenuAction(gtk.Action):
    pass
gobject.type_register(ToolMenuAction)
ToolMenuAction.set_tool_item_type(
    gobject.type_from_name('GtkMenuToolButton').pytype)


class App(object):
    """Class for application control. """

    def __init__(self, window_class, config, options, runner, embedded,
                 launcher, name):
        """
        Create a new object App.
        @param main_window_class: A eAppWindow subclass
        """
        if not issubclass(window_class, AppWindow):
            raise TypeError
        self.config = config
        self.options = options
        self.runner = runner
        self.window_class = window_class
        self.embedded = embedded
        self.launcher = launcher
        self.name = name

        # The self should be passed to main_window to let it access
        # shutdown and do_sync methods.
        self.main_window = window_class(self)

    def show(self):
        if self.embedded:
            win = self.main_window.get_toplevel()
            self.launcher.show_app(self.main_window, win.child)
            win.hide()
        else:
            self.main_window.show()

    def run(self):
        self.show()

    def hide(self):
        self.main_window.hide()

    def shutdown(self, *args):
        if reactor.running:
            reactor.stop()


class AppWindow(GladeDelegate):
    """ Class for the main window of applications.

    @cvar app_name: This attribute is used when generating titles for
                    applications.  It's also useful if we get a list of
                    available applications with the application names
                    translated. This list is going to be used when
                    creating new user profiles.

    """

    app_name = None
    app_icon_name = None
    search = None
    gladefile = toplevel_name = ''
    title = ''
    size = ()

    def __init__(self, app, keyactions=None):
        self._sensitive_group = dict()
        self.app = app
        self.conn = api.new_transaction()
        self.uimanager = self._create_ui_manager()
        self.accel_group = self.uimanager.get_accel_group()

        self._create_ui_manager_ui()
        GladeDelegate.__init__(self, delete_handler=self._on_delete_handler,
                               keyactions=keyactions,
                               gladefile=self.gladefile,
                               toplevel_name=self.toplevel_name)
        self._configure_toplevel()
        self.create_ui()

        self._ui_bootstrap()

    def _create_ui_manager(self):
        if self.app.embedded:
            uimanager = self.app.launcher.uimanager
        else:
            uimanager = gtk.UIManager()
        return uimanager

    def _create_ui_manager_ui(self):
        # Create actions, this must be done before the constructor
        # is called, eg when signals are autoconnected
        self.create_actions()
        if self.app.options.debug:
            self.add_debug_ui()

    def _configure_toplevel(self):
        toplevel = self.get_toplevel()
        add_current_toplevel(toplevel)
        if self.size:
            toplevel.set_size_request(*self.size)
        toplevel.set_title(self.get_title())

        if not self.app.embedded:
            toplevel.add_accel_group(self.uimanager.get_accel_group())

    def _ui_bootstrap(self):
        if self.app.name != 'launcher':
            return

        self._check_demo_mode()
        self._check_version()
        self._usability_hacks()

        if not stoq.stable and not api.is_developer_mode():
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

        self.main_toolbar.set_style(gtk.TOOLBAR_BOTH_HORIZ)

    def _check_demo_mode(self):
        if not api.sysparam(self.conn).DEMO_MODE:
            return

        if api.config.get('UI', 'hide_demo_warning') == 'True':
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
        self.main_vbox.reorder_child(bar, 2)

    def _check_version(self):
        if not api.sysparam(self.conn).ONLINE_SERVICES:
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

    #
    # Overridables
    #

    def create_actions(self):
        """This is called before the BaseWindow constructor, so we
        can create actions that can be autoconnected.
        The widgets and actions loaded from builder files are not set
        yet"""

    def create_ui(self):
        """This is called when the UI such as GtkWidgets should be
        created. Glade widgets are now created and can be accessed
        in the instance.
        """

    def activate(self):
        """This is when you switch to an application.
        You should setup widget sensitivity here and refresh lists etc"""

    def setup_focus(self):
        """Define this method on child when it's needed.
        This is for calling grab_focus(), it's called after the window
        is shown. focus chains should be created in create_ui()"""

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

    def new_activate(self):
        """Called when the New toolbar item is activated"""
        raise NotImplementedError

    def search_activate(self):
        """Called when the Search toolbar item is activated"""
        raise NotImplementedError

    #
    # Public API
    #

    def print_report(self, report_class, *args, **kwargs):
        filters = self.search.get_search_filters()
        if filters:
            kwargs['filters'] = filters

        print_report(report_class, *args, **kwargs)

    def toggle_fullscreen(self):
        window = self.get_toplevel()
        if window.window.get_state() & gtk.gdk.WINDOW_STATE_FULLSCREEN:
            window.unfullscreen()
        else:
            window.fullscreen()

    def set_sensitive(self, widgets, value):
        """Set the C{widgets} sensitivity based on C{value}

        @note: if a sensitive group was registered for any widget,
            it's validation function will be tested and, if C{False}
            is returned, it will be set insensitive, ignoring C{value}

        @param widgets: a L{list} of widgets
        @param value: either C{True} or C{False}
        """
        # FIXME: Maybe this should ne done on kiwi?
        for widget in widgets:
            sensitive = value

            for validator in self._sensitive_group.get(widget, []):
                if not validator[0](*validator[1]):
                    sensitive = False
                    break

            widget.set_sensitive(sensitive)

    def register_sensitive_group(self, widgets, validation_func, *args):
        """Register widgets on a sensitive group.

        Everytime self.set_sensitive() is called, if there is any
        validation function for a given widget on sensitive group,
        then that will be used to decide if it gets sensitive or
        insensitive.

        @param widgets: a L{list} of widgets
        @param validation_func: a function for validation. It should
            return either C{True} or C{False}.
        @param args: args that will be passed to C{validation_func}
        """
        assert callable(validation_func)

        for widget in widgets:
            validators = self._sensitive_group.setdefault(widget, set())
            validators.add((validation_func, args))

    def get_dialog(self, dialog_class, *args, **kwargs):
        """ Encapsuled method for getting dialogs. """
        return get_dialog(self, dialog_class, *args, **kwargs)

    def run_dialog(self, dialog_class, *args, **kwargs):
        """ Encapsuled method for running dialogs. """
        return run_dialog(dialog_class, self, *args, **kwargs)

    def add_ui_actions(self, ui_string, actions, name='Actions',
                       action_type='normal', filename=None):
        ag = gtk.ActionGroup(name)
        if action_type == 'normal':
            ag.add_actions(actions)
        elif action_type == 'toogle':
            ag.add_toggle_actions(actions)
        else:
            raise ValueError(action_type)
        self.uimanager.insert_action_group(ag, 0)
        if filename is not None:
            filename = environ.find_resource('uixml', filename)
            ui_id = self.uimanager.add_ui_from_file(filename)
        else:
            ui_id = self.uimanager.add_ui_from_string(ui_string)
        for action in ag.list_actions():
            setattr(self, action.get_name(), action)
        return ui_id

    def add_tool_menu_actions(self, actions):
        group = gtk.ActionGroup(name="ToolMenuGroup")
        self.uimanager.insert_action_group(group, 0)
        for name, label, tooltip, stock_id in actions:
            action = ToolMenuAction(name=name,
                                    label=label,
                                    tooltip=tooltip,
                                    stock_id=stock_id)
            group.add_action(action)
            setattr(self, action.get_name(), action)

    def set_help_section(self, label, section):
        def on_HelpHelp__activate(action):
            show_section(section)

        ui_string = """<ui>
        <menubar action="menubar">
          <menu action="HelpMenu">
            <placeholder name="HelpPH">
              <menuitem action="HelpHelp"/>
            </placeholder>
          </menu>
        </menubar>
        </ui>"""
        help_help_actions = [
            ("HelpHelp", None, label, 'F1',
             _("Show help for this application"),
             on_HelpHelp__activate),
            ]
        self.help_ui = self.add_ui_actions(
            ui_string,
            help_help_actions, 'HelpHelpActions')

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
        return Inventory.has_open(self.conn,api.get_current_branch(self.conn))

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
        self.main_vbox.reorder_child(bar, 2)

        return bar

    #
    # AppWindow
    #


    def shutdown_application(self, *args):
        if not self.can_close_application():
            return False

        if self.search:
            self.search.save_columns()
        return True

    #
    # Callbacks
    #

    def key_control_F11(self):
        self.toggle_fullscreen()

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
        api.config.set('Database', 'enable_production', 'True')
        api.config.flush()
        self.shutdown_application()
        raise SystemExit

    def _on_delete_handler(self, *args):
        self.shutdown_application()

    def _on_quit_action__clicked(self, *args):
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

        self.executer = ORMObjectQueryExecuter(api.get_connection())
        self.executer.set_table(self.search_table)

        self.search = StoqlibSearchSlaveDelegate(self.get_columns(),
                                     restore_name=self.__class__.__name__)
        self.search.enable_advanced_search()
        self.search.set_query_executer(self.executer)
        self.search.search.connect("search-completed",
                                   self._on_search__search_completed)
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

    def search_completed(self, results, states):
        pass

    #
    # Callbacks
    #

    def _on_search__search_completed(self, search, results, states):
        self.search_completed(results, states)

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
        api.config.set('General', 'last-version-check',
                       datetime.date.today().strftime('%Y-%m-%d'))
        api.config.set('General', 'latest-version', details['version'])
        api.config.flush()

    #
    #   Public API
    #

    def check_new_version(self):
        if api.is_developer_mode():
            return
        log.debug('Checking version')
        date = api.config.get('General', 'last-version-check')
        if date:
            check_date = datetime.datetime.strptime(date, '%Y-%m-%d')
            diff = datetime.date.today() - check_date.date()
            if diff.days >= self.DAYS_BETWEEN_CHECKS:
                return self._download_details()
        else:
            return self._download_details()

        latest_version = api.config.get('General', 'latest-version')
        if latest_version:
            self._check_details(latest_version)
