# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006, 2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              João Victor Duarte Martins  <jvdm@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
##
"""First time installation wizard for Stoq

Stoq Configuration dialogs

Current flow of the database steps:

-> DatabaseSettingsStep
    If Existing DB -> ExistingAdminPasswordStep
        -> ECFPluginStep
    If New DB -> AdminPasswordStep
        -> ExampleDatabaseStep
            If DB is empty -> ECFPluginStep
            Otherwise      -> BranchSettingsStep
                -> ECFPluginStep
-> FinishInstallationStep

"""

import gettext
from decimal import Decimal
import os
import socket

import gtk
from kiwi.component import provide_utility
from kiwi.datatypes import ValidationError
from kiwi.python import Settable
from kiwi.ui.dialogs import info
from stoqlib.exceptions import StoqlibError, DatabaseInconsistency
from stoqlib.database.admin import (USER_ADMIN_DEFAULT_NAME, user_has_usesuper,
                                    create_main_branch)
from stoqlib.database.interfaces import ICurrentBranch, ICurrentBranchStation
from stoqlib.database.runtime import (new_transaction, rollback_and_begin,
                                      get_current_branch)
from stoqlib.database.settings import DatabaseSettings
from stoqlib.domain.person import Person
from stoqlib.domain.station import BranchStation
from stoqlib.domain.interfaces import IBranch, IUser, ICompany
from stoqlib.domain.system import SystemTable
from stoqlib.exceptions import DatabaseError
from stoqlib.gui.slaves.userslave import PasswordEditorSlave
from stoqlib.gui.base.wizards import (WizardEditorStep, BaseWizard,
                                      BaseWizardStep)
from stoqlib.importers.stoqlibexamples import create as create_examples
from stoqlib.lib.message import warning, yesno, error
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.pluginmanager import provide_plugin_manager
from stoqlib.lib.validators import validate_cnpj

from stoq.lib.configparser import StoqConfig
from stoq.lib.startup import clean_database, setup


_ = gettext.gettext


#
# Wizard Steps
#

(TRUST_AUTHENTICATION,
 PASSWORD_AUTHENTICATION) = range(2)


