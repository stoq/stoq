# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2011 Async Open Source
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""Routines for parsing the configuration file"""

import binascii
from ConfigParser import SafeConfigParser
import os

from stoqlib.lib.interfaces import IStoqConfig
from stoqlib.lib.osutils import get_application_dir
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.exceptions import (FilePermissionError,
                                NoConfigurationError)

_config = None


class StoqConfig:
    domain = 'stoq'

    def __init__(self):
        self._config = SafeConfigParser()
        self._settings = None
        self.filename = None

    def _get_config_file(self):
        filename = self.domain + '.conf'
        configdir = self.get_config_directory()
        return os.path.join(configdir, filename)

    def _open_config(self, filename):
        if not os.path.exists(filename):
            return False
        self._config.read(filename)
        return True

    #
    # Public API
    #

    def create(self):
        config_dir = self.get_config_directory()
        if not os.path.exists(config_dir):
            os.mkdir(config_dir)
        self.filename = os.path.join(
            config_dir, StoqConfig.domain + '.conf')

    def load_default(self):
        """
        Loads default configuration file one will be loaded
        """
        self.filename = self._get_config_file()
        self.load(self.filename)

    def load(self, filename):
        """
        Loads the data from a configuration file
        :param filename: filename
        """
        if not filename:
            raise TypeError("Missing filename option")
        if not self._open_config(filename):
            return
        self.filename = filename

    def load_settings(self, settings):
        """
        Load data from a DatabaseSettings object
        :param settings: the settings object
        """

        self.set('General', 'logfile',
                 os.path.join(get_application_dir(StoqConfig.domain),
                              'application.log'))
        self.set('Database', 'rdbms', settings.rdbms)
        self.set('Database', 'address', settings.address)
        self.set('Database', 'port', str(settings.port))
        self.set('Database', 'dbname', settings.dbname)
        self.set('Database', 'dbusername', settings.username)
        if settings.password:
            self.store_password(settings.password)
        self._settings = settings

    def flush(self):
        """
        Writes the current configuration data to disk.
        """
        if not self.filename:
            self.filename = self._get_config_file()

        with open(self.filename, 'w') as f:
            self._config.write(f)

    def get_filename(self):
        config_dir = self.get_config_directory()
        return os.path.join(config_dir, 'stoq.conf')

    def get_config_directory(self):
        return os.path.join(get_application_dir(self.domain))

    def store_password(self, password):
        configdir = self.get_config_directory()
        datafile = os.path.join(configdir, 'data')
        if not os.path.exists(datafile):
            if not os.path.exists(configdir):
                try:
                    os.makedirs(configdir)
                    os.chmod(configdir, 0700)
                except OSError as e:
                    if e.errno == 13:
                        raise FilePermissionError(
                            "Could not " % configdir)
                    raise

        try:
            fd = open(datafile, "w")
        except OSError as e:
            if e.errno == 13:
                raise FilePermissionError("%s is not writable" % datafile)
            raise

        # obfuscate password to avoid it being easily identified when
        # editing file on screen. this is *NOT* encryption!
        fd.write(binascii.b2a_base64(password))
        fd.close()

    def get_settings(self):
        if self._settings:
            return self._settings

        rdbms = self.get('Database', 'rdbms')
        address = self.get('Database', 'address')
        dbname = self.get('Database', 'dbname')
        username = self.get('Database', 'dbusername')
        port = self.get('Database', 'port')
        if port:
            port = int(port)

        database_section = self.get('General', 'database_section')
        if database_section is not None:
            rdbms = self.get(database_section, 'rdbms') or rdbms
            address = self.get(database_section, 'address') or address
            dbname = self.get(database_section, 'dbname') or dbname
            username = self.get(database_section, 'dbusername') or username
            port = self.get(database_section, 'port') or port

        # FIXME: This and load_settings() needs to be simplified now when
        #        we only have one global settings singleton
        from stoqlib.database.settings import db_settings
        db_settings.rdbms = rdbms or db_settings.rdbms
        db_settings.address = address or db_settings.address
        db_settings.port = port or db_settings.port
        db_settings.dbname = dbname or db_settings.dbname
        db_settings.username = username or db_settings.username
        db_settings.password = db_settings.password
        return db_settings

    def set_from_options(self, options):
        """
        Updates the configuration given a values instance
        :param options: a optparse.Values instance
        """

        from stoqlib.database.settings import db_settings
        if options.address:
            self.set('Database', 'address', options.address)
            db_settings.address = options.address
        if options.port:
            self.set('Database', 'port', options.port)
            db_settings.port = options.port
        if options.dbname:
            self.set('Database', 'dbname', options.dbname)
            db_settings.dbname = options.dbname
        if options.username:
            self.set('Database', 'dbusername', options.username)
            db_settings.username = options.username
        if options.password:
            self.store_password(options.password)

    def set(self, section, option, value):
        if not self.has_section(section):
            self._config.add_section(section)

        self._config.set(section, option, value)

    def get(self, section, option):
        if not self.has_section(section):
            return

        if not self._config.has_option(section, option):
            return

        return self._config.get(section, option)

    def remove(self, section, option):
        if self.has_section(section):
            self._config.remove_option(section, option)

    def remove_section(self, section):
        self._config.remove_section(section)

    def has_section(self, section):
        return self._config.has_section(section)

    def items(self, section):
        if not self.has_section(section):
            return []
        return self._config.items(section)

#
# General routines
#


def register_config(config):
    from kiwi.component import provide_utility
    global _config
    _config = config

    try:
        provide_utility(IStoqConfig, config, replace=True)
    except NoConfigurationError:
        msg = _(u"Error: Stoq configuration is not avaiable. Check that the "
                "current user has a configuration file (~/.stoq/stoq.conf).")
        if os.geteuid() == 0:
            msg += _('\n\nYou are running stoq using sudo. That is not '
                     'recommended.')
        raise SystemExit(msg)


def get_config():
    return _config
