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

#XXX
this_dir = os.path.dirname(__file__)
if os.path.exists(os.path.join(this_dir, "..", "..", "setup.py")):
    environ.add_resource("glade", os.path.join(this_dir, "glade"))
else:
    environ.add_resource("glade", SYSTEM_GLADEPATH)


class About(Delegate):
    widgets = ['about', 'logo', 'license', 'credits', 'close']
    
    def __init__(self):
        Delegate.__init__(self, gladefile='about', 
                          delete_handler=self.close_cb)
        
        self.logo.set_from_file(environ.find_resource('glade','logo.png'))
    
    def on_credits__clicked(self, button):
        self.credits_window = Credits()
        self.credits_window.show_all()
    
    def on_license__clicked(self, button):
        self.license_window = License()
        self.license_window.show_all()
    
    def on_close__clicked(self, button):
        self.close_cb()
    
    def close_cb(self, widget=None, extra=None):
        self.about.destroy()

class CreditsContent:
    written_by = """Adriano Monteiro Marques <adriano@globalred.com.br>
Christian Robottom Reis <kiko@async.com.br>
Cleber Rodrigues Rosa Júnior <cleber@globalred.com.br>
Evandro Vale Miquelito <evandro@async.com.br>
Johan Dahlin <jdahlin@async.com.br>"""

class Credits(Delegate):
    widgets = ['credits', 'close', 'written_by']
    
    def __init__(self):
        Delegate.__init__(self, gladefile='credits', 
                          delete_handler=self.close_cb)
        
        self.contents = CreditsContent()
        self.proxy = self.add_proxy(self.contents, ['written_by'])

    def on_close__clicked(self, button):
        self.close_cb()

    def close_cb(self, widget=None, extra=None):
        self.credits.destroy()

class LicenseContent:
    license_text = """Fiscal Printer
Copyright (C) 2005 Async Open Source <http://www.async.com.br>
All rights reserved

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
USA.

Authors: Adriano Monteiro Marques <adriano@globalred.com.br>
         Christian Robottom Reis <kiko@async.com.br>
         Cleber Rodrigues Rosa Júnior <cleber@globalred.com.br>
         Evandro Vale Miquelito <evandro@async.com.br>
         Johan Dahlin <jdahlin@async.com.br>"""

class License(Delegate):
    widgets = ['license', 'close', 'license_text']
    
    def __init__(self):
        Delegate.__init__(self, gladefile='license', 
                          delete_handler=self.close_cb)
        
        self.contents = LicenseContent()
        self.proxy = self.add_proxy(self.contents, ['license_text'])

    def on_close__clicked(self, button):
        self.close_cb()

    def close_cb(self, widget=None, extra=None):
        self.license.destroy()


if __name__ == '__main__':
    a = About()
    a.show_all()
    gtk.main()
