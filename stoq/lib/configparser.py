# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##
##  Author(s):  Evandro Vale Miquelito  <evandro@async.com.br>
##              Henrique Romano         <henrique@async.com.br>
##              Johan Dahlin            <jdahlin@async.com.br>
##
"""Routines for parsing the configuration file"""

import binascii
import gettext
import os
import sys
from ConfigParser import SafeConfigParser

from kiwi.environ import environ, EnvironmentError
from kiwi.argcheck import argcheck
from stoqlib.database import (DEFAULT_RDBMS, DatabaseSettings,
                              build_connection_uri,
                              check_database_connection)
from stoqlib.exceptions import (FilePermissionError, ConfigError,
                                NoConfigurationError)

_ = gettext.gettext
_config = None


class StoqConfig:
    config_template = \
"""
# This file is generated automatically by Stoq and should not be changed
# manually unless you know exactly what are you doing.


[General]
# Default file where status and errors are appended to. Comment this out
# to allow output to be sent to stderr/stdout
logfile=~/.%(DOMAIN)s/application.log

# Set here the Branch Station identifier for the current station. Note that
# this field is not used when running an example database
#
# Warning: you should never change this option unless you know exactly what are
# you doing
#
station_id=%(STATION_ID)s

[Database]
# Choose here the relational database management system you would like to
# use. Available is: postgres
rdbms=%(RDBMS)s

# This is used by the client to find the server.
address=%(ADDRESS)s

# The port to connect to
port=%(PORT)s

# The name of Stoq database in rdbms.
dbname=%(DBNAME)s

# the test database name
testdb=%(TESTDB)s

# The database username in rdbms.
dbusername=%(DBUSERNAME)s"""

    sections = ['General', 'Database']
    # Only Postgresql database is supported right now
    rdbms = DEFAULT_RDBMS
    domain = 'stoq'
    datafile = 'data'

    def __init__(self, filename=None):
        if not filename:
            filename = self._get_config_file()

        self._config = SafeConfigParser()

        if filename:
            if not self._open_config(filename):
                filename = None

        self._filename = filename

    def _write_config_data(self):
        fd = open(self._filename, 'w')
        self._config.write(fd)
        fd.close()

    def _get_config_file(self):
        filename = self.domain + '.conf'
        configdir = self.get_config_directory()
        standard = os.path.join(configdir, filename)
        if os.path.exists(standard):
            return standard

        try:
            conf_file = environ.find_resource('config', filename)
        except EnvironmentError, e:
            return
        return conf_file

    def get_config_directory(self):
        return os.path.join(os.getenv('HOME'), '.' + self.domain)

    def _open_config(self, filename):
        if not os.path.exists(filename):
            return False
        self._config.read(filename)

        for section in StoqConfig.sections:
            if not self._config.has_section(section):
                raise ConfigError(
                    "config file does not have section: %s" % section)
        return True

    def _store_password(self, password):
        configdir = self.get_config_directory()
        datafile = os.path.join(configdir, StoqConfig.datafile)
        if not os.path.exists(datafile):
            if not os.path.exists(configdir):
                try:
                    os.makedirs(configdir)
                    os.chmod(configdir, 0700)
                except OSError, e:
                    if e.errno == 13:
                        raise FilePermissionError(
                            "Could not " % configdir)
                    raise

        try:
            fd = open(datafile, "w")
        except OSError, e:
            if e.errno == 13:
                raise FilePermissionError("%s is not writable" % datafile)
            raise

        # obfuscate password to avoid it being easily identified when
        # editing file on screen. this is *NOT* encryption!
        fd.write(binascii.b2a_base64(password))
        fd.close()

    def _get_password(self, filename):
        if not os.path.exists(filename):
            return

        data = open(filename).read()
        return binascii.a2b_base64(data)

    #
    # Public API
    #

    def check_permissions(self, origin, writable=False, executable=False):
        # Make sure permissions are correct on relevant files/directories
        exception = None
        if not os.access(origin, os.R_OK):
            exception = "%s is not readable."
        if writable and not os.access(origin, os.W_OK):
            exception = "%s is not writable."
        if executable and not os.access(origin, os.X_OK):
            exception = "%s is not executable."
        if exception:
            raise FilePermissionError(exception % origin)

    def remove_config_file(self):
        self.check_permissions(self._filename)
        os.remove(self._filename)

    def has_installed_config_data(self):
        return self._filename != None

    @argcheck(DatabaseSettings, int)
    def install_default(self, config_data, station_id=0):
        password = config_data.password

        self._store_password(password)
        configdir = self.get_config_directory()
        filename = os.path.join(configdir, StoqConfig.domain + '.conf')
        fd = open(filename, 'w')
        config_dict = dict(DOMAIN=StoqConfig.domain,
                           RDBMS=StoqConfig.rdbms,
                           PORT=config_data.port,
                           ADDRESS=config_data.address,
                           DBNAME=config_data.dbname,
                           STATION_ID=station_id,
                           TESTDB=config_data.dbname,
                           DBUSERNAME=config_data.username)
        fd.write(StoqConfig.config_template % config_dict)
        fd.close()
        self._config.read(filename)
        self._filename = filename

    def has_option(self, name, section='General'):
        return self._config.has_option(section, name)

    def get_option(self, name, section='General'):
        if not section in StoqConfig.sections:
            raise ConfigError('Invalid section: %s' % section)

        if self._config.has_option(section, name):
            return self._config.get(section, name)

        raise NoConfigurationError('%s does not have option: %s' %
                                   (self._filename, name))

    def set_option(self, section, name, value, write_to_file=False):
        if not section in StoqConfig.sections:
            raise ConfigError('Invalid section: %s' % section)

        self._config.set(section, name, value)
        if write_to_file:
            self._write_config_data()

    def set_station(self, station_id, write_to_file=False):
        """
        Overrides the station_id option
        @param station_id: the identifier of branch station
        """
        self.set_option("General", "station_id", station_id, write_to_file)

    def set_database(self, database):
        """
        Overrides the default database configuration option.
        @param database: the database
        """
        self._config.set('Database', 'dbname', database)

    def set_username(self, username):
        """
        Overrides the default username configuration option.
        @param username: the username
        """
        self._config.set('Database', 'dbusername', username)

    def set_hostname(self, hostname):
        """
        Overrides the default hostname configuration option.
        @param hostname: the hostname
        """
        self._config.set('Database', 'address', hostname)

    def set_port(self, port):
        """
        Overrides the default hostname configuration option.
        param port: the port
        """
        self._config.set('Database', 'port', port)

    def set_password(self, password):
        """
        Overrides the default hostname configuration option.
        @param password: the password
        """
        self._store_password(password)

    def use_test_database(self):
        self.set_database(self.get_option('testdb', section='Database'))

    def check_connection(self):
        """Checks the stored database rdbms settings and raises ConfigError
        if something is wrong
        """
        try:
            conn_uri = self.get_connection_uri()
        except:
            raise
            type, value, trace = sys.exc_info()
            raise ConfigError(value)

        check_database_connection(conn_uri)


    #
    # Accessors
    #

    def get_station_id(self):
        return self.get_option('station_id', section='General')

    def get_rdbms_name(self):
        return self.get_option('rdbms', section='Database')

    def get_address(self):
        return self.get_option('address', section='Database')

    def get_port(self):
        return self.get_option('port', section='Database')

    def get_dbname(self):
        return self.get_option('dbname', section='Database')

    def get_username(self):
        return self.get_option('dbusername', section='Database')

    def get_password(self):
        """
        @returns: password or None if it is not set
        """

        configdir = self.get_config_directory()
        data_file = os.path.join(configdir, StoqConfig.datafile)
        return self._get_password(data_file)

    def get_connection_uri(self):
        rdbms = self.get_rdbms_name()
        dbname = self.get_option('dbname', section='Database')

        if self.has_option('dbusername', section='Database'):
            username = self.get_option('dbusername', section='Database')
        else:
            username = os.getlogin()
        return build_connection_uri(self.get_address(), self.get_port(),
                                    dbname, rdbms, username,
                                    self.get_password())

    def get_settings(self):
        return DatabaseSettings(self.get_rdbms_name(),
                                self.get_address(),
                                self.get_port(),
                                self.get_dbname(),
                                self.get_username(),
                                self.get_password())

#
# General routines
#


def _setup_stoqlib(config):
    from stoqlib.database import register_db_settings
    from stoqlib.lib.runtime import register_application_names
    from stoq.lib.applist import get_application_names

    register_db_settings(config.get_settings())
    register_application_names(get_application_names())

@argcheck(StoqConfig)
def register_config(config):
    global _config
    _config = config
    _setup_stoqlib(config=config)

def get_config():
    global _config
    return _config
