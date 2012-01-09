# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

import gtk

from kiwi.ui.objectlist import ObjectList
from kiwi.ui.widgets.list import Column

from stoqlib.api import api
from stoqlib.gui.base.dialogs import BasicDialog
from stoqlib.gui.keybindings import get_bindings
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class ShortcutsEditor(BasicDialog):
    size = (500, 400)
    title = _("Keyboard shortcuts")

    def __init__(self, conn):
        BasicDialog.__init__(self)
        self._initialize(size=ShortcutsEditor.size, title=ShortcutsEditor.title)
        self._create_ui()

    def _create_ui(self):
        self.cancel_button.hide()
        box = gtk.VBox()
        self.shortcuts = ObjectList(self._get_columns(), get_bindings(),
                                gtk.SELECTION_BROWSE)
        self.shortcuts.connect("cell-edited", self.on_cell_edited)
        box.pack_start(self.shortcuts)
        self.shortcuts.show()

        self._label = gtk.Label(
            _("You need to restart Stoq for the changes to take effect"))
        box.pack_start(self._label, False, False, 6)

        self.main.remove(self.main.get_child())
        self.main.add(box)
        box.show()

    def _get_columns(self):
        return [Column('description', data_type=str,
                       expand=True),
                Column('category', data_type=str),
                Column('shortcut', data_type=str, editable=True)]

    def on_cell_edited(self, shortcuts, shortcut, attr):
        # FIXME: this should not be stored in stoq.conf
        # FIXME: Use a keyboard grabber
        # FIXME: this is emitted even if the text isn't changed
        api.config.set('Shortcuts', shortcut.name, shortcut.shortcut)
        api.config.flush()
        self._label.show()
