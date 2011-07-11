# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2011 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
"""First time installation wizard for Stoq

Stoq Configuration dialogs

Current flow of the database steps:

-> DatabaseSettingsStep
    If Existing DB -> ExistingAdminPasswordStep
        -> PluginStep
    If New DB -> AdminPasswordStep
        -> ExampleDatabaseStep
        -> PluginStep
        -> DatabasePage
-> FinishInstallationStep

"""

import gettext
import os
import socket

import gtk
from kiwi.component import provide_utility
from kiwi.environ import environ
from kiwi.python import Settable
from kiwi.ui.dialogs import info
from kiwi.ui.delegates import GladeSlaveDelegate
from kiwi.ui.wizard import WizardStep
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.database.admin import USER_ADMIN_DEFAULT_NAME, ensure_admin_user
from stoqlib.database.database import test_local_database
from stoqlib.database.interfaces import (ICurrentBranchStation,
                                         ICurrentBranch)
from stoqlib.database.runtime import new_transaction
from stoqlib.database.settings import DatabaseSettings
from stoqlib.domain.person import Person
from stoqlib.domain.station import BranchStation
from stoqlib.domain.interfaces import IUser
from stoqlib.domain.system import SystemTable
from stoqlib.exceptions import DatabaseError
from stoqlib.gui.base.wizards import BaseWizard, WizardEditorStep
from stoqlib.gui.slaves.userslave import PasswordEditorSlave
from stoqlib.gui.processview import ProcessView
from stoqlib.lib.message import warning, yesno
from stoqlib.lib.parameters import sysparam

from stoq.lib.configparser import StoqConfig
from stoq.lib.options import get_option_parser
from stoq.lib.startup import setup, set_default_profile_settings
from stoq.main import run_app

_ = gettext.gettext


#
# Wizard Steps
#

(TRUST_AUTHENTICATION,
 PASSWORD_AUTHENTICATION) = range(2)

class BaseWizardStep(WizardStep, GladeSlaveDelegate):
    """A wizard step base class definition"""
    gladefile = None

    def __init__(self, wizard, previous=None):
        self.wizard = wizard
        WizardStep.__init__(self, previous)
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)


class DatabaseLocationStep(WizardEditorStep):
    gladefile = 'DatabaseLocationStep'
    model_type = DatabaseSettings

    def __init__(self, wizard):
        self.wizard = wizard
        WizardEditorStep.__init__(self, None, wizard, wizard.settings)

    def next_step(self):
        self.wizard.db_is_local = self.radio_local.get_active()

        settings = self.wizard.settings
        if self.wizard.db_is_local:
            settings.address = "" # Unix socket really
            self.wizard.config.load_settings(self.wizard.settings)

        if (test_local_database() and
            self.wizard.try_connect(settings) and
            self.wizard.has_installed_db):
            return FinishInstallationStep(self.wizard)
        elif self.wizard.db_is_local:
            return ExampleDatabaseStep(self.wizard, self)
        else:
            return DatabaseSettingsStep(self.wizard, self)


class DatabaseSettingsStep(WizardEditorStep):
    gladefile = 'DatabaseSettingsStep'
    model_type = DatabaseSettings
    proxy_widgets = ('address',
                     'port',
                     'username',
                     'password',
                     'dbname')

    def __init__(self, wizard, previous):
        WizardEditorStep.__init__(self, None, wizard, wizard.settings,
                                  previous)
        self._update_widgets()

    def _update_widgets(self):
        logo = environ.find_resource('pixmaps', 'stoq_logo.svg')
        self.image1.set_from_file(logo)
        self.title_label.set_size('xx-large')
        self.title_label.set_bold(True)
        self.title_label.set_color('blue')
        selected = self.authentication_type.get_selected_data()
        need_password = selected == PASSWORD_AUTHENTICATION
        self.password.set_sensitive(need_password)
        self.passwd_label.set_sensitive(need_password)

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def validate_step(self):
        if not self.model.check_database_address():
            msg = _("The database address '%s' is invalid. "
                    "Please fix it and try again"
                    % self.model.address)
            warning(_(u'Invalid database address'), msg)
            # '' is not strictly invalid, since it's an alias for
            # unix socket, so don't tell that to the user, make him
            # belive that he still uses "localhost"
            if self.model.address != "":
                self.address.set_invalid(_("Invalid database address"))
                self.force_validation()
            return False

        settings = self.wizard.settings

        # If we configured setting to localhost, try connecting
        # with address == '', eg unix socket first before trying
        # to connect to localhost. This is done because the default
        # postgres configuration doesn't allow you to connect via localhost,
        # only unix socket.
        if settings.address == 'localhost':
            if not self.wizard._try_connect(settings, warn=False):
                settings.address = ''

        if not self.wizard.try_connect(settings):
            # Restore it
            settings.address = 'localhost'
            return False

        if settings.address == '':
            # Reload settings as they changed
            self.wizard.config.load_settings(settings)

        self.wizard.auth_type = self.authentication_type.get_selected()

        return True

    def setup_proxies(self):
        self.authentication_type.prefill([
            (_("Needs Password"), PASSWORD_AUTHENTICATION),
            (_("Trust"), TRUST_AUTHENTICATION)])

        self.add_proxy(self.model, DatabaseSettingsStep.proxy_widgets)
        # Show localhost instead of empty for unix socket, not strictly
        # correct but better than showing nothing.
        if not self.model.address:
            self.address.set_text("localhost")
        self.model.stoq_user_data = Settable(password='')
        self.add_proxy(self.model.stoq_user_data)

    def next_step(self):
        if self.wizard.has_installed_db:
            return FinishInstallationStep(self.wizard)
        else:
            return ExampleDatabaseStep(self.wizard, self)

    #
    # Callbacks
    #

    def on_authentication_type__content_changed(self, *args):
        self._update_widgets()


