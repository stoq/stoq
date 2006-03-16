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

import os
import sys
import gettext
import binascii
from ConfigParser import SafeConfigParser

from kiwi.environ import environ, EnvironmentError
from kiwi.argcheck import argcheck
from stoqlib.database import (DEFAULT_RDBMS, DatabaseSettings,
                              get_connection_uri)
from stoqlib.exceptions import (FilePermissionError, ConfigError,
                                NoConfigurationError)

_ = gettext.gettext
_config = None


class StoqConfigParser:
    config_template = \
"""
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
    filename = 'stoq.conf'
    datafile = 'data'

    def __init__(self, test_mode=False):
        self.config = SafeConfigParser()
        self.test_mode = test_mode
        homepath = self.get_homepath()
        self.home_filename = os.path.join(homepath, self.filename)

    def _open_config(self, filename):
        if not os.path.exists(filename):
            return 0
        self.config.read(filename)

        for section in self.sections:
            if not self.config.has_section(section):
                msg = "config file does not have section: %s" % section
                raise ConfigError, msg
        return True

    def _store_password(self, password, path):
        datafile = os.path.join(path, "data")
        if os.path.exists(datafile):
            self.check_permissions(datafile, writable=True)
            os.remove(datafile)
        fd = open(datafile, "w")
        # obfuscate password to avoid it being easily identified when
        # editing file on screen. this is *NOT* encryption!
        text = binascii.b2a_base64(password)
        fd.write(text)
        fd.close()

    def _get_password(self, datafile):
        data = open(datafile).read()
        password = binascii.a2b_base64(data)
        return password

    def _check_installed_config_file(self):
        try:
            conf_file = environ.find_resource('config', self.filename)
        except EnvironmentError:
            return False
        return conf_file

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
            raise FilePermissionError, exception % origin

    def remove_config_file(self):
        self.check_permissions(self.home_filename)
        os.remove(self.home_filename)

    def get_homepath(self):
        return os.path.join(os.getenv('HOME'), '.' + self.domain)

    def has_installed_config_data(self):
        if (os.path.exists(self.home_filename) or
            self._check_installed_config_file()):
            return True
        return False

    def load_config(self):
        # Try to load configuration  from:
        # - $HOME/.$domain/$filename
        # - $PREFIX/share/$domain/$filename

        if self._open_config(self.home_filename):
            return

        installed_file = self._check_installed_config_file()
        if not installed_file:
            raise ConfigError("Could not find config file. You should "
                              "first call 'install_default' and supply "
                              "valid config information")

        if not self._open_config(installed_file):
            raise ConfigError("Could not open config file")

    @argcheck(DatabaseSettings)
    def install_default(self, config_data):
        path = self.get_homepath()
        if not os.path.exists(path):
            os.makedirs(path)
        else:
            os.chmod(path, 0700)

        password = config_data.password

        self._store_password(password, path)
        fd = open(os.path.join(path, self.filename), 'w')
        config_dict = dict(DOMAIN=self.domain, RDBMS=self.rdbms,
                           PORT=config_data.port,
                           ADDRESS=config_data.address,
                           DBNAME=config_data.dbname,
                           TESTDB=config_data.dbname,
                           DBUSERNAME=config_data.username)
        fd.write(self.config_template % config_dict)
        fd.close()

    def has_option(self, name, section='General'):
        return self.config.has_option(section, name)

    def get_option(self, name, section='General'):
        if not section in self.sections:
            raise  ConfigError, 'Invalid section: %s' % section

        if self.config.has_option(section, name):
            return self.config.get(section, name)

        raise NoConfigurationError, ('%s does not have option: %s' %
                                     (self.filename, name))

    def set_option(self, name, section='General'):
        if not section in self.sections:
            raise ConfigError, 'Invalid section: %s' % section

        self.config.set(section, name)

    def set_database(self, database):
        """
        Overrides the default database configuration option.
        @param database: the database
        """
        self.config.set('Database', 'dbname', database)

    def set_username(self, username):
        """
        Overrides the default username configuration option.
        @param username: the username
        """
        self.config.set('Database', 'dbusername', username)

    def set_hostname(self, hostname):
        """
        Overrides the default hostname configuration option.
        @param hostname: the hostname
        """
        self.config.set('Database', 'address', hostname)

    def set_port(self, port):
        """
        Overrides the default hostname configuration option.
        param port: the port
        """
        self.config.set('Database', 'port', port)

    def set_password(self, password):
        """
        Overrides the default hostname configuration option.
        @param password: the password
        """
        homepath = self.get_homepath()
        filename = os.path.join(homepath, self.filename)
        if os.path.exists(filename):
            path = homepath
        else:
            path = environ.get_resource_paths('config')[0]
        self._store_password(password, path)

    def raise_invalid_rdbms_settings(self):
        """Checks the stored database rdbms settings and raises ConfigError
        if something is wrong
        """
        try:
            conn_uri = self.get_connection_uri()
        except:
            type, value, trace = sys.exc_info()
            raise ConfigError(value)


    #
    # Database config accessors
    #

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
        if self._check_installed_config_file():
            try:
                data_file = environ.find_resource('config', self.datafile)
            except EnvironmentError:
                raise ConfigError('No config data set at this point')
        else:
            homepath = self.get_homepath()
            data_file = os.path.join(homepath, "data")
            if not os.path.exists(data_file):
                raise ConfigError('No config data set at this point')
        return self._get_password(data_file)

    def get_connection_uri(self):
        rdbms = self.get_rdbms_name()
        if self.test_mode:
            dbname = self.get_option('testdb', section='Database')
        else:
            dbname = self.get_option('dbname', section='Database')

        if self.has_option('dbusername', section='Database'):
            username = self.get_option('dbusername', section='Database')
        else:
            username = os.getlogin()
        return get_connection_uri(self.get_address(), self.get_port(),
                                  dbname, rdbms, username,
                                  self.get_password())


#
# General routines
#


@argcheck(StoqConfigParser)
def register_config(config):
    global _config
    _config = config

def get_config():
    global _config
    return _config
