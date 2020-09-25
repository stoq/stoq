# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

#
# Copyright (C) 2011-2013 Async Open Source <http://www.async.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
# Author(s): Stoq Team <stoq-devel@async.com.br>
#
""" Application to launcher other application.  """


from gi.repository import Gtk

from stoqlib.api import api
from stoqlib.lib.translation import stoqlib_gettext
from stoq.lib.gui.widgets.workorder import WorkOrderList

from stoq.gui.shell.shellapp import ShellApp
from stoq.gui.widgets import Apps, ShortcutGrid, Section

_ = stoqlib_gettext


class LauncherApp(ShellApp):
    gladefile = "launcher"
    app_title = "Stoq"

    #
    # ShellApp
    #

    def create_ui(self):
        self._updating = False
        self.main_box.get_style_context().add_class(Gtk.STYLE_CLASS_VIEW)

        self.app_grid = Apps(self.window)
        launcher_screen = api.user_settings.get('launcher-screen', None)
        if launcher_screen == 'my-work-orders':
            main_widget = WorkOrderList(self.window.store)
        else:
            main_widget = self.app_grid
        self.app_box.pack_start(main_widget, False, False, 0)

        self.side_box.pack_start(Section(_('Shortcuts')), False, False, 0)
        self.sc_grid = ShortcutGrid(self.window)
        self.side_box.pack_start(self.sc_grid, False, False, 0)

        self.side_box.pack_start(Section(_('Messages')), False, False, 0)
        from stoq.gui.shell.statusbar import StatusBox
        self.status = StatusBox(compact=True)
        self.side_box.pack_start(self.status, True, True, 0)

        self.main_box.show_all()
        self.boxes = self.app_grid.get_flowboxes() + [self.sc_grid]
        for box in self.boxes:
            box.connect('selected-children-changed', self._on_selection_changed)

        self.status.update_ui()

    #
    # Callbacks
    #

    def _on_selection_changed(self, box):
        selection = box.get_selected_children()
        if not selection:
            return

        for other in self.boxes:
            if other != box:
                other.unselect_all()
