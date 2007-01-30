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
import optparse
from ConfigParser import SafeConfigParser

from kiwi.argcheck import argcheck
from kiwi.component import provide_utility
from stoqlib.database.interfaces import IDatabaseSettings
from stoqlib.database.settings import DEFAULT_RDBMS, DatabaseSettings
from stoqlib.exceptions import (FilePermissionError, ConfigError,
                                NoConfigurationError)

_ = gettext.gettext
_config = None

def getlogin():
    import pwd
    return pwd.getpwuid(os.getuid())[0]

class StoqConfig:
    config_template = \
"""
# This file is generated automatically by Stoq and should not be changed
# manually unless you know exactly what are you doing.


[General]
# Default file where status and errors are appended to. Comment this out
# to allow output to be sent to stderr/stdout
logfile=~/.%(DOMAIN)s/application.log

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

    def __init__(self):
        self._config = SafeConfigParser()
        self._filename = None
        self._settings = None

    def _get_config_file(self):
        filename = self.domain + '.conf'
        configdir = self.get_config_directory()
        return os.path.join(configdir, filename)

    def _open_config(self, filename):
        if not os.path.exists(filename):
            return False
        self._config.read(filename)

        for section in StoqConfig.sections:
            if not self._config.has_section(section):
                raise ConfigError(
                    "config file does not have section: %s" % section)
        return True

    def _get_password(self, filename):
        if not os.path.exists(filename):
            return

        data = open(filename).read()
        return binascii.a2b_base64(data)

    def _check_permissions(self, origin, writable=False, executable=False):
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

    def _has_option(self, name, section='General'):
        return self._config.has_option(section, name)

    def _get_option(self, name, section='General'):
        if not section in StoqConfig.sections:
            raise ConfigError('Invalid section: %s' % section)

        if self._config.has_option(section, name):
            return self._config.get(section, name)

        raise NoConfigurationError('%s does not have option: %s' %
                                   (self._filename, name))

    def _get_rdbms_name(self):
        if not self._has_option('rdbms', section='Database'):
            return 'postgres'
        return self._get_option('rdbms', section='Database')

    def _get_address(self):
        return self._get_option('address', section='Database')

    def _get_port(self):
        if not self._has_option('port', section='Database'):
            return '5432'
        return self._get_option('port', section='Database')

    def _get_dbname(self):
        if not self._has_option('dbname', section='Database'):
            return self._get_username()
        return self._get_option('dbname', section='Database')

    def _get_username(self):
        if not self._has_option('dbusername', section='Database'):
            return getlogin()
        return self._get_option('dbusername', section='Database')

    #
    # Public API
    #

    def create(self):
        config_dir = self.get_config_directory()
        if not os.path.exists(config_dir):
            os.mkdir(config_dir)
        self._filename = os.path.join(
            config_dir, StoqConfig.domain + '.conf')

        if not self._config.has_section('General'):
            self._config.add_section('General')

        if not self._config.has_section('Database'):
            self._config.add_section('Database')

    def load(self, filename=None):
        """
        Loads the data from a configuration file, if filename is
        not specified the default one will be loaded
        @param filename: filename
        """
        if not filename:
            filename = self._get_config_file()

        if filename:
            if not self._open_config(filename):
                filename = None

        self._filename = filename

    @argcheck(DatabaseSettings)
    def load_settings(self, settings):
        """
        Load data from a DatabaseSettings object
        @param settings: the settings object
        """
        for section in StoqConfig.sections:
            if not self._config.has_section(section):
                self._config.add_section(section)

        self._config.set('General', 'logfile',
                         os.path.join(os.environ['HOME'], StoqConfig.domain,
                                      'application.log'))
        self._config.set('Database', 'rdbms', StoqConfig.rdbms)
        self._config.set('Database', 'address', settings.address)
        self._config.set('Database', 'port', str(settings.port))
        self._config.set('Database', 'dbname', settings.dbname)
        self._config.set('Database', 'testdb', settings.dbname)
        self._config.set('Database', 'dbusername', settings.username)
        self.store_password(settings.password)
        self._settings = settings

    def flush(self):
        """
        Writes the current configuration data to disk.
        """
        if not self._filename:
            self._filename = self._get_config_file()
        filename = self._filename

        fd = open(filename, 'w')
        self._config.write(fd)
        fd.close()

    def remove(self):
        if not self._filename:
            return
        self._check_permissions(self._filename)
        os.remove(self._filename)

    def get_config_directory(self):
        return os.path.join(os.getenv('HOME'), '.' + self.domain)

    def use_test_database(self):
        self._config.set('Database', 'dbname',
                         self._get_option('testdb', section='Database'))

    def check_connection(self):
        # This will trigger a "check"
        self.get_connection_uri()

    def store_password(self, password):
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

    #
    # Accessors
    #

    def get_password(self):
        """
        @returns: password or None if it is not set
        """

        configdir = self.get_config_directory()
        data_file = os.path.join(configdir, StoqConfig.datafile)
        return self._get_password(data_file)

    def get_connection_uri(self):
        db_settings = self.get_settings()
        return db_settings.get_connection_uri()

    def get_settings(self):
        if not self._settings:
            rdbms = self._get_rdbms_name()
            dbname = self._get_option('dbname', section='Database')

            if self._has_option('dbusername', section='Database'):
                username = self._get_option('dbusername', section='Database')
            else:
                username = getlogin()
            settings = DatabaseSettings(
                rdbms, self._get_address(), self._get_port(),
                dbname, username, self.get_password())
        else:
            settings = self._settings
        return settings

    @argcheck(optparse.Values)
    def set_from_options(self, options):
        """
        Updates the configuration given a values instance
        @param options: a optparse.Values instance
        """

        if options.address:
            self._config.set('Database', 'address', options.address)
        if options.port:
            self._config.set('Database', 'port', options.port)
        if options.dbname:
            self._config.set('Database', 'dbname', options.dbname)
        if options.username:
            self._config.set('Database', 'dbusername', options.username)
        if options.password:
            self.store_password(options.password)



#
# General routines
#


@argcheck(StoqConfig)
def register_config(config):
    global _config
    _config = config

    provide_utility(IDatabaseSettings, config.get_settings())

def get_config():
    global _config
    return _config
