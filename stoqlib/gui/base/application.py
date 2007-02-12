# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##
""" Base classes for applications """

import gtk
from kiwi.ui.delegates import GladeDelegate
from kiwi.argcheck import argcheck

from stoqlib.gui.base.dialogs import (get_dialog, run_dialog,
                                      add_current_toplevel)


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
        self.show()

    def hide(self):
        self.main_window.hide()

    def show(self):
        self.main_window.show()

    def shutdown(self, *args):
        gtk.main_quit()



#
# Expects an app, with app.shutdown available as a handler
#

class BaseAppWindow(GladeDelegate):
    """ Class to be inherited by applications main window.  """
    gladefile = toplevel_name = ''
    title = ''
    size = ()

    @argcheck(BaseApp, object)
    def __init__(self, app, keyactions=None):
        self.app = app
        GladeDelegate.__init__(self, delete_handler=app.shutdown,
                          keyactions=keyactions,
                          gladefile=self.gladefile,
                          toplevel_name=self.toplevel_name)
        toplevel = self.get_toplevel()
        add_current_toplevel(toplevel)
        if self.size:
            toplevel.set_size_request(*self.size)
        toplevel.set_title(self.get_title())

        # As of Gtk+ 2.8, the proper way to track this is using
        # window-state-event, we skip that and assume the window
        # is not made fullscreen by any other means
        self._is_fullscreen = False

    def key_control_F11(self):
        window = self.get_toplevel()
        if self._is_fullscreen:
            window.unfullscreen()
        else:
            window.fullscreen()
        self._is_fullscreen = not self._is_fullscreen

    def get_title(self):
        """This method must be overwritten on child when it's needed"""
        return self.title

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

    #
    # Callbacks
    #

    def _on_quit_action__clicked(self, *args):
        self.app.shutdown()