class DatabaseSettingsStep(WizardEditorStep):
    gladefile = 'DatabaseSettingsStep'
    model_type = DatabaseSettings
    proxy_widgets = ('address',
                     'port',
                     'username',
                     'password',
                     'dbname')

    authentication_types = {TRUST_AUTHENTICATION: _("Trust"),
                            PASSWORD_AUTHENTICATION: _("Needs Password")}

    def __init__(self, wizard, model):
        self.wizard_model = model
        self.authentication_items = None
        self.has_installed_db = False
        self.admin_password = None
        WizardEditorStep.__init__(self, None, wizard)
        self.title_label.set_size('xx-large')
        self.title_label.set_bold(True)
        self.title_label.set_color('blue')
        self._update_widgets()

    def _update_widgets(self):
        if not self.authentication_items:
            return
        selected = self.authentication_type.get_selected_data()
        need_password = selected == PASSWORD_AUTHENTICATION
        self.password.set_sensitive(need_password)
        self.passwd_label.set_sensitive(need_password)

    def _create_database(self, db_settings):
        # First check the version
        conn = db_settings.get_default_connection()
        version = conn.dbVersion()
        if version < (8, 1):
            info(_("Stoq requires PostgresSQL 8.1 or later, but %s found") %
                 ".".join(map(str, version)))
            conn.close()
            return False

        # Secondly, ask the user if he really wants to create the database,
        dbname = db_settings.dbname
        if yesno(_("The specifed database `%s' does not exist.\n"
                   "Do you want to create it?") % dbname,
                 gtk.RESPONSE_NO,
                 _("Don't create"), _("Create")):
            return False

        # Thirdly, verify that the user has permission to create the database
        if not user_has_usesuper(conn):
            username = db_settings.username
            info(_("User <u>%s</u> has insufficient permissions") % username,
                 _("The specified user `%s' does not have the required "
                   "permissions to install Stoq.\n"
                   "The PostgreSQL user must be a superuser. "
                   "Consult the Stoq documentation for more information on "
                   "how to solve this problem.") % username)
            conn.close()
            return False

        # Finally create it, nothing should go wrong at this point
        conn.createDatabase(dbname, ifNotExists=True)
        conn.close()
        return True

    #
    # WizardStep hooks
    #

    def create_model(self, conn):
        self.wizard_model.db_settings = db_settings = DatabaseSettings()
        return db_settings

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def validate_step(self):
        if not self.model.check_database_address():
            msg = _("The database address '%s' is invalid. Please fix the "
                    "address you have set and try again"
                    % self.model.address)
            warning(_(u'Invalid database address'), msg)
            self.address.set_invalid(_("Invalid database address"))
            self.force_validation()
            return False

        db_settings = self.wizard_model.db_settings
        try:
            if db_settings.has_database():
                conn = db_settings.get_connection()
                self.has_installed_db = SystemTable.is_available(conn)
                conn.close()
            else:
                if not self._create_database(db_settings):
                    return False
                self.has_installed_db = False

        except DatabaseError, e:
            warning(e.short, e.msg)
            return False

        return True

    def _setup_pgpass(self):
        # There's no way to pass in the password to psql, so we need
        # to setup a ~/.pgpass where we store the password entered here
        pgpass = os.environ.get('PGPASSFILE', os.path.join(
            os.environ['HOME'], '.pgpass'))

        if os.path.exists(pgpass):
            lines = []
            for line in open(pgpass):
                if line[-1] == '\n':
                    line = line[:-1]
                lines.append(line)
        else:
            lines = []

        line = '%s:%s:%s:%s:%s' % (self.model.address, self.model.port,
                                   self.model.dbname,
                                   self.model.username, self.model.password)
        if line in lines:
            return

        lines.append(line)
        open(pgpass, 'w').write('\n'.join(lines))
        os.chmod(pgpass, 0600)

    def next_step(self):
        # At this point all the data is validated and it's guaranteed that
        # we can create a connection to postgres.

        # Save password if using password authentication
        if self.authentication_type.get_selected() == PASSWORD_AUTHENTICATION:
            self._setup_pgpass()
        self.wizard.config.load_settings(self.wizard_model.db_settings)

        setup(self.wizard.config, self.wizard.options,
              register_station=False, check_schema=False,
              load_plugins=False)

        if not self.has_installed_db:
            # Initialize database connections and create system data if the
            # database is empty
            if self.admin_password:
                self.wizard.config.store_password(self.admin_password)

            # To prevent the eventloop from starving
            while gtk.events_pending():
                gtk.main_iteration()
            clean_database(self.wizard.config)

        existing_conn = self.wizard.get_connection()
        if existing_conn:
            rollback_and_begin(existing_conn)
            existing_conn.close()
            conn = existing_conn
        else:
            conn = new_transaction()
        self.wizard.set_connection(conn)

        dummy = object()
        if self.has_installed_db:
            # So we already have a installed db. At this point we should set our branch.
            branches = Person.iselect(IBranch, connection=conn)
            if not branches:
                error(_("Schema error, no branches found"))

            # use first branch until we support multiple branches.
            self.wizard.branch = branches[0]
            provide_utility(ICurrentBranch, self.wizard.branch)

            return ExistingAdminPasswordStep(conn, self.wizard, self, dummy)
        else:
            return AdminPasswordStep(conn, self.wizard, self, dummy)

    def setup_proxies(self):
        items = [(value, key)
                    for key, value in self.authentication_types.items()]
        self.authentication_type.prefill(items)
        self.authentication_items = items
        self.add_proxy(self.model, DatabaseSettingsStep.proxy_widgets)
        self.wizard_model.stoq_user_data = Settable(password='')
        self.add_proxy(self.wizard_model.stoq_user_data)

    #
    # Callbacks
    #

    def on_authentication_type__content_changed(self, *args):
        self._update_widgets()


class AdminPasswordStep(BaseWizardStep):
    """ Ask a password for the new user being created. """
    gladefile = 'AdminPasswordStep'

    def __init__(self, conn, wizard, previous, next_model):
        self._next_model = next_model
        BaseWizardStep.__init__(self, conn, wizard, previous)
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
        return PasswordEditorSlave(self.conn)

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
        good_pass =  self.password_slave.validate_confirm()
        if good_pass:
            adminuser = Person.iselectOneBy(IUser,
                                            username=USER_ADMIN_DEFAULT_NAME,
                                            connection=self.conn)
            if adminuser is None:
                raise DatabaseInconsistency(
                    ("You should have a user with username: %s"
                     % USER_ADMIN_DEFAULT_NAME))
            adminuser.password = self.password_slave.model.new_password
        return good_pass

    def next_step(self):
        return ExampleDatabaseStep(
            self.conn, self.wizard, self._next_model, self)


