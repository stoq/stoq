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
        -> DeviceSettingsStep
    If New DB -> AdminPasswordStep
        -> ExampleDatabaseStep
            If DB is empty -> DeviceSettingsStep
            Otherwise      -> BranchSettingsStep
                -> DeviceSettingsStep

"""

import gettext
from decimal import Decimal
import socket

import gtk
from kiwi.argcheck import argcheck
from kiwi.python import Settable
from kiwi.ui.dialogs import info
from stoqlib.exceptions import StoqlibError, DatabaseInconsistency
from stoqlib.database.admin import USER_ADMIN_DEFAULT_NAME, user_has_usesuper
from stoqlib.database.database import rollback_and_begin
from stoqlib.database.runtime import (new_transaction,
                                      set_current_branch_station)
from stoqlib.database.settings import DatabaseSettings
from stoqlib.domain.person import Person
from stoqlib.domain.station import BranchStation
from stoqlib.domain.examples import createall as examples
from stoqlib.domain.interfaces import IUser
from stoqlib.domain.system import SystemTable
from stoqlib.exceptions import DatabaseError
from stoqlib.gui.slaves.userslave import PasswordEditorSlave
from stoqlib.gui.base.wizards import (WizardEditorStep, BaseWizard,
                                      BaseWizardStep)
from stoqlib.lib.message import warning, yesno
from stoqlib.lib.parameters import sysparam

from stoq.lib.configparser import StoqConfig
from stoq.lib.startup import clean_database, setup


_ = gettext.gettext


#
# Wizard Steps
#


class DatabaseSettingsStep(WizardEditorStep):
    gladefile = 'DatabaseSettingsStep'
    model_type = DatabaseSettings
    proxy_widgets = ('address',
                     'port',
                     'username',
                     'password',
                     'dbname')

    (TRUST_AUTHENTICATION,
     PASSWORD_AUTHENTICATION) = range(2)

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
        need_password = selected == self.PASSWORD_AUTHENTICATION
        self.password.set_sensitive(need_password)
        self.passwd_label.set_sensitive(need_password)

    def _create_database(self, db_settings):
        # First, ask the user if he really wants to create the database,
        dbname = db_settings.dbname
        if yesno(_("The specifed database `%s' does not exist.\n"
                   "Do you want to create it?") % dbname,
                 gtk.RESPONSE_NO,
                 _("Don't create"), _("Create")):
            return False

        # Secondly, verify that the user has permission to create the database
        conn = db_settings.get_default_connection()
        if not user_has_usesuper(conn):
            username = db_settings.username
            info(_("User <u>%s</u> has insufficient permissions") % username,
                 _("The specified user `%s' does not have the required "
                   "permissions to install Stoq.\n"
                   "The PostgreSQL user must be a superuser. "
                   "Consult the Stoq documentation for more information on "
                   "how to solve this problem.") % username)
            return False

        # Finally create it, nothing should go wrong at this point
        conn.createDatabase(dbname, ifNotExists=True)
        return True

    def _create_station(self, conn, branch, station_name):
        station = BranchStation.get_station(conn, branch, station_name)
        if not station:
            station = BranchStation.create(conn, branch, station_name)
        return station

    #
    # WizardStep hooks
    #

    def create_model(self, conn):
        db_settings = DatabaseSettings()
        self.wizard_model.db_settings = db_settings
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
        if db_settings.has_database():
            try:
                conn = db_settings.get_connection()
            except DatabaseError, e:
                warning(e.short, e.msg)
                return False

            self.has_installed_db = SystemTable.is_available(conn)
        else:
            if not self._create_database(db_settings):
                return False
            self.has_installed_db = False

        return True

    def next_step(self):
        self.wizard.install_default()

        setup(self.wizard.config, register_station=False, check_schema=False)

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
            conn = existing_conn
        else:
            conn = new_transaction()
        self.wizard.set_connection(conn)

        station_name = socket.gethostname()
        model = sysparam(conn).MAIN_COMPANY
        if not self.wizard.station:
            self.wizard.station = self._create_station(conn, model,
                                                       station_name)
        set_current_branch_station(conn, station_name)

        model = model.person
        if self.has_installed_db:
            return ExistingAdminPasswordStep(conn, self.wizard, self, model)
        else:
            return AdminPasswordStep(conn, self.wizard, self, model)

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
               % self.wizard.station.name)
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
        return DeviceSettingsStep(self.conn, self.wizard,
                                  self._next_model, self)

class ExampleDatabaseStep(WizardEditorStep):
    gladefile = "ExampleDatabaseStep"
    model_type = object

    def next_step(self):
        if self.empty_database_radio.get_active():
            stepclass = BranchSettingsStep
        else:
            self.conn.commit()
            examples.create()
            stepclass = DeviceSettingsStep
        return stepclass(self.conn, self.wizard, self.model, self)

class BranchSettingsStep(WizardEditorStep):
    gladefile = 'BranchSettingsStep'
    person_widgets = ('name',
                      'phone_number',
                      'fax_number')
    tax_widgets = ('icms',
                   'iss',
                   'substitution_icms')
    proxy_widgets = person_widgets + tax_widgets


    def __init__(self, conn, wizard, model, previous):
        self.param = sysparam(conn)
        self.model_type = Person
        WizardEditorStep.__init__(self, conn, wizard, model, previous)
        self._setup_widgets()

    def _setup_widgets(self):
        self.title_label.set_size('large')
        self.title_label.set_bold(True)

    def _update_system_parameters(self, company):
        icms = self.tax_proxy.model.icms
        self.param.update_parameter('ICMS_TAX', unicode(icms))

        iss = self.tax_proxy.model.iss
        self.param.update_parameter('ISS_TAX', unicode(iss))

        substitution = self.tax_proxy.model.substitution_icms
        self.param.update_parameter('SUBSTITUTION_TAX',
                                    unicode(substitution))

        address = company.person.get_main_address()
        if not address:
            raise StoqlibError("You should have an address defined at "
                               "this point")

        city = address.city_location.city
        self.param.update_parameter('CITY_SUGGESTED', city)

        country = address.city_location.country
        self.param.update_parameter('COUNTRY_SUGGESTED', country)

        state = address.city_location.state
        self.param.update_parameter('STATE_SUGGESTED', state)

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()
        self.name.grab_focus()

    def next_step(self):
        branch = self.param.MAIN_COMPANY
        self._update_system_parameters(branch)
        conn = self.wizard.get_connection()
        return DeviceSettingsStep(conn, self.wizard, self.model, self)

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

    def setup_slaves(self):
        from stoqlib.gui.slaves.addressslave import AddressSlave
        address = self.model.get_main_address()
        slave = AddressSlave(self.conn, self.model, address)
        self.attach_slave("address_holder", slave)

class DeviceSettingsStep(BaseWizardStep):
    gladefile = 'DeviceSettingsStep'

    def __init__(self, conn, wizard, station, previous):
        BaseWizardStep.__init__(self, conn, wizard, previous=previous)
        self._setup_widgets()
        self._setup_slaves(station)

    def _setup_widgets(self):
        self.title_label.set_size('large')
        self.title_label.set_bold(True)

    def _setup_slaves(self, station):
        from stoqlib.gui.slaves.devicesslave import DeviceSettingsDialogSlave
        slave = DeviceSettingsDialogSlave(self.conn, station=self.wizard.station)
        self.attach_slave("devices_holder", slave)

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def has_next_step(self):
        return False


#
# Main wizard
#


class FirstTimeConfigWizard(BaseWizard):
    title = _("Setting up Stoq")
    size = (550, 450)

    @argcheck(StoqConfig)
    def __init__(self, config):
        self.config = config
        self._conn = None
        self.station = None
        self.model = Settable(db_settings=None, stoq_user_data=None)
        first_step = DatabaseSettingsStep(self, self.model)
        BaseWizard.__init__(self, None, first_step, self.model,
                            title=self.title)

    def set_connection(self, conn):
        self._conn = conn

    def get_connection(self):
        return self._conn

    def install_default(self):
        self.config.install_default(self.model.db_settings)

    #
    # WizardStep hooks
    #

    def finish(self):
        self._conn.commit(close=True)

        self.retval = self.model
        self.close()

    def cancel(self):
        if self._conn:
            self._conn.close()

        # XXX: Find out when the file was installed and only try to
        #      remove it if it really was.
        try:
            self.config.remove()
        except IOError:
            pass

        BaseWizard.cancel(self)
