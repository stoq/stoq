# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
##
##
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##
""" Base classes for applications """

import gtk
from kiwi.ui.delegates import Delegate

from stoqlib.gui.base.dialogs import get_dialog, run_dialog


#
# Expects a main window class, which takes one argument: the app (for
# shutdown purposes)
#


class BaseApp:
    """ Base class for application control. """
    def __init__(self, main_window_class):
        # The self should be passed to main_window to let it access
        # shutdown and do_sync methods.
        self.main_window = main_window_class(self)

    def run(self):
        self.main_window.show()

    def shutdown(self, *args):
        gtk.main_quit()



#
# Expects an app, with app.shutdown available as a handler
#

class BaseAppWindow(Delegate):
    """ Class to be inherited by applications main window.  """
    gladefile = toplevel_name = ''

    def __init__(self, app, keyactions=None):
        Delegate.__init__(self, delete_handler=app.shutdown, 
                          keyactions=keyactions, widgets=self.widgets,
                          gladefile=self.gladefile,
                          toplevel_name=self.toplevel_name)

    def set_sensitive(self, widgets, value):
        """Sets one or more widgets to state sensitive. XXX: Kiwi?"""
        for widget in widgets:
            widget.set_sensitive(value)

    def get_dialog(self, dialog_class, *args, **kwargs):
        """ Encapsuled method for getting dialogs. """
        return get_dialog(self, dialog_class, *args, **kwargs)

    def run_dialog(self, dialog_class, *args, **kwargs):
        """ Encapsuled method for running dialogs. """
        return run_dialog(dialog_class, self, *args, **kwargs)

