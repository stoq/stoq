# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
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
##
"""
stoqdrivers/configparser.py:

    Useful routines when parsing the configuration file
"""
    
import os
import gettext
from ConfigParser import ConfigParser

from stoqdrivers.exceptions import ConfigError

_ = gettext.gettext


class FiscalPrinterConfig:
    config_template = \
"""
[General]
# Default file where status and errors are appended to. Comment this out
# to allow output to be sent to stderr/stdout
logfile=~/.fiscalprinter/application.log

[Printer]
# Choose here the fiscal printer brand you would like to
# use. Available are: sweda, bematech, daruma
brand=%(BRAND)s

# The fiscal printer model. Avaliable models are:
#   sweda       = IFS9000I
#   bematech    = MP25
#   daruma      = FS345, FS2100, FS600MFD
model=%(MODEL)s

# Device type which has been used for the printer: serial or network
devicetype=%(DEVICETYPE)s

[Serial]
# The device where the printer is connected to...
device=%(DEVICE)s

#... or the baudrate
baudrate=%(BAUDRATE)s


[Network]
# Port...
port=%(PORT)s

#... or the host where it can be found
host=%(HOST)s
"""


    sections = ['General', 'Printer', 'Serial', 'Network']
    domain = 'fiscalprinter'

    def __init__(self, filename=None):
        """
        filename is the name of the configuration file we're reading
        (the "fiscalprinter.conf" is used otherwise) """

        if not filename:
            filename = self.domain + '.conf'
            
        self.filename = filename
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
            raise OSError(exception % origin)
    
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
        print ("Adding configuration file for Fiscal Printer."
               "\nYou can edit the file manually in"
               "\n$HOME/.fiscalprinter/fiscalprinter.conf")

        msg = _("What is the fiscal printer brand you have connected "
                "on your computer ? default is 'sweda'\nbrand> ")
        brand = raw_input(msg) or 'sweda'

        msg = _("What is the fiscal printer model ?"
                "default is 'IFS9000I'\nmodel> ")
        model = raw_input(msg) or 'IFS9000I'

        msg = _("What is the device-type for the printer?"
                "default is 'serial'. Available options are:\n"
                "serial, network' '\ndevice-type> ")
        devicetype= raw_input(msg) or 'serial'

        if devicetype == 'serial':
            host = ''
            port = ''
            msg = _("What is the device where the fiscal printer is "
                    "connected to ? default is '/dev/ttyS0'\ndevice> ")
            device = raw_input(msg) or '/dev/ttyS0'
            msg = _("What is the baudrate number which your fiscal printer "
                    "is connected to? default is '9600'\nbaudrate> ")
            baudrate = raw_input(msg) or '9600'
        elif devicetype == 'network':
            device = ''
            baudrate = ''
            msg = _("What is the host where the printer can "
                    "be found ? default is 'localhost'\nhost> ")
            host = raw_input(msg) or 'localhost'
            msg = _("What is the port number which your fiscal printer "
                    "is connected to? default is '4000'\nport> ")
            port = raw_input(msg) or '4000'
            return dict(BRAND=brand, DEVICETYPE=devicetype,
                        MODEL=model, HOST=host,
                        PORT=port)
        else:
            raise ConfigError('Invalid option for device-type %s'
                              % devicetype)
        return dict(BRAND=brand, DEVICETYPE=devicetype,
                    MODEL=model, DEVICE=device,
                    BAUDRATE=baudrate, HOST=host, PORT=port)

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
        return True

    def has_option(self, name, section='General'):
        return self.config.has_option(section, name)
    
    def get_option(self, name, section='General'):
        if not section in self.sections:
            raise  ConfigError, 'Invalid section: %s' % section
        
        if self.config.has_option(section, name):
            return self.config.get(section, name)

        raise ConfigError('%s does not have option: %s' % 
                          (self.filename, name))

    def set_option(self, name, section='General'):
        if not section in self.sections:
            raise ConfigError, 'Invalid section: %s' % section
        self.config.set(section, name)


        
    #
    # Config accessors
    #



    def get_brand(self):
        return self.get_option('brand', section='Printer')
        
    def get_model(self):
        return self.get_option('model', section='Printer')

    def get_devicetype(self):
        return self.get_option('devicetype', section='Printer')

    def get_device(self):
        return self.get_option('device', section='Serial')

    def get_baudrate(self):
        return self.get_option('baudrate', section='Serial')

    def get_port(self):
        return self.get_option('port', section='Network')

    def get_host(self):
        return self.get_option('host', section='Network')
