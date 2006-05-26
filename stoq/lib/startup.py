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

from stoqlib.lib.admin import initialize_system
from stoqlib.lib.migration import schema_migration
from stoqlib.lib.parameters import ensure_system_parameters
from stoqlib.lib.runtime import get_connection, set_verbose

from stoq.lib.configparser import StoqConfig, register_config

def _update_config(config, options):
    if options.address:
        config.set_hostname(options.address)
    if options.port:
        config.set_port(options.port)
    if options.dbname:
        config.set_database(options.dbname)
    if options.username:
        config.set_username(options.username)
    if options.password:
        config.set_password(options.password)
    if options.verbose:
        set_verbose(options.verbose)

def setup(config, options):
    """
    Loads the configuration from arguments and configuration file.

    @param config: a StoqConfig instance
    @param options: a Optionparser instance
    """

    # NOTE: No GUI calls are allowed in here
    #       If you change anything here, you need to verify that all
    #       callsites are still working properly.
    #       bin/stoq
    #       bin/init-database
    #       python stoq/tests/runtest.py

    _update_config(config, options)

    register_config(config)

    if options.clean:
        initialize_system(options.password,
                          verbose=options.verbose)
    else:
        schema_migration.update_schema()
        ensure_system_parameters()

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

def simple_setup(args, **kwargs):
    """
    Simplified setup:
      - Parses arguments
      - Loads configuration
      - Doing the rest of the initialization
    @param args: command line parameters, normally sys.argv
    @param kwargs: override arguments
    """
    parser = get_option_parser()
    config = StoqConfig()

    options, args = parser.parse_args(args)
    if not 'clean' in kwargs:
        kwargs['clean'] = False
    for key, value in kwargs.items():
        setattr(options, key, value)
    setup(config, options)

