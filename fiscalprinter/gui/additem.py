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

from fiscalprinter.common import is_float
from fiscalprinter.drivers.interface import IFiscalPrinterDriver

class Item:
    code = ""
    quantity = 2.0
    price = 5.0
    description = ""
    percentage = 0.0
    unit = None
    taxcode = None

class AddItem(Delegate):
    widgets = ['additem', 'code', 'quantity', 'price', 'unit',
               'description', 'percentage', 'taxcode',
               'add', 'cancel', 'discount_type']
    
    disc_types = {'Discount':'-', 'Charge':'+'}
    
    def __init__(self, printer):
        Delegate.__init__(self, gladefile='additem', 
                          delete_handler=self.close_cb)
        
        self.quantity.set_data_format("%.3f")
        self.price.set_data_format("%.3f")
        self.percentage.set_data_format("%.3f")
        
        self.discount_type.prefill(self.disc_types.keys())
        
        self.register_validate_function(self.validity)
        self.force_validation()
        
        self.printer = printer
                 
        self.item = Item()
        
        self.proxy = self.add_proxy(self.item, ['code', 'quantity',
                                                'price', 'description',
                                                'unit', 'taxcode',
                                                'percentage'])

    def validity(self, valid):
        self.add.set_sensitive(valid)

    def on_add__clicked(self, button):
        if self.discount_type.get_active_text() == 'Discount':
            self.printer.add_item(self.item.code,
                                  self.item.quantity, self.item.price,
                                  self.item.unit, self.item.description,
                                  self.taxcode, self.item.percentage, 0.0)
        else:
            self.printer.add_item(self.item.code,
                                  self.item.quantity, self.item.price,
                                  self.item.unit, self.item.description,
                                  self.taxcode, 0.0, self.item.percentage)
        
        self.close_cb()
    
    def on_cancel__clicked(self, button):
        self.close_cb()
    
    def close_cb(self, widget=None, extra=None):
        self.additem.destroy()
