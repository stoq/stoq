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

class SelectPrinter(Delegate):
    widgets = ['selectprinter', 'printer_brand', 'printer_model', 'cancel', 'ok']
    printers = {'sweda':['IFS9000I'],
                'bematech':['MP25'],
                'daruma':['FS345']}
    
    def __init__(self):
        Delegate.__init__(self, gladefile='selectprinter', 
                          delete_handler=self.close_cb)
                
        self.register_validate_function(self.validity)
        self.force_validation()
        
        self.printer_brand.prefill(self.printers.keys())
    
    def on_printer_brand__changed(self, combo):
        printer = combo.get_active_text()
        printer_model_list = self.printer_model.get_model()
        [printer_model_list.remove(printer_model_list.get_iter_root())
            for a in xrange(len(printer_model_list))]
        
        for m in self.printers[printer]:
            printer_model_list.append([m, None])
    
    def validity(self, valid):
        self.ok.set_sensitive(valid)
        
    def on_ok__clicked(self, button):
        self.close_cb()                        
    
    def on_cancel__clicked(self, button):
        self.close_cb()
    
    def close_cb(self, widget=None, extra=None):
        self.selectprinter.destroy()

if __name__ == '__main__':
    a = SelectPrinter()
    a.show_all()
    gtk.main()