class ExistingAdminPasswordStep(AdminPasswordStep):
    def _check_password(self, conn, password):
        # We can't use PersonAdaptToUser.select here because it requires
        # us to have an IDatabaseSettings utility provided.
        results = conn.queryOne(
            "SELECT password FROM person_adapt_to_user WHERE username=%s" % (
            conn.sqlrepr(USER_ADMIN_DEFAULT_NAME),))
        if not results:
            return True
        if len(results) > 1:
            raise DatabaseInconsistency(
                "It is not possible have more than one user with "
                "the same username: %s" % USER_ADMIN_DEFAULT_NAME)
        elif len(results) == 1:
            user_password = results[0]
            if user_password and user_password != password:
                return False
        return True

    def _setup_widgets(self):
        msg = (_(u"This machine which has the name <b>%s</b> will be "
                 "registered so it can be used to access the system.")
               % socket.gethostname())
        label = gtk.Label()
        label.set_use_markup(True)
        label.set_markup(msg)
        label.set_alignment(0.0, 0.0)
        label.set_line_wrap(True)
        self.slave_box.pack_start(label, False, False, 10)
        label.show()

    #
    # Hooks
    #

    def setup_slaves(self):
        AdminPasswordStep.setup_slaves(self)
        self._setup_widgets()

    def get_description_label(self):
        db_settings = self.wizard.model.db_settings
        return (_("There is already a database called <b>%s</b> on <b>%s</b>. "
                  "You must enter the password for the user <b>%s</b> to "
                  "continue the installation: ")
                % (db_settings.dbname, db_settings.address,
                   USER_ADMIN_DEFAULT_NAME))

    def get_title_label(self):
        return _("<b>Administrator Account</b>")

    def get_slave(self):
        return PasswordEditorSlave(self.conn, confirm_password=False)

    def validate_step(self):
        if not self.password_slave.validate_confirm():
            return False
        slave = self.password_slave
        if self._check_password(self.conn, slave.model.new_password):
            return True
        slave.invalidate_password(_("The password supplied is "
                                    "not valid."))
        return False

    def next_step(self):
        return ECFPluginStep(self.conn, self.wizard, self._next_model)



class ExampleDatabaseStep(WizardEditorStep):
    gladefile = "ExampleDatabaseStep"
    model_type = object

    def next_step(self):
        self.conn.commit()
        if self.empty_database_radio.get_active():
            return BranchSettingsStep(self.conn, self.wizard,
                                      None, self)
        else:
            create_examples(utilities=True)
            self.wizard.installed_examples = True
            branch = get_current_branch(self.conn)
            return ECFPluginStep(self.conn, self.wizard,
                                 branch.person)


