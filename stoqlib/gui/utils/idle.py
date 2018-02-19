# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013-2018 Async Open Source
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

"""
This modules has one function :func:`get_idle_seconds` that returns
the number of the seconds since the user has used the keyboard or mouse.
"""

from gi.repository import Gtk, Gdk, GLib


class IdleEventHandler(object):
    def __init__(self):
        Gdk.event_handler_set(self._filter_callback)
        GLib.timeout_add_seconds(1, self._increase_idle)
        self._idle = 0

    def _filter_callback(self, event):
        if event.type in [Gdk.EventType.BUTTON_PRESS,
                          Gdk.EventType.BUTTON_RELEASE,
                          Gdk.EventType.KEY_PRESS,
                          Gdk.EventType.KEY_RELEASE,
                          Gdk.EventType.MOTION_NOTIFY,
                          Gdk.EventType.SCROLL]:
            self._idle = 0
        Gtk.main_do_event(event)

    def _increase_idle(self):
        self._idle += 1
        return True

    def get_idle(self):
        return self._idle


_idle = None


def get_idle_seconds():
    """
    Returns the number of seconds the current user has been idle.

    :returns: idle seconds
    :rtype: int
    """
    global _idle
    if _idle is None:
        _idle = IdleEventHandler()
    return _idle.get_idle()
