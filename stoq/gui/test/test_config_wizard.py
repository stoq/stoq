# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
from stoqlib.gui.uitestutils import GUITest

from stoq.gui.config import (DatabaseSettingsStep,
                             FirstTimeConfigWizard)


class TestFirstTimeConfigWizard(GUITest):
    @mock.patch('stoq.gui.config.test_local_database')
    @mock.patch('stoq.gui.config.ProcessView.execute_command')
    @mock.patch('stoq.gui.config.ensure_admin_user')
    @mock.patch('stoq.gui.config.create_default_profile_settings')
    @mock.patch('stoq.gui.config.yesno')
    @mock.patch('stoq.gui.config.warning')
    @mock.patch('stoq.gui.config.BranchStation')
    def testLocal(self,
                  BranchStation,
                  warning,
                  yesno,
                  create_default_profile_settings,
                  ensure_admin_user,
                  execute_command,
                  test_local_database):
        options = mock.Mock()
        options.sqldebug = False
        options.verbose = False

        test_local_database.return_value = ('/var/run/postgres', 5432)

        settings = DatabaseSettings(address='localhost',
                                    port=12345,
                                    dbname='dbname',
                                    username='username',
                                    password='password')

        settings.has_database = lambda: False
        config = self.fake.StoqConfig(settings)
        wizard = FirstTimeConfigWizard(options, config)

        self.check_wizard(wizard, 'wizard-config-welcome')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertTrue(step.radio_local.get_active())
        self.check_wizard(wizard, 'wizard-config-database-location')
        self.click(wizard.next_button)

        # Warning should not have being called by now.
        self.assertEquals(warning.call_count, 0, warning.call_args_list)

        self.check_wizard(wizard, 'wizard-config-installation-mode')
        self.click(wizard.next_button)

        self.check_wizard(wizard, 'wizard-config-plugins')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        step.name.update('Name')
        step.email.update('example@example.com')
        step.phone.update('1212341234')
        wizard.tef_request_done = True
        self.check_wizard(wizard, 'wizard-config-tef')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        step.password_slave.password.update('foobar')
        step.password_slave.confirm_password.update('foobar')
        self.check_wizard(wizard, 'wizard-config-admin-password')
        self.click(wizard.next_button)

        self.check_wizard(wizard, 'wizard-config-installing')
        execute_command.assert_called_once_with([
            'stoqdbadmin', 'init',
            '--no-load-config', '--no-register-station', '-v',
            '--enable-plugins', 'ecf',
            '--create-dbuser',
            '-d', 'stoq',
            '-p', '12345',
            '-u', 'username',
            '-w', 'password'])
        step = wizard.get_current_step()
        self.assertEquals(step.progressbar.get_text(),
                          'Creating database...')

        step.process_view.emit('read-line', 'stoqlib.database.create SCHEMA')
        self.assertEquals(step.progressbar.get_text(),
                          'Creating base schema...')

        step.process_view.emit('read-line', 'stoqlib.database.create PATCHES:1')
        self.assertEquals(step.progressbar.get_text(),
                          'Creating schema, applying patches...')

        step.process_view.emit('read-line', 'stoqlib.database.create PATCH:0')
        self.assertEquals(step.progressbar.get_text(),
                          'Creating schema, applying patch 1 ...')

        step.process_view.emit('read-line', 'stoqlib.database.create INIT START')
        self.assertEquals(step.progressbar.get_text(),
                          'Creating additional database objects ...')

        step.process_view.emit('read-line', 'stoqlib.database.create PLUGIN')
        self.assertEquals(step.progressbar.get_text(),
                          'Activating plugins ...')

        yesno.return_value = False
        step.process_view.emit('finished', 30)
        yesno.assert_called_once_with(
            'Something went wrong while trying to create the database. Try again?',
            gtk.RESPONSE_NO, 'Change settings', 'Try again')

        step.process_view.emit('finished', 999)
        warning.assert_called_once_with(
            "Something went wrong while trying to create the Stoq database")

        step.process_view.emit('finished', 0)
        create_default_profile_settings.assert_called_once_with()
        ensure_admin_user.assert_called_once_with('password')
        self.click(wizard.next_button)

        self.check_wizard(wizard, 'wizard-config-done')
        self.click(wizard.next_button)
        self.assertTrue(config.flushed)

    @mock.patch('stoq.gui.config.ProcessView.execute_command')
    @mock.patch('stoq.gui.config.ensure_admin_user')
    @mock.patch('stoq.gui.config.create_default_profile_settings')
    @mock.patch('stoq.gui.config.yesno')
    @mock.patch('stoq.gui.config.warning')
    @mock.patch('stoq.gui.config.BranchStation')
    def testRemote(self,
                   BranchStation,
                   warning,
                   yesno,
                   create_default_profile_settings,
                   ensure_admin_user,
                   execute_command):
        options = mock.Mock()
        options.sqldebug = False
        options.verbose = False

        DatabaseSettingsStep.model_type = self.fake.DatabaseSettings
        settings = self.fake.DatabaseSettings(self.trans)
        config = self.fake.StoqConfig(settings)
        wizard = FirstTimeConfigWizard(options, config)

        # Welcome
        self.click(wizard.next_button)

        # DatabaseLocationStep
        step = wizard.get_current_step()
        step.radio_network.set_active(True)
        self.click(wizard.next_button)

        # DatabaseSettingsStep, invalid
        step = wizard.get_current_step()
        step.address.update('remotehost')
        step.port.update(12345)
        step.username.update('username')
        step.dbname.update('dbname')

        # DatabaseSettingsStep, valid
        settings.check = True
        self.click(wizard.next_button)

        # Installation mode
        self.click(wizard.next_button)

        # Plugins
        self.click(wizard.next_button)

        # TEF
        step = wizard.get_current_step()
        step.name.update('Name')
        step.email.update('example@example.com')
        step.phone.update('1212341234')
        wizard.tef_request_done = True
        self.click(wizard.next_button)

        # AdminPassword
        step = wizard.get_current_step()
        step.password_slave.password.update('foobar')
        step.password_slave.confirm_password.update('foobar')
        self.check_wizard(wizard, 'wizard-config-admin-password')
        fname = tempfile.mktemp()
        os.environ['PGPASSFILE'] = fname
        self.click(wizard.next_button)
        self.assertEquals(open(fname).read(),
                          ('remotehost:12345:postgres:username:\n'
                           'remotehost:12345:dbname:username:\n'))

        # Installing
        step = wizard.get_current_step()
        yesno.return_value = False
        step.process_view.emit('finished', 0)
        yesno.assert_called_once_with(
            "The specifed database 'dbname' does not exist.\n"
            "Do you want to create it?", gtk.RESPONSE_NO, "Don't create",
            "Create database")

        create_default_profile_settings.assert_called_once_with()
        ensure_admin_user.assert_called_once_with('password')
        self.click(wizard.next_button)

        self.check_wizard(wizard, 'wizard-config-done')
        self.click(wizard.next_button)
        self.assertTrue(config.flushed)
