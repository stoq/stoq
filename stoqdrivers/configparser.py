# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Stoqdrivers
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##
"""
Useful routines when parsing the configuration file
"""
import os
from ConfigParser import ConfigParser

from stoqdrivers.exceptions import ConfigError
from stoqdrivers.translation import stoqdrivers_gettext

_ = stoqdrivers_gettext

class StoqdriversConfig:

    domain = 'stoqdrivers'

    def __init__(self, filename=None):
        """ filename is the name of the configuration file we're reading """

        self.filename = filename or (self.domain + '.conf')
        self.config = ConfigParser()
        self._load_config()

    def get_homepath(self):
        return os.path.join(os.getenv('HOME'), '.' + self.domain)

    def _open_config(self, path):
        filename = os.path.join(path, self.filename)
        if not os.path.exists(filename):
            return False
        self.config.read(filename)
        return True

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
        if not (self._open_config(homepath) or self._open_config(etcpath) or
                self._open_config(globetcpath)):
            raise ConfigError(_("Config file not found in: `%s', `%s' and "
                                "`%s'") % (homepath, etcpath, globetcpath))

    def has_section(self, section):
        return self.config.has_section(section)

    def has_option(self, name, section='General'):
        return self.config.has_option(section, name)
    
    def get_option(self, name, section='General'):
        if not self.config.has_section(section):
            raise  ConfigError(_("Invalid section: %s") % section)
        elif not self.config.has_option(section, name):
            raise ConfigError(_("%s does not have option: %s")
                              % (self.filename, name))
        return self.config.get(section, name)

    def set_option(self, name, section='General'):
        if not self.config.has_section(section):
            raise ConfigError(_("Invalid section: %s") % section)
        self.config.set(section, name)