class ExampleDatabaseStep(BaseWizardStep):
    gladefile = "ExampleDatabaseStep"
    model_type = object

    def next_step(self):
        self.wizard.enable_production = not self.empty_database_radio.get_active()
        return PluginStep(self.wizard, self)


class PluginStep(BaseWizardStep):
    gladefile = 'PluginStep'

    def post_init(self):
        self.wizard.plugins = []

    def next_step(self):
        if self.enable_ecf.get_active():
            self.wizard.plugins.append('ecf')
        if self.enable_nfe.get_active():
            self.wizard.plugins.append('nfe')

        return AdminPasswordStep(self.wizard, self)


class AdminPasswordStep(BaseWizardStep):
    """ Ask a password for the new user being created. """
    gladefile = 'AdminPasswordStep'

    def __init__(self, wizard, previous):
        BaseWizardStep.__init__(self, wizard, previous)
        self.description_label.set_markup(
            self.get_description_label())
        self.title_label.set_markup(self.get_title_label())
        self.setup_slaves()

    def get_title_label(self):
        return _("<b>Administrator Account Creation</b>")

    def get_description_label(self):
        return _("I'm adding a user called `%s' which will "
                 "have administrator privilegies.\n\nTo be "
                 "able to create other users you need to login "
                 "with this user in the admin application and "
                 "create them.") % USER_ADMIN_DEFAULT_NAME

    def get_slave(self):
        return PasswordEditorSlave(None)

    #
    # WizardStep hooks
    #

    def setup_slaves(self):
        self.password_slave = self.get_slave()
        self.attach_slave("password_holder", self.password_slave)

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()
        self.password_slave.password.grab_focus()

    def validate_step(self):
        good_pass = self.password_slave.validate_confirm()
        if good_pass:
            self.wizard.options.login_username = 'admin'
            self.wizard.login_password = self.password_slave.model.new_password
        return good_pass

    def next_step(self):
        return CreateDatabaseStep(self.wizard, self)


