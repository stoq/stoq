# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
##
##
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##
""" Runtime routines for applications"""

import sys

from sqlobject import connectionForURI
from kiwi.argcheck import argcheck

_connection = None
_current_user = None
_verbose = False
_test_mode = False
_domain = 'stoqlib'
_config_file = 'stoqlib.conf'
_app_names = None


#
# Work with connections and transactions
#

def initialize_connection():
    # Avoiding circular imports
    from stoqlib.lib.configparser import config
    global _connection
    msg = 'The connection for this application was already set.'
    assert not _connection, msg

    conn_uri = config.get_connection_uri(test_mode=get_test_mode())
    conn = connectionForURI(conn_uri)

    # Stoq applications always use transactions explicitly
    conn.autoCommit = False
    _connection = conn


def get_connection():
    # There is no sense to have more than one database connection for an
    # Stoq application. That's why we always reuse the same _connection
    # variable.
    global _connection
    if not _connection:
        initialize_connection()
    return _connection


def new_transaction():
    _transaction = get_connection().transaction()
    assert _transaction is not None
    return _transaction

#
# User methods
#

def set_verbose(verbose_value):
    global _verbose
    _verbose = verbose_value


def print_immediately(message, break_line=True):
    if break_line:
        print message
    else:
        print message,
    sys.stdout.flush()


def print_msg(message, break_line=True):
    global _verbose
    if not _verbose:
        return
    print_immediately(message, break_line)


def get_current_user():
    global _current_user
    return _current_user


def set_current_user(user):
    global _current_user
    assert user
    # He we store a PersonAdaptToUser object.
    _current_user = user

def set_test_mode(value):
    global _test_mode
    _test_mode = value

def get_test_mode():
    global _test_mode
    return _test_mode

def register_configparser_settings(domain, file_name=''):
    global _domain, _config_file
    _domain = domain
    _config_file = file_name

def get_configparser_settings():
    global _domain, _config_file
    return _domain, _config_file

@argcheck(list)
def register_application_names(app_names):
    global _app_names
    _app_names = app_names

def get_application_names():
    global _app_names
    return _app_names
