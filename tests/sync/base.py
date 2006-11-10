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
## Author(s):   Henrique Romano  <henrique@async.com.br>
##
import os
import subprocess
import atexit

try:
    from twisted.trial import unittest
    unittest # pyflakes
except:
    import unittest

from kiwi.component import get_utility
from kiwi.log import Logger

from stoqlib.database.interfaces import IDatabaseSettings
from stoqlib.database.runtime import new_transaction
from stoqlib.database.synchronization import SynchronizationClient
from stoqlib.database.testsuite import (provide_database_settings,
                                        provide_utilities, bootstrap_testsuite)
from stoqlib.domain.interfaces import ICompany, IBranch
from stoqlib.domain.person import Person
from stoqlib.domain.station import BranchStation

from tests import base
base #pyflakes

log = Logger('tests.sync.base')

# XXX: to be replaced by a config module
class SyncTestData:
    """ Data needed by SyncTest """
    server_proc = None
    orig_dbname = None
    office_dbname = None
    shop_dbname = None
    client = None
    office_trans = None
    shop_trans = None
    db_address = None
    db_port = None
    db_username = None
    db_password = None

class SyncTest(unittest.TestCase):
    """ Base class for all the tests related to database synchronization.

    It is important to note that the SyncTestData must be *already* filled
    before this class is initialized; normally, the SyncTestData is
    initialized when this module is imported.
    """

    def update(self, station_name):
        return SyncTestData.client.update(station_name)

    def _switch_to_database(self, dbname, station_name, branch_name):
        provide_database_settings(dbname, SyncTestData.db_address,
                                  SyncTestData.db_port,
                                  SyncTestData.db_username,
                                  SyncTestData.db_password,
                                  create=False)
        provide_utilities(station_name, branch_name)

    def switch_to_shop(self):
        log.info("Switching to shop database")
        self._switch_to_database(SyncTestData.shop_dbname, 'shop-computer',
                                 'Second branch')

    def switch_to_office(self):
        log.info("Switching to office database")
        self._switch_to_database(SyncTestData.office_dbname, 'Stoqlib station',
                                 'Async Open Source')

    @classmethod
    def tearDownClass(cls):
        _provide_original_settings()

#
# Bootstrap
#

def _provide_original_settings():
    log.info("Restoring original database settings.")
    data = (SyncTestData.orig_dbname,
            SyncTestData.db_address,
            SyncTestData.db_port,
            SyncTestData.db_username,
            SyncTestData.db_password)
    if None in data:
        raise ValueError("The test data should contains valid "
                         "data at this point")
    provide_database_settings(*data)
    provide_utilities("Stoqlib station", "Async Open Source")


def _create_office_database(conn):
    log.info("Creating office database.")
    if conn.databaseExists(SyncTestData.office_dbname):
        conn.dropDatabase(SyncTestData.office_dbname)
    bootstrap_testsuite(SyncTestData.db_address,
                        SyncTestData.office_dbname,
                        SyncTestData.db_port,
                        SyncTestData.db_username,
                        SyncTestData.db_password)

def _create_shop_database(conn):
    log.info("Creating shop database")
    if conn.databaseExists(SyncTestData.shop_dbname):
        conn.dropDatabase(SyncTestData.shop_dbname)
    provide_database_settings(SyncTestData.shop_dbname,
                              SyncTestData.db_address,
                              SyncTestData.db_port,
                              SyncTestData.db_username,
                              SyncTestData.db_password)

def _register_shop_station(trans):
    log.info("Registering a new station for the shop.")
    person = Person(name="Second branch", connection=trans)
    person.addFacet(ICompany, connection=trans)
    branch = person.addFacet(IBranch, connection=trans)
    station = BranchStation(branch=branch, name="shop-computer",
                            connection=trans)
    station.activate()

def terminate_server(proc):
    SyncTestData.client.quit()
    proc.wait()

def _initialize_server():
    server_path = os.path.join(os.path.dirname(__file__), "syncd")
    cmd = ("%s -H %s -d %s -s %s -u %s"
           % (server_path, SyncTestData.db_address,
              SyncTestData.shop_dbname, "shop-computer",
              SyncTestData.db_username))
    log.info("Starting up server with command %s" % cmd)
    SyncTestData.server_proc = subprocess.Popen(cmd, shell=True)
    atexit.register(terminate_server, SyncTestData.server_proc)

def bootstrap():
    settings = get_utility(IDatabaseSettings)
    conn = settings.get_connection()

    SyncTestData.orig_dbname = settings.dbname
    SyncTestData.shop_dbname = settings.dbname + '_shop'
    SyncTestData.office_dbname = settings.dbname + '_office'
    SyncTestData.db_address = settings.address
    SyncTestData.db_port = settings.port
    SyncTestData.db_username = settings.username
    SyncTestData.db_password = settings.password

    _create_shop_database(conn)
    _initialize_server()
    conn.close()
    _create_office_database(conn)

    trans = new_transaction()
    _register_shop_station(trans)
    trans.commit()

    SyncTestData.client = SynchronizationClient("localhost", 9000)
    SyncTestData.client.clean()
    SyncTestData.client.clone("shop-computer", transaction=trans)

    _provide_original_settings()

try:
    bootstrap()
except Exception, e:
    # Work around trial
    import traceback
    traceback.print_exc()
    os._exit(1)
