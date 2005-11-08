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
fiscalprinter/bin/main.py:
    
    Main interface for fiscal printers management
"""

import gettext
import gtk
import os
import sys
from serial import SerialException

_ = gettext.gettext

from kiwi.environ import require_gazpacho, environ
require_gazpacho()

from kiwi.datatypes import ValidationError
from kiwi.ui.delegates import Delegate

from fiscalprinter.gui.additem import AddItem
from fiscalprinter.gui.cancelitem import CancelItem
from fiscalprinter.gui.totalize import TotalizeCoupon
from fiscalprinter.gui.selectprinter import SelectPrinter
from fiscalprinter.gui.setupprinter import SetupPrinter
from fiscalprinter.gui.about import About
from fiscalprinter.gui.opencoupon import OpenCoupon

from fiscalprinter.printer import FiscalPrinter
from fiscalprinter.log import Logger


#XXX
#this_dir = os.path.dirname(__file__)
#if os.path.exists(os.path.join(this_dir, "..", "..", "setup.py")):
#    environ.add_resource("glade", os.path.join(this_dir, "glade"))
#else:
#    environ.add_resource("glade", SYSTEM_GLADEPATH)

# Changed the code above to this:
this_dir = os.path.dirname(__file__)
environ.add_resource("glade", os.path.join(this_dir, "glade"))

class MainWindow(Delegate, Logger):
    widgets = ['summarize', 'cancel_coupon', 'open_coupon', 'add_item',
               'cancel_item', 'discount_charge_coupon', 'close_coupon',
               'totalize_coupon', 'Quit', 'select_printer',
               'setup_printer', 'about']
    
    def __init__(self):
        Delegate.__init__(self, gladefile='main',
                          delete_handler=self.quit_cb)
        Logger.__init__(self)

        try:self.printer = FiscalPrinter()
        except SerialException, e:
            critical_msg = _("Couldn't open serial device!")
            self.critical(critical_msg)
            
            dialog = gtk.MessageDialog(type=gtk.MESSAGE_WARNING,
                        buttons=gtk.BUTTONS_OK,
                        message_format=critical_msg)
            
            dialog.format_secondary_text(repr(e))
            dialog.run()
            dialog.destroy()
            
            # Uncomment while in prodution
            self.printer = None
            #sys.exit(1)
 
    def on_about__activate(self, action):
        about = About()
        about.show_all()
 
    def on_setup_printer__activate(self, action):
        setupprinter = SetupPrinter(self.printer)
        setupprinter.show_all()
 
    def on_select_printer__activate(self, action):
        selectprinter = SelectPrinter()
        selectprinter.show_all()
 
    def on_summarize__activate(self, action):
        IFiscalPrinterDriver.summarize()
    
    def on_cancel_coupon__activate(self, action):
        IFiscalPrinterDriver.cancel_coupon()
    
    def on_open_coupon__activate(self, action):
        opencoupon = OpenCoupon(self.printer)
        opencoupon.show_all()
    
    def on_add_item__activate(self, action):
        additem = AddItem(self.printer)
        additem.show_all()
    
    def on_cancel_item__activate(self, action):
        cancelitem = CancelItem(self.printer)
        cancelitem.show_all()
    
    def on_discount_charge_coupon__activate(self, action):
        IFiscalPrinterDriver.coupon_add_charge(0,0,0)
    
    def on_close_coupon__activate(self, action):
        IFiscalPrinterDriver.close_coupon()
    
    def on_totalize_coupon__activate(self, action):
        totalize = TotalizeCoupon(self.printer)
        totalize.show_all()
    
    def quit_cb(self, widget=None, extra=None):
        gtk.main_quit()
    
    def on_Quit__activate(self, action):
        self.quit_cb()

if __name__ == '__main__':
    m = MainWindow()
    m.show_all()
    gtk.main()
