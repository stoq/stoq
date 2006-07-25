# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
##
##
""" Stoq Configuration dialogs"""

import sys
import gettext
from decimal import Decimal

from kiwi.python import Settable
from kiwi.argcheck import argcheck

from stoqlib.exceptions import StoqlibError, DatabaseInconsistency
from stoqlib.lib.message import warning
from stoqlib.lib.runtime import new_transaction, get_connection
from stoqlib.lib.validators import validate_password
from stoqlib.gui.base.wizards import (WizardEditorStep, BaseWizard,
                                      BaseWizardStep)
from stoqlib.database import (DatabaseSettings, finish_transaction,
                              check_installed_database, rollback_and_begin)
from stoqlib.lib.admin import USER_ADMIN_DEFAULT_NAME
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import IUser

from stoq.lib.configparser import StoqConfig, register_config
from stoq.lib.startup import setup, set_branch_by_stationid


_ = gettext.gettext


#
# Wizard Steps
#


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
        from stoqlib.gui.slaves.devices import DeviceSettingsDialogSlave
        slave = DeviceSettingsDialogSlave(self.conn, station=station)
        self.attach_slave("devices_holder", slave)

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def has_next_step(self):
        return False



class BranchStationSettingsStep(WizardEditorStep):
    gladefile = 'BranchStationSettingsStep'

    def __init__(self, conn, wizard, branch_company, previous):
        # This line avoid some problems when importing domain data before
        # setting up the database. That's why we are not using model_type as
        # a class attribute
        from stoqlib.domain.person import BranchStation
        model = BranchStation(connection=conn, name=None,
                              branch=branch_company)
        self.model_type = BranchStation
        WizardEditorStep.__init__(self, conn, wizard, model, previous)

    def _setup_widgets(self):
        from stoqlib.domain.person import PersonAdaptToBranch
        table = PersonAdaptToBranch
        items = [(branch.get_description(), branch)
                    for branch in table.get_active_branches(self.conn)]
        self.branch.prefill(items)
        self.title_label.set_size('large')
        self.title_label.set_bold(True)
        self.branch_company_title.set_size('medium')
        self.branch_company_title.set_bold(True)

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()
        self.name.grab_focus()

    def validate_step(self):
        conn = get_connection()
        name = self.station_proxy.model.name
        if self.model_type.selectBy(name=name, connection=conn).count():
            self.name.set_invalid(_(u"This station name already exists"))
            self.force_validation()
            return False
        return True

    def next_step(self):
        self.model.name = self.station_proxy.model.name
        # Avoid having unused active stations on database if user go back
        # to this step
        self.model.activate()
        self.wizard.install_default(self.model.identifier)

        set_branch_by_stationid(self.wizard.config.get_station_id(),
                                self.conn)
        return DeviceSettingsStep(self.conn, self.wizard, self.model, self)

    def setup_proxies(self):
        self._setup_widgets()
        from stoqlib.lib.parameters import sysparam
        self.id_proxy = self.add_proxy(self.model, ['identifier'])

        model = Settable(name=u"", branch=sysparam(self.conn).MAIN_COMPANY)
        self.station_proxy = self.add_proxy(model, ['name', 'branch'])


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
        # This line avoid some problems when importing domain data before
        # setting up the database
        from stoqlib.domain.person import Person
        from stoqlib.lib.parameters import sysparam
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

        address = company.get_adapted().get_main_address()
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
        model = self.param.MAIN_COMPANY
        self._update_system_parameters(model)
        conn = self.wizard.get_connection()
        return BranchStationSettingsStep(conn, self.wizard, model, self)

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
        from stoqlib.gui.slaves.address import AddressSlave
        address = self.model.get_main_address()
        slave = AddressSlave(self.conn, self.model, address)
        self.attach_slave("address_holder", slave)