class BranchSettingsStep(WizardEditorStep):
    gladefile = 'BranchSettingsStep'
    person_widgets = ('name',
                      'phone_number',
                      'fax_number')
    tax_widgets = ('icms',
                   'iss',
                   'substitution_icms')
    company_widgets = ('cnpj',
                       'state_registry')
    proxy_widgets = person_widgets + tax_widgets + company_widgets
    model_type = Person

    def __init__(self, conn, wizard, model, previous):
        model = create_main_branch(name="", trans=conn).person

        self.param = sysparam(conn)
        WizardEditorStep.__init__(self, conn, wizard, model, previous)
        self._setup_widgets()

    def _setup_widgets(self):
        self.title_label.set_size('large')
        self.title_label.set_bold(True)

    def _update_system_parameters(self, person):
        icms = self.tax_proxy.model.icms
        self.param.update_parameter('ICMS_TAX', unicode(icms))

        iss = self.tax_proxy.model.iss
        self.param.update_parameter('ISS_TAX', unicode(iss))

        substitution = self.tax_proxy.model.substitution_icms
        self.param.update_parameter('SUBSTITUTION_TAX',
                                    unicode(substitution))

        address = person.get_main_address()
        if not address:
            raise StoqlibError("You should have an address defined at "
                               "this point")

        city = address.city_location.city
        self.param.update_parameter('CITY_SUGGESTED', city)

        country = address.city_location.country
        self.param.update_parameter('COUNTRY_SUGGESTED', country)

        state = address.city_location.state
        self.param.update_parameter('STATE_SUGGESTED', state)

        # Update the fancy name
        self.company_proxy.model.fancy_name = self.person_proxy.model.name

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()
        self.name.grab_focus()

    def next_step(self):
        self._update_system_parameters(self.model)
        self.wizard.branch = IBranch(self.model)
        conn = self.wizard.get_connection()
        return ECFPluginStep(conn, self.wizard, self.model)

    def setup_proxies(self):
        widgets = BranchSettingsStep.person_widgets
        self.person_proxy = self.add_proxy(self.model, widgets)

        widgets = BranchSettingsStep.tax_widgets
        iss = Decimal(self.param.ISS_TAX)
        icms = Decimal(self.param.ICMS_TAX)
        substitution = Decimal(self.param.SUBSTITUTION_TAX)
        model = Settable(iss=iss, icms=icms,
                         substitution_icms=substitution)
        self.tax_proxy = self.add_proxy(model, widgets)

        widgets = BranchSettingsStep.company_widgets
        model = ICompany(self.model, None)
        if not model is None:
            self.company_proxy = self.add_proxy(model, widgets)

    def setup_slaves(self):
        from stoqlib.gui.editors.addresseditor import AddressSlave
        address = self.model.get_main_address()
        slave = AddressSlave(self.conn, self.model, address)
        self.attach_slave("address_holder", slave)

    #
    # Kiwi Callbacks
    #

    def on_icms__validate(self, entry, value):
        if value > 100:
            return ValidationError(_("ICMS can not be greater than 100"))
        if value < 0:
            return ValidationError(_("ICMS can not be less than 0"))

    def on_iss__validate(self, entry, value):
        if value > 100:
            return ValidationError(_("ISS can not be greater than 100"))
        if value < 0:
            return ValidationError(_("ISS can not be less than 0"))

    def on_substitution_icms__validate(self, entry, value):
        if value > 100:
            return ValidationError(_("ICMS Substitution can not be greater "
                                     "than 100"))
        if value < 0:
            return ValidationError(_("ICMS Substitution can not be "
                                     "less than 0"))

    def on_cnpj__validate(self, widget, value):
        if not validate_cnpj(value):
            return ValidationError(_(u'The CNPJ is not valid.'))


class ECFPluginStep(BaseWizardStep):
    gladefile = 'ECFPluginStep'

    def next_step(self):
        return FinishInstallationStep(self.conn, self.wizard, self)

    def post_init(self):
        self.wizard.enable_ecf = True

    def on_yes__toggled(self, radio):
        self.wizard.enable_ecf = radio.get_active()


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
        self.wizard.finish()
        # Use False instead of None, so we can distinguish quit from cancel
        self.wizard.retval = False


#
# Main wizard
#


class FirstTimeConfigWizard(BaseWizard):
    title = _("Setting up Stoq")
    size = (550, 450)

    def __init__(self, options):
        self.config = StoqConfig()
        self.options = options
        self._conn = None
        self.branch = None
        self.installed_examples = False
        self.device_slave = None
        self.enable_ecf = False
        self.model = Settable(db_settings=None, stoq_user_data=None)
        first_step = DatabaseSettingsStep(self, self.model)
        BaseWizard.__init__(self, None, first_step, self.model,
                            title=self.title)
        # Disable back until #2771 is solved
        self.previous_button.hide()

    def set_connection(self, conn):
        self._conn = conn

    def get_connection(self):
        return self._conn

    def _create_station(self, conn, branch, station_name):
        station = BranchStation.get_station(conn, branch, station_name)
        if not station:
            station = BranchStation.create(conn, branch, station_name)
        return station

    #
    # WizardStep hooks
    #

    def finish(self):
        # Commit data created during the wizard, such as stations
        self._conn.commit()

        if self.branch:
            station_name = socket.gethostname()
            station = self._create_station(self._conn, self.branch,
                                           station_name)
            provide_utility(ICurrentBranchStation, station)
            self._conn.commit()

        # We need to provide the plugin manager at some point since
        # we're skipping it above

        manager = provide_plugin_manager()
        if self.enable_ecf:
            manager.enable_plugin('ecf')

        # Okay, all plugins enabled go on and activate them
        manager.activate_plugins()

        self._conn.close()

        # Write configuration to disk
        self.config.flush()

        self.retval = self.model
        self.close()

    def cancel(self):
        if self._conn:
            self._conn.close()

        BaseWizard.cancel(self)
