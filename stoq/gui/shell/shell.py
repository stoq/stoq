# -*- coding: utf-8 *-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2013 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

""" Stoq shell routines"""

import logging
import os
import sys

# FIXME: We can import whatever we want here, but don't import anything
#        significant, it's good to maintain lazy loaded things during startup
from stoqlib.exceptions import StoqlibError
from stoqlib.lib.translation import stoqlib_gettext as _
from twisted.internet.defer import inlineCallbacks, succeed

log = logging.getLogger(__name__)
_shell = None
PRIVACY_STRING = _(
    "One of the new features of Stoq 1.0 is support for online "
    "services. Features using the online services include automatic "
    "bug report and update notifications. More services are under development."
    "To be able to provide a better service and properly identify the user "
    "we will collect the CNPJ of the primary branch and the ip address.\n\n"
    "<b>We will not disclose the collected information and we are committed "
    "to keeping your privacy intact.</b>")


class ShellDatabaseConnection(object):
    """Sets up a database connection

      - Connects to a database
      - Telling why if it failed
      - Runs database wizard if needed
      - Runs schema migration
      - Activates plugins
      - Sets up main branch
    """

    def __init__(self, options):
        self._options = options
        self._config = None
        self._ran_wizard = False

    def connect(self):
        self._load_configuration()
        self._maybe_run_first_time_wizard()
        self._try_connect()
        self._post_connect()

    def _load_configuration(self):
        from stoqlib.lib.configparser import StoqConfig
        log.debug('reading configuration')
        self._config = StoqConfig()
        if self._options.filename:
            self._config.load(self._options.filename)
        else:
            self._config.load_default()

    def _maybe_run_first_time_wizard(self):
        from stoqlib.gui.base.dialogs import run_dialog
        from stoq.gui.config import FirstTimeConfigWizard

        config_file = self._config.get_filename()
        if self._options.wizard or not os.path.exists(config_file):
            run_dialog(FirstTimeConfigWizard, None, self._options)
            self._ran_wizard = True

        if self._config.get('Database', 'enable_production') == 'True':
            run_dialog(FirstTimeConfigWizard, None, self._options, self._config)
            self._ran_wizard = True

    def _try_connect(self):
        from stoqlib.lib.message import error
        try:
            store_dsn = self._config.get_settings().get_store_dsn()
        except:
            type, value, trace = sys.exc_info()
            error(_("Could not open the database config file"),
                  _("Invalid config file settings, got error '%s', "
                    "of type '%s'") % (value, type))

        from stoqlib.database.exceptions import PostgreSQLError
        from stoq.lib.startup import setup

        # XXX: progress dialog for connecting (if it takes more than
        # 2 seconds) or creating the database
        log.debug('calling setup()')
        try:
            setup(self._config, self._options, register_station=False,
                  check_schema=False, load_plugins=False)
        except (StoqlibError, PostgreSQLError) as e:
            error(_('Could not connect to the database'),
                  'error=%s uri=%s' % (str(e), store_dsn))

    def _post_connect(self):
        self._check_schema_migration()
        self._check_branch()
        self._activate_plugins()

    def _check_schema_migration(self):
        from stoqlib.lib.message import error
        from stoqlib.database.migration import needs_schema_update
        from stoqlib.exceptions import DatabaseInconsistency
        if needs_schema_update():
            self._run_update_wizard()

        from stoqlib.database.migration import StoqlibSchemaMigration
        migration = StoqlibSchemaMigration()
        try:
            migration.check()
        except DatabaseInconsistency as e:
            error(_('The database version differs from your installed '
                    'version.'), str(e))

    def _activate_plugins(self):
        from stoqlib.lib.pluginmanager import get_plugin_manager
        manager = get_plugin_manager()
        manager.activate_installed_plugins()

    def _check_branch(self):
        from stoqlib.database.runtime import (get_default_store, new_store,
                                              get_current_station,
                                              set_current_branch_station)
        from stoqlib.domain.person import Company
        from stoqlib.lib.parameters import sysparam
        from stoqlib.lib.message import info

        default_store = get_default_store()
        set_current_branch_station(default_store, station_name=None)

        compaines = default_store.find(Company)
        if (compaines.count() == 0 or
            not sysparam(default_store).MAIN_COMPANY):
            from stoqlib.gui.base.dialogs import run_dialog
            from stoqlib.gui.dialogs.branchdialog import BranchDialog
            if self._ran_wizard:
                info(_("You need to register a company before start using Stoq"))
            else:
                info(_("Could not find a company. You'll need to register one "
                       "before start using Stoq"))
            store = new_store()
            person = run_dialog(BranchDialog, None, store)
            if not person:
                raise SystemExit
            branch = person.branch
            sysparam(store).MAIN_COMPANY = branch.id
            get_current_station(store).branch = branch
            store.commit()
            store.close()

    def _run_update_wizard(self):
        from stoqlib.gui.base.dialogs import run_dialog
        from stoq.gui.update import SchemaUpdateWizard
        retval = run_dialog(SchemaUpdateWizard, None)
        if not retval:
            raise SystemExit()


