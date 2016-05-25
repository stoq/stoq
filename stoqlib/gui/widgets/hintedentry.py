# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011-2013 Async Open Source
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

import gobject
import gtk
from kiwi.ui.entry import KiwiEntry

# Ported from evolution
# Replace with GtkEntry::placeholder-text in Gtk 3.2


class HintedEntry(KiwiEntry):
    __gtype_name__ = 'HintedEntry'

    def __init__(self):
        super(HintedEntry, self).__init__()
        self._hint_shown = False
        self._hint = None

    def set_hint(self, text):
        self._hint = text
        if self._hint_shown:
            gtk.Entry.set_text(self, text)

    def set_text(self, text):
        if not text and not self.has_focus():
            self.show_hint()
        else:
            self.show_text(text)

    def get_text(self):
        if self._hint_shown:
            return ""
        return super(HintedEntry, self).get_text()

    def show_hint(self):
        self._hint_shown = True
        super(HintedEntry, self).set_text(self._hint)
        self.modify_text(gtk.STATE_NORMAL,
                         self.get_style().text[gtk.STATE_INSENSITIVE])

    def show_text(self, text):
        self._hint_shown = False
        super(HintedEntry, self).set_text(text)
        self.modify_text(gtk.STATE_NORMAL, None)

    def do_grab_focus(self):
        if self._hint_shown:
            # Why do we have to do_grab_focus from gtk.Widget here?
            return gtk.Widget.do_grab_focus(self)
        else:
            return KiwiEntry.do_grab_focus(self)

    def do_focus_in_event(self, event):
        if self._hint_shown:
            self.show_text("")
        return KiwiEntry.do_focus_in_event(self, event)

    def do_focus_out_event(self, event):
        text = self.get_text()
        if not text:
            self.show_hint()
        return KiwiEntry.do_focus_out_event(self, event)


gobject.type_register(HintedEntry)
