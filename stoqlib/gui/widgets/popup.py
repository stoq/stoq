# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2015 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

import gtk


class EntryPopup(gtk.Window):
    """A generic popup for entries."""

    def __init__(self, entry):
        self.entry = entry
        super(EntryPopup, self).__init__(gtk.WINDOW_POPUP)
        self._setup()

    #
    # Public API
    #

    def confirm(self):
        """Confirm the popup.

        Called when the user activates the popup.
        Subclasses can override this to do something when that happens
        """

    def get_main_widget(self):
        """Get the main widget to attach on the popup.

        Should return a gtk.Widget to be attached inside the popup.

        :return: a gtk.Widget
        """
        raise NotImplementedError

    def validate_popup(self):
        """Check if we can popup or not."""
        return True

    def popup(self):
        """Display the popup."""
        if not self.entry.get_realized():
            return

        if not self.validate_popup():
            return

        toplevel = self.entry.get_toplevel().get_toplevel()
        if (isinstance(toplevel, (gtk.Window, gtk.Dialog)) and
                toplevel.get_group()):
            toplevel.get_group().add_window(self)

        # width is meant for the popup window
        x, y, width, height = self._get_position()
        self.set_size_request(width, -1)
        self.move(x, y)
        self.show_all()

        if not self._popup_grab_window():
            self.hide()
            return

        self.grab_add()

    def popdown(self):
        """Hide the popup."""
        if not self.entry.get_realized():
            return

        self.grab_remove()
        self.hide()
        self.entry.grab_focus()

    #
    #  Private
    #

    def _setup(self):
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.KEY_PRESS_MASK)
        self.connect('key-press-event', self._on__key_press_event)
        self.connect('button-press-event', self._on__button_press_event)

        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
        self.add(frame)
        frame.show()

        alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        alignment.set_padding(6, 6, 2, 2)
        frame.add(alignment)
        alignment.show()

        alignment.add(self.get_main_widget())

        self.set_resizable(False)
        self.set_screen(self.entry.get_screen())

    def _popup_grab_window(self):
        activate_time = 0L
        window = self.get_window()
        grab_status = gtk.gdk.pointer_grab(window, True,
                                           (gtk.gdk.BUTTON_PRESS_MASK |
                                            gtk.gdk.BUTTON_RELEASE_MASK |
                                            gtk.gdk.POINTER_MOTION_MASK),
                                           None, None, activate_time)
        if grab_status == gtk.gdk.GRAB_SUCCESS:
            if gtk.gdk.keyboard_grab(window, True, activate_time) == 0:
                return True
            else:
                window.get_display().pointer_ungrab(activate_time)
                return False

        return False

    def _get_position(self):
        allocation = self.entry.get_allocation()
        window = self.entry.get_window()

        if hasattr(window, 'get_root_coords'):
            x, y = 0, 0
            if not self.entry.get_has_window():
                x += allocation.x
                y += allocation.y
            x, y = window.get_root_coords(x, y)
        else:
            # PyGTK lacks gdk_window_get_root_coords(),
            # but we can use get_origin() instead, which is the
            # same thing in our case.
            x, y = self.entry.window.get_origin()

        return x, y + allocation.height, allocation.width, allocation.height

    #
    #  Callbacks
    #

    def _on__key_press_event(self, window, event):
        keyval = event.keyval
        if keyval == gtk.keysyms.Escape:
            self.popdown()
            return True
        elif keyval in [gtk.keysyms.Return,
                        gtk.keysyms.KP_Enter,
                        gtk.keysyms.Tab]:
            self.confirm()
            return True

        return False

    def _on__button_press_event(self, window, event):
        # If we're clicking outside of the window
        # close the popup
        if (event.window != self.get_window() or
            (tuple(self.allocation.intersect(
                   gtk.gdk.Rectangle(x=int(event.x), y=int(event.y),
                                     width=1, height=1)))) == (0, 0, 0, 0)):
            self.popdown()
