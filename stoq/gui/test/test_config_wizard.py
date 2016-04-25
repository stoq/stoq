# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012-2013 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import os
import tempfile

import gtk
import mock
from stoqlib.database.settings import DatabaseSettings
from stoqlib.gui.test.uitestutils import GUITest

from stoq.gui.config import (DatabaseSettingsStep,
                             FirstTimeConfigWizard)


class MockDatabaseSettings(DatabaseSettings):
    def has_database(self):
        return False


class TestFirstTimeConfigWizard(GUITest):

    def setUp(self):
        GUITest.setUp(self)
        self.settings = None

    def create_wizard(self):
        options = mock.Mock()
        options.sqldebug = False
        options.verbose = False

        if self.settings is None:
            self.settings = MockDatabaseSettings(address=u'localhost',
                                                 port=12345,
                                                 dbname=u'dbname',
                                                 username=u'username',
                                                 password=u'password')

        self.config = self.fake.StoqConfig(self.settings)
        wizard = FirstTimeConfigWizard(options, self.config)
        return wizard

    @mock.patch('stoq.gui.config.needs_schema_update')
    @mock.patch('stoq.gui.config.test_local_database')
    @mock.patch('stoq.gui.config.ProcessView.execute_command')
    @mock.patch('stoq.gui.config.create_default_profile_settings')
    @mock.patch('stoq.gui.config.yesno')
    @mock.patch('stoq.gui.config.warning')
    @mock.patch('stoq.gui.config.get_hostname')
    @mock.patch('stoq.gui.config.check_extensions')
    def test_local(self,
                   check_extensions,
                   get_hostname,
                   warning,
                   yesno,
                   create_default_profile_settings,
                   execute_command,
                   test_local_database,
                   needs_schema_update):
        needs_schema_update.return_value = False

        DatabaseSettingsStep.model_type = self.fake.DatabaseSettings
        self.settings = self.fake.DatabaseSettings(self.store)

        get_hostname.return_value = u'foo_hostname'
        test_local_database.return_value = (u'/var/run/postgres', 5432)

        wizard = self.create_wizard()

        self.check_wizard(wizard, u'wizard-config-welcome')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertTrue(step.radio_local.get_active())
        self.check_wizard(wizard, u'wizard-config-database-location')
        self.click(wizard.next_button)

        # Warning should not have being called by now.
        self.assertEquals(warning.call_count, 0, warning.call_args_list)

        self.check_wizard(wizard, u'wizard-config-installation-mode')
        self.click(wizard.next_button)

        self.check_wizard(wizard, u'wizard-config-plugins')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        step.password_slave.password.update(u'foobar')
        step.password_slave.confirm_password.update(u'foobar')
        self.check_wizard(wizard, u'wizard-config-admin-password')
        self.click(wizard.next_button)

        self.check_wizard(wizard, u'wizard-config-installing')
        execute_command.assert_called_once_with([
            u'stoq', u'dbadmin', u'init',
            u'--no-load-config', u'--no-register-station', u'-v',
            u'--enable-plugins', u'ecf',
            u'--create-dbuser',
            u'-d', u'stoq',
            u'-p', u'12345',
            u'-u', u'username',
            u'-w', u'password'])
        step = wizard.get_current_step()
        self.assertEquals(step.progressbar.get_text(),
                          u'Creating database...')

        step.process_view.emit(u'read-line', u'stoqlib.database.create SCHEMA')
        self.assertEquals(step.progressbar.get_text(),
                          u'Creating base schema...')

        step.process_view.emit(u'read-line', u'stoqlib.database.create PATCHES:1')
        self.assertEquals(step.progressbar.get_text(),
                          u'Creating schema, applying patches...')

        step.process_view.emit(u'read-line', u'stoqlib.database.create PATCH:0')
        self.assertEquals(step.progressbar.get_text(),
                          u'Creating schema, applying patch 1 ...')

        step.process_view.emit(u'read-line', u'stoqlib.database.create INIT START')
        self.assertEquals(step.progressbar.get_text(),
                          u'Creating additional database objects ...')

        step.process_view.emit(u'read-line', u'stoqlib.database.create PLUGIN')
        self.assertEquals(step.progressbar.get_text(),
                          u'Activating plugins ...')

        yesno.return_value = False
        step.process_view.emit(u'finished', 30)
        yesno.assert_called_once_with(
            u'Something went wrong while trying to create the database. Try again?',
            gtk.RESPONSE_NO, u'Change settings', u'Try again')

        step.process_view.emit(u'finished', 999)
        warning.assert_called_once_with(
            u"Something went wrong while trying to create the Stoq database")

        step.process_view.emit(u'finished', 0)
        create_default_profile_settings.assert_called_once_with()
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        step.name.update(u'Name')
        step.email.update(u'example@example.com')
        step.phone.update(u'1212341234')
        wizard.link_request_done = True
        self.check_wizard(wizard, u'wizard-config-link')
        self.click(wizard.next_button)

        self.check_wizard(wizard, u'wizard-config-done')

        # FIXME: Find out why this is False when running the tests on a
        # clean database and True otherwhise.
        wizard.has_installed_db = True
        self.click(wizard.next_button)
        self.assertTrue(self.config.flushed)

    @mock.patch('stoq.gui.config.needs_schema_update')
    @mock.patch('stoq.gui.config.ProcessView.execute_command')
    @mock.patch('stoq.gui.config.create_default_profile_settings')
    @mock.patch('stoq.gui.config.yesno')
    @mock.patch('stoq.gui.config.warning')
    @mock.patch('stoq.gui.config.get_hostname')
    @mock.patch('stoq.gui.config.get_database_version')
    @mock.patch('stoq.gui.config.check_extensions')
    def test_remote(self,
                    check_extensions,
                    get_database_version,
                    get_hostname,
                    warning,
                    yesno,
                    create_default_profile_settings,
                    execute_command,
                    needs_schema_update):
        needs_schema_update.return_value = False

        DatabaseSettingsStep.model_type = self.fake.DatabaseSettings
        self.settings = self.fake.DatabaseSettings(self.store)
        get_hostname.return_value = u'foo_hostname'
        get_database_version.return_value = (9, 1)
        wizard = self.create_wizard()

        # Welcome
        self.click(wizard.next_button)

        # DatabaseLocationStep
        step = wizard.get_current_step()
        step.radio_network.set_active(True)
        self.click(wizard.next_button)

        # DatabaseSettingsStep, invalid
        step = wizard.get_current_step()
        step.address.update(u'remotehost')
        step.port.update(12345)
        step.username.update(u'username')
        step.dbname.update(u'dbname')

        # DatabaseSettingsStep, valid
        self.settings.check = True
        self.click(wizard.next_button)

        # Installation mode
        self.click(wizard.next_button)

        # Plugins
        self.click(wizard.next_button)

        # AdminPassword
        step = wizard.get_current_step()
        step.password_slave.password.update(u'foobar')
        step.password_slave.confirm_password.update(u'foobar')
        self.check_wizard(wizard, u'wizard-config-admin-password-remote')
        with tempfile.NamedTemporaryFile() as f:
            os.environ[u'PGPASSFILE'] = f.name
            self.click(wizard.next_button)
            data = f.read()
        self.assertEquals(data,
                          (u'remotehost:12345:postgres:username:password\n'
                           u'remotehost:12345:dbname:username:password\n'))

        # Installing
        step = wizard.get_current_step()
        yesno.return_value = False
        step.process_view.emit(u'finished', 0)
        yesno.assert_called_once_with(
            u"The specified database 'dbname' does not exist.\n"
            u"Do you want to create it?", gtk.RESPONSE_YES,
            u"Create database", u"Don't create")

        create_default_profile_settings.assert_called_once_with()
        self.click(wizard.next_button)

        # Link
        step = wizard.get_current_step()
        step.name.update(u'Name')
        step.email.update(u'example@example.com')
        step.phone.update(u'1212341234')
        wizard.link_request_done = True
        self.click(wizard.next_button)

        self.check_wizard(wizard, u'wizard-config-done')

        # FIXME: Find out why this is False when running the tests on a
        # clean database and True otherwhise.
        wizard.has_installed_db = True
        self.click(wizard.next_button)
        self.assertTrue(self.config.flushed)

    @mock.patch('stoq.gui.config.warning')
    def test_database_name(self, warning):

        wizard = self.create_wizard()

        self.click(wizard.next_button)
        step = wizard.get_current_step()
        step.radio_network.set_active(True)
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        step.address.update(u'remotehost')
        step.port.update(12345)
        step.username.update(u'username')
        step.dbname.update(u'invalid; DROP DATABASE postgresql;')
        self.assertFalse(wizard.next_button.props.sensitive)

        # DatabaseSettingsStep, valid
        step.dbname.update(u'valid')
        self.click(wizard.next_button)

        warning.assert_called_once_with(
            u'Invalid database address',
            u"The database address 'remotehost' is invalid. Please fix it and try again")