class Shell(object):
    """The main application shell
    - bootstraps via ShellBootstrap
    - connects to the database via ShellDatabaseConnection
    - handles login
    - runs applications
    """
    def __init__(self, bootstrap, options, initial=True):
        global _shell
        _shell = self
        self._appname = None
        self._bootstrap = bootstrap
        self._dbconn = ShellDatabaseConnection(options=options)
        self._blocked_apps = []
        self._hidden_apps = []
        self._login = None
        self._options = options
        self._user = None
        self.windows = []

    #
    # Private
    #

    def _do_login(self):
        from stoqlib.exceptions import LoginError
        from stoqlib.gui.utils.login import LoginHelper
        from stoqlib.lib.message import error

        self._login = LoginHelper(username=self._options.login_username)
        try:
            if not self.login():
                return False
        except LoginError as e:
            error(str(e))
            return False
        self._check_param_online_services()
        self._maybe_show_welcome_dialog()
        return True

    def _check_param_online_services(self):
        from stoqlib.database.runtime import get_default_store, new_store
        from stoqlib.lib.parameters import sysparam
        import gtk

        sparam = sysparam(get_default_store())
        if sparam.ONLINE_SERVICES is None:
            from kiwi.ui.dialogs import HIGAlertDialog
            # FIXME: All of this is to avoid having to set markup as the default
            #        in kiwi/ui/dialogs:HIGAlertDialog.set_details, after 1.0
            #        this can be simplified when we fix so that all descriptions
            #        sent to these dialogs are properly escaped
            dialog = HIGAlertDialog(
                parent=None,
                flags=gtk.DIALOG_MODAL,
                type=gtk.MESSAGE_WARNING)
            dialog.add_button(_("Not right now"), gtk.RESPONSE_NO)
            dialog.add_button(_("Enable online services"), gtk.RESPONSE_YES)

            dialog.set_primary(_('Do you want to enable Stoq online services?'))
            dialog.set_details(PRIVACY_STRING, use_markup=True)
            dialog.set_default_response(gtk.RESPONSE_YES)
            response = dialog.run()
            dialog.destroy()
            store = new_store()
            sysparam(store).ONLINE_SERVICES = int(bool(response == gtk.RESPONSE_YES))
            store.commit()
            store.close()

    def _maybe_show_welcome_dialog(self):
        from stoqlib.api import api
        if not api.user_settings.get('show-welcome-dialog', True):
            return
        api.user_settings.set('show-welcome-dialog', False)

        from stoq.gui.welcomedialog import WelcomeDialog
        from stoqlib.gui.base.dialogs import run_dialog
        run_dialog(WelcomeDialog)

    def _maybe_correct_demo_position(self, shell_window):
        # Possibly correct window position (livecd workaround for small
        # screens)
        from stoqlib.database.runtime import get_default_store
        from stoqlib.lib.parameters import sysparam
        from stoqlib.lib.pluginmanager import get_plugin_manager
        manager = get_plugin_manager()
        if (sysparam(get_default_store()).DEMO_MODE and
            manager.is_active(u'ecf')):
            pos = shell_window.toplevel.get_position()
            if pos[0] < 220:
                shell_window.toplevel.move(220, pos[1])

    def _logout(self):
        from stoqlib.database.runtime import (get_current_user,
                                              get_default_store)
        log.debug('Logging out the current user')
        try:
            user = get_current_user(get_default_store())
            if user:
                user.logout()
        except StoqlibError:
            pass

    @inlineCallbacks
    def _terminate(self, restart=False):
        log.info("Terminating Stoq")

        # This removes all temporary files created when calling
        # get_resource_filename() that extract files to the file system
        import pkg_resources
        pkg_resources.cleanup_resources()

        log.debug('Stopping deamon')
        from stoqlib.lib.daemonutils import stop_daemon
        stop_daemon()

        # Finally, go out of the reactor and show possible crash reports
        yield self._quit_reactor_and_maybe_show_crashreports()

        if restart:
            from stoqlib.lib.process import Process
            log.info('Restarting Stoq')
            Process([sys.argv[0], '--no-splash-screen'])

        # os._exit() forces a quit without running atexit handlers
        # and does not block on any running threads
        # FIXME: This is the wrong solution, we should figure out why there
        #        are any running threads/processes at this point
        log.debug("Terminating by calling os._exit()")
        os._exit(0)

        raise AssertionError("Should never happen")

    def _show_crash_reports(self):
        from stoqlib.lib.crashreport import has_tracebacks
        if not has_tracebacks():
            return succeed(None)
        if 'STOQ_DISABLE_CRASHREPORT' in os.environ:
            return succeed(None)
        from stoqlib.gui.dialogs.crashreportdialog import show_dialog
        return show_dialog()

    @inlineCallbacks
    def _quit_reactor_and_maybe_show_crashreports(self):
        log.debug("Show some crash reports")
        yield self._show_crash_reports()
        log.debug("Shutdown reactor")
        from twisted.internet import reactor
        reactor.stop()

    #
    # Public API
    #

    def login(self):
        """
        Do a login
        @param try_cookie: Try to use a cookie if one is available
        @returns: True if login succeed, otherwise false
        """
        from stoqlib.exceptions import LoginError
        from stoqlib.lib.message import info
        user = self._login.cookie_login()

        if not user:
            try:
                user = self._login.validate_user()
            except LoginError as e:
                info(str(e))

        if user:
            self._user = user
        return bool(user)

    def get_current_app_name(self):
        """
        Get the name of the currently running application
        @returns: the name
        @rtype: str
        """
        if not self.windows:
            return ''
        return self.window[0].current_app.app_name

    def create_window(self):
        """
        Creates a new shell window.

        Note that it will not contain any applications and it will be hidden.

        :returns: the shell_window
        """
        from stoq.gui.shell.shellwindow import ShellWindow
        from stoqlib.database.runtime import get_default_store
        shell_window = ShellWindow(self._options,
                                   shell=self,
                                   store=get_default_store())
        self.windows.append(shell_window)

        self._maybe_correct_demo_position(shell_window)

        return shell_window

    def close_window(self, shell_window):
        """
        Close a currently open window
        :param ShellWindow shell_window: the shell_window
        """
        shell_window.close()
        self.windows.remove(shell_window)

    def main(self, appname):
        """
        Start the shell.
        This will:
        - connect to the database
        - login the current user
        - create a new window
        - run the launcher/application selector app
        - run a mainloop

        This will only exit when the complete stoq application
        is shutdown.

        :param appname: name of the application to run
        """
        self._dbconn.connect()
        if not self._do_login():
            raise SystemExit
        if appname is None:
            appname = u'launcher'
        shell_window = self.create_window()
        shell_window.run_application(unicode(appname))
        shell_window.show()

        log.debug("Entering reactor")
        self._bootstrap.entered_main = True
        from twisted.internet import reactor
        reactor.run()
        log.info("Leaving reactor")

    def quit(self, restart=False):
        """
        Quit the shell and exit the application.
        This will save user settings and then forcefully terminate
        the application
        """
        from stoqlib.api import api
        self._logout()

        # Write user settings to disk, this obviously only happens when
        # termination the complete stoq application
        log.debug("Flushing user settings")
        api.user_settings.flush()

        self._terminate(restart=restart)


def get_shell():
    return _shell
