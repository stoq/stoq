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

class Totalize:
    discount = None
    charge = None
    taxcode = None

class TotalizeCoupon(Delegate):
    widgets = ['totalize', 'discount', 'charge', 'taxcode', 'cancel', 'ok']
    
    def __init__(self, printer):
        Delegate.__init__(self, gladefile='totalize', 
                          delete_handler=self.close_cb)
        
        self.discount.set_data_format('%.3f')
        self.charge.set_data_format('%.3f')
        
        self.register_validate_function(self.validity)
        self.force_validation ()
        
        self.printer = printer
        
        self.tlz = Totalize()
        
        self.proxy = self.add_proxy(self.tlz, ['discount', 'charge',
                                               'taxcode'])

    def validity(self, valid):
        self.ok.set_sensitive(valid)
        
    def on_ok__clicked(self, button):
        self.printer.totalize(self.tlz.discount,
                              self.tlz.charge,
                              self.tlz.taxcode)
        self.close_cb()                        
    
    def on_cancel__clicked(self, button):
        self.close_cb()
    
    def close_cb(self, widget=None, extra=None):
        self.totalize.destroy()

if __name__ == '__main__':
    a = TotalizeCoupon()
    a.show_all()
    gtk.main()
