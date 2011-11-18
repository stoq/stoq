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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Base classes for applications """

import gtk
from kiwi.ui.delegates import GladeDelegate
from twisted.internet import reactor

from stoqlib.gui.base.dialogs import (get_dialog, run_dialog,
                                      add_current_toplevel)


#
# Expects a main window class, which takes one argument: the app (for
# shutdown purposes)
#


class BaseApp:
    """ Base class for application control. """
    def __init__(self, main_window_class):
        """
        Create a new object BaseApp.
        @param main_window_class: A BaseAppWindow subclass
        """
        if not issubclass(main_window_class, BaseAppWindow):
            raise TypeError
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
        if reactor.running:
            reactor.stop()



#
# Expects an app, with app.shutdown available as a handler
#

class BaseAppWindow(GladeDelegate):
    """ Class to be inherited by applications main window.  """
    gladefile = toplevel_name = ''
    title = ''
    size = ()

    def __init__(self, app, keyactions=None):
        self._sensitive_group = dict()
        self.app = app
        GladeDelegate.__init__(self, delete_handler=self._on_delete_handler,
                          keyactions=keyactions,
                          gladefile=self.gladefile,
                          toplevel_name=self.toplevel_name)
        toplevel = self.get_toplevel()
        add_current_toplevel(toplevel)
        if self.size:
            toplevel.set_size_request(*self.size)
        toplevel.set_title(self.get_title())

    def key_control_F11(self):
        self.toggle_fullscreen()

    def toggle_fullscreen(self):
        window = self.get_toplevel()
        if window.window.get_state() & gtk.gdk.WINDOW_STATE_FULLSCREEN:
            window.unfullscreen()
        else:
            window.fullscreen()

    def get_title(self):
        """This method must be overwritten on child when it's needed"""
        return self.title

    def set_sensitive(self, widgets, value):
        """Set the C{widgets} sensitivity based on C{value}

        @note: if a sensitive group was registered for any widget,
            it's validation function will be tested and, if C{False}
            is returned, it will be set insensitive, ignoring C{value}

        @param widgets: a L{list} of widgets
        @param value: either C{True} or C{False}
        """
        # FIXME: Maybe this should ne done on kiwi?
        for widget in widgets:
            sensitive = value

            for validator in self._sensitive_group.get(widget, []):
                if not validator[0](*validator[1]):
                    sensitive = False
                    break

            widget.set_sensitive(sensitive)

    def register_sensitive_group(self, widgets, validation_func, *args):
        """Register widgets on a sensitive group.

        Everytime self.set_sensitive() is called, if there is any
        validation function for a given widget on sensitive group,
        then that will be used to decide if it gets sensitive or
        insensitive.

        @param widgets: a L{list} of widgets
        @param validation_func: a function for validation. It should
            return either C{True} or C{False}.
        @param args: args that will be passed to C{validation_func}
        """
        assert callable(validation_func)

        for widget in widgets:
            validators = self._sensitive_group.setdefault(widget, set())
            validators.add((validation_func, args))

    def get_dialog(self, dialog_class, *args, **kwargs):
        """ Encapsuled method for getting dialogs. """
        return get_dialog(self, dialog_class, *args, **kwargs)

    def run_dialog(self, dialog_class, *args, **kwargs):
        """ Encapsuled method for running dialogs. """
        return run_dialog(dialog_class, self, *args, **kwargs)

    def shutdown_application(self, *args):
        self.app.shutdown()

    #
    # Callbacks
    #

    def _on_delete_handler(self, *args):
        self.shutdown_application()

    def _on_quit_action__clicked(self, *args):
        self.shutdown_application()
