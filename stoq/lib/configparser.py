# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
"""
lib/configparser.py:

    Routines for parse the configuration file.
"""
    
import os
from ConfigParser import ConfigParser

from stoqlib.exceptions import (FilePermissionError, ConfigError,
                                NoConfigurationError)


class StoqConfigParser:
    config_template = \
"""
[General]
# Default file where status and errors are appended to. Comment this out
# to allow output to be sent to stderr/stdout
logfile=~/.%(DOMAIN)s/application.log

[Database]
# Choose here the relational database management system you would like to
# use. Available are: MySQL, PostgreSQL, SQLite, Firebird, Sybase, and 
# MAX DB (also known as SAP DB).
rdbms=%(RDBMS)s

# This is used by the client to find the server. 
address=%(ADDRESS)s

# The name of Stoq database in rdbms.
dbname=%(DBNAME)s

# The database username in rdbms.
dbusername=%(DBUSERNAME)s"""

    sections = ['General']

    def __init__(self, domain, filename=None, extra_sections=[]):
        """
        domain is the name given to the application system; it should
        be a name that describes the whole system, such as the company
        name. A domain will handle multiple applications

        filename is the name of the configuration file we're reading
        (the domain name suffixed with ".conf" is used otherwise)

        sections indicates extra sections that can be parsed from this
        configuration file.
        
        """

        if not filename:
            filename = domain + '.conf'
            
        self.domain = domain
        self.filename = filename
        
        if extra_sections:
            for section in extra_sections:
                self.sections.append(section)
                                     
        self.config = ConfigParser()
        self._load_config()

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
    
    def get_homepath(self):
        return os.path.join(os.getenv('HOME'), '.' + self.domain)

    def _load_config(self):
        # Try to load configuration  from:
        # 1) $HOME/.$domain/$filename
        # 2) $PREFIX/etc/$domain/$filename
        # 3) /etc/$filename
        
        # This is a bit hackish:
        # $prefix / lib / $DOMAIN / lib / config.py
        #    -4      -3     -2      -1       0
        filename = os.path.abspath(__file__)
        stripped = filename.split(os.sep)[:-4]
        self.prefix = os.path.join(os.sep, *stripped)
        
        homepath = self.get_homepath()
        etcpath = os.path.join(self.prefix, 'etc', self.domain)
        globetcpath = os.path.join(os.sep, 'etc', self.domain)
        if not (self._open_config(homepath) or
                self._open_config(etcpath) or
                self._open_config(globetcpath)):
            
            path = os.path.join(homepath, self.filename)
            assert not os.path.exists(path)

            self.install_default(homepath)
            
            assert self._open_config(homepath)

    def ask_configuration_data(self):
        print ("Adding configuration file for Stoq applications. "
               "\nYou can edit the file manually in $HOME/.stoq/stoq.conf")

        # XXX For now we only suport postgres. SQLObject also suports
        # firebird, mysql, sybase and sqllite but these databases are not
        # tested yet.
        rdbms = 'postgres'
            
        msg = _("What is the database address used by the client to "
                "find the server ? default is 'localhost'\naddress> ")
        address = raw_input(msg) or 'localhost'

        msg = _("What is the database name in the database system ? "
                "default is 'stoq'\ndatabase> ")
        dbname = raw_input(msg) or 'stoq'

        msg = _("What is the database username in the database system ? "
                "default is 'stoq'\nusername> ")
        dbusername = raw_input(msg) or 'stoq'

        return dict(DOMAIN=self.domain, RDBMS=rdbms,
                    ADDRESS=address, DBNAME=dbname,
                    DBUSERNAME=dbusername)

    def install_default(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
        else:
            os.chmod(path, 0700)

        config_data = self.ask_configuration_data()
        fd = open(os.path.join(path, self.filename), 'w')
        fd.write(self.config_template % config_data)
        fd.close()
        
    def _open_config(self, path):
        filename = os.path.join(path, self.filename)
        if not os.path.exists(filename):
            return 0
        self.config.read(filename)
        
        for section in self.sections:
            if not self.config.has_section(section):
                msg = "file does not have section: %s" % section
                raise ConfigError, msg
        return 1

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


        
    #
    # Database config accessors
    #



    def get_database_address(self):
        return self.get_option('address', section='Database')
        
    def get_rdbms_name(self):
        return self.get_option('rdbms', section='Database')

    def get_dbname(self):
        return self.get_option('dbname', section='Database')

    def get_dbusername(self):
        return self.get_option('dbusername', section='Database')