class DatabaseSettingsStep(WizardEditorStep):
    gladefile = 'DatabaseSettingsStep'
    model_type = DatabaseSettings
    proxy_widgets = ('address',
                     'port',
                     'username',
                     'password',
                     'dbname')
    stoq_user_proxy = ('stoq_user_passwd',)

    (TRUST_AUTHENTICATION,
     PASSWORD_AUTHENTICATION) = range(2)

    authentication_types = {TRUST_AUTHENTICATION: _("Trust"),
                            PASSWORD_AUTHENTICATION: _("Needs Password")}

    def __init__(self, wizard, model):
        self.wizard_model = model
        self.authentication_items = None
        WizardEditorStep.__init__(self, None, wizard)
        self.title_label.set_size('xx-large')
        self.title_label.set_bold(True)
        self.title_label.set_color('blue')
        self.hint_label.set_size('small')
        self._update_widgets()

    def _update_widgets(self):
        if not self.authentication_items:
            return
        selected = self.authentication_type.get_selected_data()
        need_password = selected == self.PASSWORD_AUTHENTICATION
        self.password.set_sensitive(need_password)
        self.passwd_label.set_sensitive(need_password)

    def _check_admin_password(self):
        table = Person.getAdapterClass(IUser)
        result = table.select(table.q.username == USER_ADMIN_DEFAULT_NAME,
                              connection=get_connection())
        if result.count() > 1:
            raise DatabaseInconsistency("It is not possible have more than "
                                        "one user with the same username: %s"
                                        % USER_ADMIN_DEFAULT_NAME)
        elif result.count() == 1:
            user = result[0]
            password = self.wizard_model.stoq_user_data.password
            if user.password and user.password != password:
                self.stoq_user_passwd.set_invalid(
                    _("There is already a user registered as administrator "
                      "and the password supplied doesn't match it"))
                return False
        return True

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

        password = self.wizard_model.stoq_user_data.password
        callback = lambda msg: self.stoq_user_passwd.set_invalid(msg)
        if not validate_password(password, callback):
            self.force_validation()
            return False

        conn_ok, error_msg = self.model.check_database_connection()
        if not conn_ok:
            warning(_('Invalid database settings'), error_msg)
            return False

        self.wizard.install_default()
        try:
            self.wizard.config.check_connection()
        except:
            type, value, trace = sys.exc_info()
            warning(_('Could not open database config file'),
                    _("Invalid config file settings, got error '%s', "
                      "of type '%s'" % (value, type)))
            return False
        register_config(self.wizard.config)
        if check_installed_database():
            return self._check_admin_password()
        return True

    def next_step(self):
        from stoqlib.lib.parameters import sysparam
        password = self.wizard_model.stoq_user_data.password

        has_installed_db = check_installed_database()
        # Initialize database connections and create system data if the
        # database is empty
        setup(self.wizard.config, stoq_user_password=password)

        existing_conn = self.wizard.get_connection()
        if existing_conn:
            rollback_and_begin(existing_conn)
            conn = existing_conn
        else:
            conn = new_transaction()

        self.wizard.set_connection(conn)
        model = sysparam(conn).MAIN_COMPANY

        if not has_installed_db:
            step_class = BranchSettingsStep
            model = model.get_adapted()
        else:
            step_class = BranchStationSettingsStep
        return step_class(conn, self.wizard, model, self)

    def setup_proxies(self):
        items = [(value, key)
                    for key, value in self.authentication_types.items()]
        self.authentication_type.prefill(items)
        self.authentication_items = items
        self.add_proxy(self.model, DatabaseSettingsStep.proxy_widgets)
        self.wizard_model.stoq_user_data = Settable(password='')
        self.add_proxy(self.wizard_model.stoq_user_data,
                       DatabaseSettingsStep.stoq_user_proxy)

    #
    # Callbacks
    #

    def on_authentication_type__content_changed(self, *args):
        self._update_widgets()


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
        self.model = Settable(db_settings=None, stoq_user_data=None)
        first_step = DatabaseSettingsStep(self, self.model)
        BaseWizard.__init__(self, None, first_step, self.model,
                            title=self.title)

    def set_connection(self, conn):
        self._conn = conn

    def get_connection(self):
        return self._conn

    def install_default(self, station_id=0):
        self.config.install_default(self.model.db_settings, station_id)

    #
    # WizardStep hooks
    #

    def finish(self):
        finish_transaction(self._conn, 1)
        self.retval = self.model
        self.close()

    def cancel(self):
        if self._conn:
            finish_transaction(self._conn)
        if self.config.has_installed_config_data():
            self.config.remove_config_file()
        BaseWizard.cancel(self)
