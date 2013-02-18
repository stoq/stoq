# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

"""Tests for module :class:`stoqlib.database.settings`"""

import os

import mock

from stoqlib.database.settings import DatabaseSettings
from stoqlib.domain.test.domaintest import DomainTest


class DatabaseSettingsTest(DomainTest):

    def test_get_store_dsn(self):
        settings = DatabaseSettings(address='address',
                                    username='username')
        self.assertEquals(settings.get_store_dsn(),
                          'postgres://username@address:5432/stoq')

    def test_get_store_dsn_password(self):
        settings = DatabaseSettings(address='address',
                                    username='username',
                                    password='password')
        self.assertEquals(settings.get_store_dsn(),
                          'postgres://username:password@address:5432/stoq')

    def test_get_store_dsn_port(self):
        settings = DatabaseSettings(address='address',
                                    username='username',
                                    port='12345')
        self.assertEquals(settings.get_store_dsn(),
                          'postgres://username@address:12345/stoq')

    @mock.patch('stoqlib.database.runtime.StoqlibStore')
    @mock.patch('stoqlib.database.settings.create_database')
    def test_create_store(self, create_database, StoqlibStore):
        settings = DatabaseSettings(address='address',
                                    username='username',
                                    password='password',
                                    port='12345')
        store = settings.create_store()
        create_database.assert_called_once()
        uri = create_database.call_args[0][0]
        self.assertEquals(
            str(uri),
            'postgres://username:password@address:12345/stoq?isolation=read-committed')
        StoqlibStore.assert_called_once()
        self.failUnless(store)

    @mock.patch('stoqlib.database.runtime.StoqlibStore')
    @mock.patch('stoqlib.database.settings.create_database')
    @mock.patch('stoqlib.database.settings.test_local_database')
    def test_create_store_localhost(self, test_local_database,
                                    create_database, StoqlibStore):
        # FIXME: This should not be necessary, instead DatabaseSettings should
        #        do if address is not None to differenciate between '' and None
        os.environ.pop('PGHOST', None)
        test_local_database.return_value = ('/var/run/postgresql', '5432')
        settings = DatabaseSettings(address='',
                                    username='username')
        store = settings.create_store()
        create_database.assert_called_once()
        test_local_database.called_once_with()
        uri = create_database.call_args[0][0]
        self.assertEquals(uri.host, '/var/run/postgresql')
        self.assertEquals(uri.port, 5432)
        self.assertEquals(
            str(uri),
            'postgres://username@%2Fvar%2Frun%2Fpostgresql:5432/stoq?isolation=read-committed')
        StoqlibStore.assert_called_once()
        self.failUnless(store)

    @mock.patch('stoqlib.database.runtime.StoqlibStore')
    @mock.patch('stoqlib.database.settings.create_database')
    def test_create_super_store(self, create_database, StoqlibStore):
        settings = DatabaseSettings(address='localhost',
                                    username='username')
        store = settings.create_super_store()
        create_database.assert_called_once()
        uri = create_database.call_args[0][0]
        self.assertEquals(
            str(uri),
            'postgres://username@localhost:5432/postgres?isolation=read-committed')
        StoqlibStore.assert_called_once()
        self.failUnless(store)

    def test_get_command_line_arguments(self):
        settings = DatabaseSettings(address='address',
                                    username='username',
                                    password='password',
                                    port='12345')
        self.assertEquals(settings.get_command_line_arguments(),
                          ['-d', 'stoq',
                           '-H', 'address',
                           '-p', '12345',
                           '-u', 'username',
                           '-w', 'password'])

    def test_get_tool_args(self):
        settings = DatabaseSettings(address='address',
                                    username='username',
                                    password='password',
                                    port='12345')
        self.assertEquals(settings.get_tool_args(),
                          ['-U', 'username',
                           '-h', 'address',
                           '-p', '12345'])
