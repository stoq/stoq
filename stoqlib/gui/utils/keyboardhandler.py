# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

"""Global keyboard handling.

This module allows you to install a callback which will be called
for all toplevel windows
"""

import gtk
from kiwi.ui.test.recorder import add_emission_hook


class _KeyboardHandler(object):
    def __init__(self):
        self._hooks = {}

    def _on_window_key_press_event(self, window, event):
        if isinstance(window, gtk.Window):
            callback = self._hooks.get(event.keyval, None)
            if callback:
                callback(window)
        return True

    def add_hook(self, keyval, callback):
        # Nothing to do if we can't add emission hooks
        if not add_emission_hook:
            return

        if not self._hooks:
            add_emission_hook(gtk.Window, 'key-press-event',
                              self._on_window_key_press_event)

        self._hooks[keyval] = callback

_handler = _KeyboardHandler()


def install_global_keyhandler(keyval, callback):
    """ Installs a new key handler.
    :param keyval:
    :param callback:
    """
    _handler.add_hook(keyval, callback)