class CreateDatabaseStep(BaseWizardStep):
    gladefile = 'CreateDatabaseStep'

    def post_init(self):
        self.n_patches = 0
        self.process_view = ProcessView()
        self.process_view.listen_stderr = True
        self.process_view.connect('read-line', self._on_processview__readline)
        self.process_view.connect('finished', self._on_processview__finished)
        self.expander.add(self.process_view)
        self._maybe_create_database()

    def next_step(self):
        return FinishInstallationStep(self.wizard)

    def _maybe_create_database(self):
        if self.wizard.db_is_local:
            self._local_installation()
            return
        elif self.wizard.remove_demo:
            self._launch_stoqdbadmin()
            return

        # Save password if using password authentication
        if self.wizard.auth_type == PASSWORD_AUTHENTICATION:
            self._setup_pgpass()
        settings = self.wizard.settings
        self.wizard.config.load_settings(settings)

        conn = settings.get_default_connection()
        version = conn.dbVersion()
        if version < (8, 1):
            info(_("Stoq requires PostgresSQL 8.1 or later, but %s found") %
                 ".".join(map(str, version)))
            conn.close()
            return False

        # Secondly, ask the user if he really wants to create the database,
        dbname = settings.dbname
        if not yesno(_("The specifed database '%s' does not exist.\n"
                       "Do you want to create it?") % dbname,
                     gtk.RESPONSE_NO, _("Don't create"), _("Create database")):
            self.process_view.feed("** Creating database\r\n")
            self._launch_stoqdbadmin()
        else:
            self.process_view.feed("** Not creating database\r\n")

    def _setup_pgpass(self):
        # There's no way to pass in the password to psql, so we need
        # to setup a ~/.pgpass where we store the password entered here
        directory = os.environ.get('HOME', os.environ.get('APPDATA'))
        passfile = os.path.join(directory, '.pgpass')
        pgpass = os.environ.get('PGPASSFILE', passfile)

        if os.path.exists(pgpass):
            lines = []
            for line in open(pgpass):
                if line[-1] == '\n':
                    line = line[:-1]
                lines.append(line)
        else:
            lines = []

        settings = self.wizard.settings
        line = '%s:%s:%s:%s:%s' % (settings.address, settings.port,
                                   settings.dbname,
                                   settings.username, settings.password)
        if line in lines:
            return

        lines.append(line)
        open(pgpass, 'w').write('\n'.join(lines))
        os.chmod(pgpass, 0600)

    def _local_installation(self):
        if not test_local_database():
            self._install_postgres()
            return

        self._launch_stoqdbadmin()

    def _install_postgres(self):
        try:
            import aptdaemon
        except ImportError:
            warning(_("You need to install and start PostgreSQL."
                      "When done click 'OK' to continue"))
            self._local_installation()
            return

        from stoqlib.gui.aptpackageinstaller import AptPackageInstaller
        def done(api, error):
            if error is None:
                self._launch_stoqdbadmin()
            else:
                warning(_("Something went wrong while trying to install PostgreSQL"))

        self.label.set_label(
            _("Installing PostgreSQL database server."))
        api = AptPackageInstaller(parent=self.wizard.get_toplevel())
        api.install('postgresql')
        api.connect('done', done)

    def _launch_stoqdbadmin(self):
        self.wizard.disable_back()
        self.wizard.disable_next()
        args = ['stoqdbadmin', 'init',
                '--no-load-config',
                '--no-register-station',
                '-v']
        if self.wizard.enable_production and not self.wizard.remove_demo:
            args.append('--demo')
        if self.wizard.plugins:
            args.append('--enable-plugins')
            args.append(','.join(self.wizard.plugins))
        if self.wizard.db_is_local:
            args.append('--create-database')
            # FIXME: Allow developers to specify another database
            #        is_developer_mode() or STOQ_DATABASE_NAME
            args.append('stoq')
            args.append('--database-username')
            args.append(os.environ['USER'])

        dbargs = self.wizard.settings.get_command_line_arguments()
        args.extend(dbargs)
        self.label.set_label(
            _("Creating a new database for Stoq, depending on the speed of "
              "your computer and the server it may take a couple of "
              "minutes to finish."))
        self.progressbar.set_text(_("Creating database..."))
        self.progressbar.set_fraction(0.05)
        self.process_view.execute_command(args)

    def _parse_process_line(self, line):
        LOG_CATEGORY = 'stoqlib.database.create'
        log_pos = line.find(LOG_CATEGORY)
        if log_pos == -1:
            return
        line = line[log_pos+len(LOG_CATEGORY)+1:]
        if line == 'SCHEMA':
            value = 0.1
            text = _("Creating base schema...")
        elif line.startswith('PATCHES:'):
            value = 0.35
            self.n_patches = int(line.split(':', 1)[1])
            text = _("Creating schema, applying patches...")
        elif line.startswith('PATCH:'):
            # 0.4 - 0.7 patches
            patch = float(line.split(':', 1)[1])
            value = 0.4 + (patch / self.n_patches) * 0.3
            text = _("Creating schema, applying patch %d ...") % (patch+1, )
        elif line == 'INIT START':
            text = _("Creating additional database objects ...")
            value = 0.8
        elif line == 'INIT DONE' and self.wizard.enable_production:
            text = _("Creating examples ...")
            value = 0.85
        elif line.startswith('PLUGIN'):
            text = _("Activating plugins ...")
            if 'nfe' in self.wizard.plugins:
                text += ' ' + _('This may take some time.')
            value = 0.95
        else:
            return
        self.progressbar.set_fraction(value)
        self.progressbar.set_text(text)

    def _finish(self, returncode):
        if returncode:
            self.wizard.enable_back()
            # Failed to execute/create database
            if returncode == 30:
                # This probably happened because the user either;
                # - pressed cancel in the authentication popup
                # - user erred the password 3 times
                # Allow him to try again
                if yesno(_("Something went wrong while trying to create "
                           "the database. Try again?"),
                         gtk.RESPONSE_NO, _("Change settings"), _("Try again")):
                    return
                self._launch_stoqdbadmin()
                return
            else:
                # Unknown error, just inform user that something went wrong.
                self.expander.set_expanded(True)
                warning(_("Something went wrong while trying to create "
                          "the Stoq database"))
            return
        self.wizard.load_config_and_call_setup()
        set_default_profile_settings()
        ensure_admin_user(self.wizard.config.get_password())
        self.progressbar.set_text(_("Done, click 'Forward' to continue"))
        self.progressbar.set_fraction(1.0)
        self.wizard.enable_next()

    # Callbacks

    def _on_processview__readline(self, view, line):
        self._parse_process_line(line)

    def _on_processview__finished(self, view, returncode):
        self._finish(returncode)


