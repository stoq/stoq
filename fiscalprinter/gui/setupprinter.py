# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Fiscal Printer
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
## Author(s):   Adriano Monteiro        <adriano@globalred.com.br>
##
"""
fiscalprinter/gui/additem.py:
    
    Window to add an item on an open coupon
"""

import gettext
import gtk
import os

_ = gettext.gettext

from kiwi.environ import require_gazpacho, environ
require_gazpacho()

from kiwi.datatypes import ValidationError
from kiwi.ui.delegates import Delegate

from fiscalprinter.configparser import FiscalPrinterConfig

class SetupPrinter(Delegate):
    widgets = ['setupprinter', 'device_type', 'device_host', 'cancel', 'ok',
               'baudrate_port', 'device_host_label', 'baudrate_port_label']
    
    setup_data = {'Serial':{'device_host_label':'Device:',
                            'baudrate_port_label':'Baudrate:',
                            'device_host':gtk.ListStore(str),
                            'baudrate_port':gtk.ListStore(str)},
                                              
                  'Network':{'device_host_label':'Host:',
                             'baudrate_port_label':'Port:',
                             'device_host':gtk.ListStore(str),
                             'baudrate_port':gtk.ListStore(str)}}
    
    def __init__(self, printer):
        Delegate.__init__(self, gladefile='setupprinter',
                          delete_handler=self.close_cb)
        
        self.device_type.prefill(self.setup_data.keys())
        
        for i in xrange(5):
            self.setup_data['Serial']['device_host'].append(['ttyS%d'%i])
        for i in xrange(1, 13):
            self.setup_data['Serial']['baudrate_port'].append(['%d'%(i*9600)])

        self.register_validate_function(self.validity)
        self.force_validation()
        
        self.printer = printer
        self.config = FiscalPrinterConfig()
    
    def validity(self, valid):
        self.ok.set_sensitive(valid)
    
    def on_device_type__changed(self, combo):
        device_dict = self.setup_data[combo.get_active_text()]
        device_host_list = self.device_host.get_model()
        baudrate_port_list = self.baudrate_port.get_model()
        
        self.device_host_label.set_label(device_dict['device_host_label'])
        self.baudrate_port_label.set_label(device_dict['baudrate_port_label'])
        
        self.device_host.set_model(device_dict['device_host'])
        self.baudrate_port.set_model(device_dict['baudrate_port'])
        
    def on_ok__clicked(self, button):
        device_type = self.devicetype.get_active_text()
        self.config.set_option('devicetype', device_type, 'Printer')
        if device_type == 'Serial':
            self.config.set_option('device', 
                               self.device_host.child.get_text(), 'Serial')
            self.config.set_option('baudrate',
                               self.baudrate_port.child.get_text(), 'Serial')
        else:
            self.config.set_option('host', 
                               self.device_host.child.get_text(), 'Network')
            self.config.set_option('port',
                               self.baudrate_port.child.get_text(), 'Network')
        
        self.printer._load_configuration(None)
        
        self.close_cb()
    
    def on_cancel__clicked(self, button):
        self.close_cb()
    
    def close_cb(self, widget=None, extra=None):
        self.setupprinter.destroy()

if __name__ == '__main__':
    a = SetupPrinter()
    a.show_all()
    gtk.main()
