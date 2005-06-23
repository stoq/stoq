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
gui/application.py:

    Base classes for applications
"""

import gtk
import gobject

from Kiwi2 import initgtk 
from Kiwi2 import Delegates 

from stoqlib.gui import dialogs 


#
# Expects a main window class, which takes one argument: the app (for
# shutdown purposes)
#


class BaseApp:
    """ Base class for application control. """
    def __init__(self, main_window_class, sync_time=10000):
        # The self should be passed to main_window to let it access
        # shutdown and do_sync methods.
        self.main_window = main_window_class(self)
        gobject.timeout_add(sync_time, self.do_sync)

    def run(self):
        self.main_window.show()

    def shutdown(self, *args):
        gtk.main_quit()

    def do_sync(self, *args):
        if hasattr(self.main_window, 'sync'):
            self.main_window.sync()
        return True


#
# Expects an app, with app.shutdown available as a handler
#

class BaseAppWindow(Delegates.Delegate):
    """ Class to be inherited by applications main window.  """
    gladefile = toplevel_name = ''
    widgets = ()
    def __init__(self, app, keyactions=None):
        Delegates.Delegate.__init__(self, delete_handler=app.shutdown,
                                    keyactions=keyactions, 
                                    widgets=self.widgets,
                                    gladefile=self.gladefile,
                                    toplevel_name=self.toplevel_name)

    def set_sensitive(self, widgets, value):
        """Sets one or more widgets to state sensitive. XXX: Kiwi?"""
        for widget in widgets:
            widget.set_sensitive(value)

    def get_dialog(self, dialog_class, *args, **kwargs):
        """ Encapsuled method for getting dialogs. """
        return dialogs.get_dialog(self, dialog_class, *args, **kwargs)

    def run_dialog(self, dialog_class, *args, **kwargs):
        """ Encapsuled method for running dialogs. """
        return dialogs.run_dialog(dialog_class, self, *args, **kwargs)

