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

import gettext
import socket

from kiwi.argcheck import argcheck
from kiwi.component import provide_utility
from sqlobject import sqlhub
from stoqlib.database.admin import ensure_admin_user, initialize_system
from stoqlib.database.migration import SchemaMigration
from stoqlib.database.runtime import get_connection, set_current_branch_station, new_transaction
from stoqlib.domain.profile import UserProfile
from stoqlib.domain.profile import ProfileSettings
from stoqlib.exceptions import DatabaseError
from stoqlib.lib.interfaces import  IApplicationDescriptions
from stoqlib.lib.message import error

from stoq.lib.configparser import register_config, StoqConfig

_ = gettext.gettext

def setup(config, options=None, register_station=True, check_schema=True):
    """
    Loads the configuration from arguments and configuration file.

    @param config: a StoqConfig instance
    @param options: a Optionparser instance
    @param register_station: if we should register the branch station.
    @param check_schema: if we should check the schema
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
            # FIXME: Set KIWI_LOG
            pass

        config.set_from_options(options)

    register_config(config)

    from stoq.lib.applist import ApplicationDescriptions
    provide_utility(IApplicationDescriptions, ApplicationDescriptions())

    try:
        conn = get_connection()
    except DatabaseError, e:
        error(e.short, e.msg)

    if register_station:
        set_current_branch_station(conn, socket.gethostname())
    if check_schema:
        if not SchemaMigration().check_updated():
            error(_("Database schema error"),
                  _("The database schema has changed, but the database has "
                    "not been updated. Run 'stoqdbadmin updateschema` to"
                    "update the schema  to the latest available version."))

    if options and options.debug:
        from stoqlib.gui.keyboardhandler import install_global_keyhandler
        from stoqlib.gui.introspection import introspect_slaves
        from gtk import keysyms

        install_global_keyhandler(keysyms.F12, introspect_slaves)

        conn.debug = True
    sqlhub.threadConnection = conn

def clean_database(config, options=None):
    """Clean the database
    @param config: a StoqConfig instance
    @param options: a Optionparser instance
    """
    if not options:
        password = ''
        verbose = False
    else:
        password = options.password
        verbose = options.verbose

    password = password or config.get_password()
    initialize_system(verbose=verbose)
    _set_default_profile_settings()
    ensure_admin_user(password)

def _set_default_profile_settings():
    trans = new_transaction()
    profile = UserProfile.selectOneBy(name='Salesperson', connection=trans)
    ProfileSettings.set_permission(trans, profile, 'pos', True)
    trans.commit(close=True)

@argcheck(StoqConfig)
def create_examples(config):
    """Create example database for a given config file"""
    from stoqlib.domain.examples.createall import create
    create()