class FinishInstallationStep(BaseWizardStep):
    gladefile = 'FinishInstallationStep'

    def has_next_step(self):
        return False

    def post_init(self):
        # replaces the cancel button with a quit button
        self.wizard.cancel_button.set_label(gtk.STOCK_QUIT)
        # self._cancel will be a callback for the quit button
        self.wizard.cancel = self._cancel
        self.wizard.next_button.set_label(_(u'Run Stoq'))

    def _cancel(self):
        # This is the last step, so we will finish the installation
        # before we quit
        self.wizard.finish(run=False)


#
# Main wizard
#


class FirstTimeConfigWizard(BaseWizard):
    title = _("Setting up Stoq")
    size = (550, 450)

    def __init__(self, options, config=None):
        if not config:
            config = StoqConfig()
        self.settings = config.get_settings()

        self.enable_production = False
        self.config = config
        self.remove_demo = False
        self.has_installed_db = False
        self.options = options
        self.plugins = []
        self.db_is_local = False

        if config.get('Database', 'enable_production') == 'True':
            self.remove_demo = True

        if self.remove_demo:
            first_step = PluginStep(self)
        else:
            first_step = DatabaseLocationStep(self)
        BaseWizard.__init__(self, None, first_step, title=self.title)

        self.get_toplevel().set_deletable(False)

    def _create_station(self, trans):
        if self.enable_production:
            branch = sysparam(trans).MAIN_COMPANY
            assert branch
            provide_utility(ICurrentBranch, branch)
        else:
            branch = None
        station = BranchStation(connection=trans,
                                is_active=True,
                                branch=branch,
                                name=socket.gethostname())
        provide_utility(ICurrentBranchStation, station)

    def _set_admin_password(self, trans):
        adminuser = Person.iselectOneBy(IUser,
                                        username=USER_ADMIN_DEFAULT_NAME,
                                        connection=trans)
        if adminuser is None:
            raise DatabaseInconsistency(
                ("You should have a user with username: %s"
                 % USER_ADMIN_DEFAULT_NAME))
        adminuser.password = self.login_password

    def try_connect(self, settings, warn=True):
        try:
            if settings.has_database():
                conn = settings.get_connection()
                self.has_installed_db = SystemTable.is_available(conn)
                conn.close()
        except DatabaseError, e:
            if warn:
                warning(e.short, e.msg)
            return False

        return True


    def load_config_and_call_setup(self):
        dbargs = self.settings.get_command_line_arguments()
        parser = get_option_parser()
        db_options, unused_args = parser.parse_args(dbargs)
        self.config.set_from_options(db_options)
        setup(self.config,
              options=self.options,
              check_schema=True,
              register_station=False,
              load_plugins=True)

    #
    # WizardStep hooks
    #

    def finish(self, run=True):
        if self.has_installed_db:
            self.load_config_and_call_setup()
        else:
            # Commit data created during the wizard, such as stations
            trans = new_transaction()
            self._set_admin_password(trans)
            self._create_station(trans)
            trans.commit()

        # Write configuration to disk
        if self.remove_demo:
            self.config.remove('Database', 'enable_production')
        self.config.flush()

        self.close()
        if run:
            run_app(self.options, 'admin')
