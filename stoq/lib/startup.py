# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
##
""" Database startup routines"""

import optparse

from sqlobject import sqlhub
from sqlobject.sqlbuilder import AND
from kiwi.argcheck import argcheck

from stoqlib.exceptions import StoqlibError
from stoqlib.database import check_installed_database
from stoqlib.lib.admin import initialize_system
from stoqlib.lib.message import error
from stoqlib.lib.migration import schema_migration
from stoqlib.lib.parameters import check_parameter_presence
from stoqlib.lib.runtime import (get_connection, set_verbose,
                                 register_current_branch_identifier,
                                 register_current_station_identifier,
                                 get_current_station)

from stoq.lib.configparser import register_config, StoqConfig

def set_branch_by_stationid(identifier, conn=None):
    from stoqlib.domain.person import BranchStation
    conn = conn or get_connection()

    try:
        identifier = int(identifier)
    except ValueError, e:
        error("Invalid configuration settings for identifier, got %s"
              % identifier)

    if not identifier:
        # We are configuring a new computer -> skip
        return
    table = BranchStation
    q1 = table.q.is_active == True
    q2 = table.q.identifier == identifier
    query = AND(q1, q2)
    stations = table.select(query, connection=conn)
    if stations.count() != 1:
        raise StoqlibError("You should have one station for the identifier "
                           "%s, got %d." % (identifier, stations.count()))
    station = stations[0]
    identifier = station.branch.identifier
    register_current_branch_identifier(identifier)
    register_current_station_identifier(station.identifier)


def setup(config, options=None, stoq_user_password=''):
    """
    Loads the configuration from arguments and configuration file.

    @param config: a StoqConfig instance
    @param options: a Optionparser instance
    """

    # NOTE: No GUI calls are allowed in here
    #       If you change anything here, you need to verify that all
    #       callsites are still working properly.
    #       bin/debug
    #       bin/stoq
    #       bin/stoqdbadmin
    #       python stoq/tests/runtest.py


    if options:
        if options.verbose:
            set_verbose(options.verbose)

        config.set_from_options(options)

    register_config(config)

    if (options and options.clean) or not check_installed_database():
        if not options:
            password = stoq_user_password
            verbose = False
        else:
            password = options.password or config.get_password()
            verbose = options.verbose
        initialize_system(password or '', verbose=verbose)
    else:
        set_branch_by_stationid(config.get_station_id())
        schema_migration.update_schema()
        check_parameter_presence()

    sqlhub.threadConnection = get_connection()


def get_option_parser():
    """
    Get the option parser used to parse arguments on the command line
    @returns: an optparse.OptionParser
    """

    # Note: only generic command line options here, specific ones
    #       should be added at callsite

    parser = optparse.OptionParser()

    group = optparse.OptionGroup(parser, 'General')
    group.add_option('-c', '--clean',
                      action="store_true",
                      dest="clean",
                      default=False,
                      help='Clean up database')
    group.add_option('-f', '--filename',
                      action="store",
                      type="string",
                      dest="filename",
                      default=None,
                      help='Use this file name for config file')
    group.add_option('-v', '--verbose',
                     action="store_true",
                     dest="verbose",
                     default=False)
    parser.add_option_group(group)

    group = optparse.OptionGroup(parser, 'Database access')
    group.add_option('-d', '--dbname',
                      action="store",
                      dest="dbname",
                      help='Database name to use')
    group.add_option('-a', '--address',
                      action="store",
                      dest="address",
                      help='Database address to connect to')
    group.add_option('-p', '--port',
                      action="store",
                      dest="port",
                      help='Database port')
    group.add_option('-u', '--username',
                      action="store",
                      dest="username",
                      help='Database username')
    group.add_option('-w', '--password',
                     action="store",
                     type="str",
                     dest="password",
                     help='user password',
                     default='')
    parser.add_option_group(group)
    return parser

@argcheck(StoqConfig)
def create_examples(config):
    """Create example database for a given config file"""
    from stoqlib.domain.examples.createall import create
    create()
    conn = get_connection()
    station = get_current_station(conn)
    if not station:
        raise StoqlibError(
            "You should have a valid station set at this point")

    config.set_station_id(station.identifier)
    config.flush()
