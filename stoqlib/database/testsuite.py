# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2013 Async Open Source <http://www.async.com.br>
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
"""Database routines which are used by the testsuite"""

# FIXME: This should be moved/merged with the normal bootstrap

# This needs to before the other commits, so the externals/
# path is properly setup.
from stoqlib.lib.kiwilibrary import library
library  # pylint: disable=W0104

import logging
import os

from kiwi.component import provide_utility, utilities
from storm.expr import And
from storm.tracer import install_tracer, remove_tracer_type

from stoqlib.database.admin import initialize_system, ensure_admin_user
from stoqlib.database.interfaces import (
    ICurrentBranch, ICurrentBranchStation, ICurrentUser)
from stoqlib.database.runtime import new_store, get_default_store
from stoqlib.database.settings import db_settings
from stoqlib.domain.person import Branch, LoginUser, Person
from stoqlib.domain.station import BranchStation
from stoqlib.importers.stoqlibexamples import create
from stoqlib.lib.interfaces import IApplicationDescriptions, ISystemNotifier
from stoqlib.lib.message import DefaultSystemNotifier
from stoqlib.lib.osutils import get_username
from stoqlib.lib.pluginmanager import get_plugin_manager
from stoqlib.lib.settings import get_settings
from stoqlib.net.socketutils import get_hostname

log = logging.getLogger(__name__)


class StoqlibTestsuiteTracer(object):

    def __init__(self):
        self.reset()

    def install(self):
        self.reset()
        install_tracer(self)

    def remove(self):
        remove_tracer_type(type(self))

    def reset(self):
        self.count = 0

    def connection_raw_execute_success(self, connection, raw_cursor,
                                       statement, params):
        self.count += 1

    def connection_raw_execute_error(self, connection, raw_cursor,
                                     statement, params, error):
        self.count += 1


# This notifier implementation is here to workaround trial; which
# refuses to quit if SystemExit is raised or if sys.exit() is called.
# For now it is assumed that errors() are fatal, that might change in
# the near future


class TestsuiteNotifier(DefaultSystemNotifier):
    def __init__(self):
        self._messages = []

    def reset(self):
        messages = self._messages
        self._messages = []
        return messages

    def message(self, name, short, description):
        self._messages.append((name, short, description))

    def error(self, short, description):
        DefaultSystemNotifier.error(self, short, description)
        os._exit(1)

test_system_notifier = TestsuiteNotifier()


def _provide_database_settings():
    db_settings.username = os.environ.get(u'STOQLIB_TEST_USERNAME',
                                          get_username())
    db_settings.hostname = os.environ.get(u'PGHOST', u'localhost')
    db_settings.port = int(os.environ.get(u'PGPORT', u'5432'))
    db_settings.dbname = os.environ.get(u'STOQLIB_TEST_DBNAME',
                                        u'%s_test' % db_settings.username)
    db_settings.password = u''


def _provide_current_user():
    default_store = get_default_store()
    user = default_store.find(LoginUser, username=u'admin').one()
    assert user
    provide_utility(ICurrentUser, user, replace=True)


def _provide_current_station(station_name=None, branch_name=None):
    if not station_name:
        station_name = get_hostname()
    store = new_store()
    if branch_name:
        branch = store.find(Person,
                            And(Person.name == branch_name,
                                Branch.person_id == Person.id)).one()
    else:
        branches = store.find(Branch)
        if branches.count() == 0:
            person = Person(name=u"test", store=store)
            branch = Branch(person=person, store=store)
        else:
            branch = branches[0]

    provide_utility(ICurrentBranch, branch)

    station = BranchStation.get_station(store, branch, station_name)
    if not station:
        station = BranchStation.create(store, branch, station_name)

    assert station
    assert station.is_active

    provide_utility(ICurrentBranchStation, station)
    store.commit(close=True)


def _provide_app_info():
    from stoqlib.lib.interfaces import IAppInfo
    from stoqlib.lib.appinfo import AppInfo
    info = AppInfo()
    info.set(u"name", u"Stoqlib")
    info.set(u"version", u"1.0.0")
    provide_utility(IAppInfo, info)

# Public API


def provide_database_settings(dbname=None, address=None, port=None, username=None,
                              password=None, createdb=True):
    """
    Provide database settings.
    :param dbname:
    :param address:
    :param port:
    :param username:
    :param password:
    :param create: Create a new empty database if one is missing
    """
    if not username:
        username = get_username()
    if not dbname:
        dbname = username + u'_test'
    if not address:
        address = os.environ.get(u'PGHOST', u'')
    if not port:
        port = os.environ.get(u'PGPORT', u'5432')
    if not password:
        password = u""

    # Remove all old utilities pointing to the previous database.
    utilities.clean()
    provide_utility(ISystemNotifier, test_system_notifier, replace=True)
    _provide_application_descriptions()
    _provide_domain_slave_mapper()
    _provide_app_info()

    db_settings.address = address
    db_settings.port = port
    db_settings.dbname = dbname
    db_settings.username = username
    db_settings.password = password

    rv = False
    if createdb or not db_settings.database_exists(dbname):
        db_settings.clean_database(dbname, force=True)
        rv = True

    return rv


def _provide_domain_slave_mapper():
    from stoqlib.gui.interfaces import IDomainSlaveMapper
    from stoqlib.gui.slaves.domainslavemapper import DefaultDomainSlaveMapper
    provide_utility(IDomainSlaveMapper, DefaultDomainSlaveMapper(),
                    replace=True)


def _provide_application_descriptions():
    from stoq.lib.applist import ApplicationDescriptions
    provide_utility(IApplicationDescriptions, ApplicationDescriptions(),
                    replace=True)


def provide_utilities(station_name, branch_name=None):
    """
    Provide utilities like current user and current station.
    :param station_name:
    :param branch_name:
    """
    _provide_current_user()
    _provide_current_station(station_name, branch_name)
    _provide_domain_slave_mapper()


def _enable_plugins():
    manager = get_plugin_manager()
    for plugin in [u'ecf',
                   u'nfe',
                   u'optical']:
        if not manager.is_installed(plugin):
            # STOQLIB_TEST_QUICK won't let dropdb on testdb run. Just a
            # precaution to avoid trying to install it again
            manager.install_plugin(plugin)

        else:
            # Make sure that the plugin is imported so sys.path is properly
            # setup
            plugin = manager.get_plugin(plugin)
            plugin  # pylint: disable=W0104


def bootstrap_suite(address=None, dbname=None, port=5432, username=None,
                    password=u"", station_name=None, quick=False):
    """
    Test.
    :param address:
    :param dbname:
    :param port:
    :param username:
    :param password:
    :param station_name:
    :param quick:
    """

    # This will only be required when we use uuid.UUID instances
    # for UUIDCol
    #import psycopg2.extras
    #psycopg2.extras.register_uuid()

    empty = provide_database_settings(dbname, address, port, username, password,
                                      createdb=not quick)

    # Reset the user settings (loaded from ~/.stoq/settings), so that user
    # preferences don't affect the tests.
    settings = get_settings()
    settings.reset()

    if quick and not empty:
        provide_utilities(station_name)
        _enable_plugins()
        return

    initialize_system(testsuite=True, force=True)

    # Commit before trying to apply patches which requires an exclusive lock
    # to all tables.
    _enable_plugins()
    ensure_admin_user(u"")
    create(utilities=True)
