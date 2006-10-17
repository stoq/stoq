# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Johan Dahlin      <jdahlin@async.com.br>
##
"""Bootstrap the database"""

import os
import pwd
import socket

from kiwi.component import provide_utility
from kiwi.log import Logger

from stoqlib.database.admin import initialize_system, ensure_admin_user
from stoqlib.database.database import (create_database_if_missing,
                                       finish_transaction)
from stoqlib.database.runtime import (new_transaction, get_connection,
                                      get_current_station)
from stoqlib.database.settings import DatabaseSettings
from stoqlib.domain.examples.createall import create
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import IBranch, IUser
from stoqlib.domain.station import BranchStation
from stoqlib.lib.drivers import (get_fiscal_printer_settings_by_station,
                                 create_virtual_printer_for_current_station)
from stoqlib.lib.interfaces import (IApplicationDescriptions,
                                    ICurrentBranch,
                                    ICurrentBranchStation,
                                    ICurrentUser,
                                    IDatabaseSettings)
from stoqlib.lib.message import DefaultSystemNotifier, ISystemNotifier

log = Logger('stoqlib.tests')

# Provide a fake description utility, the ProfileSettings class depends on it
class FakeApplicationDescriptions:
    def get_application_names(self):
        return []

    def get_descriptions(self):
        return []
provide_utility(IApplicationDescriptions, FakeApplicationDescriptions())

# This test is here to workaround trial; which refuses to quit
# if SystemExit is raises or if sys.exit() is called.
# For now it is assumed that errors() are fatal, that might change in
# the near future
class TestsuiteNotifier(DefaultSystemNotifier):
    def error(self, short, description):
        DefaultSystemNotifier.error(self, short, description)
        os._exit(1)
provide_utility(ISystemNotifier, TestsuiteNotifier(), replace=True)

def _provide_database_settings():
    username = os.environ.get('STOQLIB_TEST_USERNAME',
                              pwd.getpwuid(os.getuid())[0])
    hostname = os.environ.get('STOQLIB_TEST_HOSTNAME', 'localhost')
    port = int(os.environ.get('STOQLIB_TEST_PORT', '5432'))
    dbname =  os.environ.get('STOQLIB_TEST_DBNAME',
                             '%s_test' % username)
    password = ''

    db_settings = DatabaseSettings(address=hostname,
                                   port=port,
                                   dbname=dbname,
                                   username=username,
                                   password=password)
    provide_utility(IDatabaseSettings, db_settings)

    if not db_settings.has_database():
        log.warning('Database %s missing, creating it' % dbname)
        conn = db_settings.get_default_connection()
        create_database_if_missing(conn, dbname)
        return True

    return False

def _provide_current_user():
    user = Person.iselectOneBy(IUser, username='admin',
                               connection=get_connection())
    provide_utility(ICurrentUser, user)

def _provide_current_station():
    trans = new_transaction()
    branches = Person.iselect(IBranch, connection=trans)
    assert branches
    branch = branches[0]
    provide_utility(ICurrentBranch, branch)

    name = socket.gethostname()
    station = BranchStation.get_station(trans, branch, name)
    if not station:
        station = BranchStation.create(trans, branch, name)
        trans.commit()

    assert station
    assert station.is_active

    provide_utility(ICurrentBranchStation, station)
    finish_transaction(trans, 1)

def _provide_devices():
    conn = get_connection()

    station = get_current_station(conn)
    if not get_fiscal_printer_settings_by_station(conn, station):
        create_virtual_printer_for_current_station()

def bootstrap_testsuite():
    quick = os.environ.get('STOQLIB_TEST_QUICK', None) is not None

    try:
        empty = _provide_database_settings()

        if quick and not empty:
            _provide_current_user()
            _provide_current_station()
            _provide_devices()
        else:
            initialize_system()
            ensure_admin_user("")
            create(utilities=True)
    except Exception, e:
        # Work around trial
        import traceback
        traceback.print_exc()
        os._exit(1)
