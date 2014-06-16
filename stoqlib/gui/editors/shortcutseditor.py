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

import warnings

import gtk
from kiwi.ui.objectlist import ObjectList, Column

from stoqlib.api import api
from stoqlib.gui.base.dialogs import BasicDialog
from stoqlib.gui.utils.keybindings import (get_bindings,
                                           set_user_binding,
                                           remove_user_binding,
                                           remove_user_bindings,
                                           get_binding_categories)
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


# Gtk+ bug 639455 fixed in 2011-01-04 in 3.x branch
warnings.filterwarnings(
    action='ignore', module='stoqlib.gui.base.dialogs',
    message=("Object class GtkCellEditableEventBox doesn't implement "
             "property 'editing-canceled' from interface 'GtkCellEditable'"))


class ShortcutColumn(Column):
    def __init__(self, attribute, title, editor, **kwargs):
        Column.__init__(self, attribute=attribute, title=title,
                        data_type=str, **kwargs)
        self.editor = editor

    def create_renderer(self, model):
        renderer = gtk.CellRendererAccel()
        renderer.props.editable = True
        renderer.props.accel_mode = gtk.CELL_RENDERER_ACCEL_MODE_OTHER
        renderer.connect('accel-edited', self._on_accel_edited)
        renderer.connect('accel-cleared', self._on_accel_cleared)
        return renderer, 'text'

    def _on_accel_edited(self, renderer, path, accel_key, mods, keycode):
        model = self._objectlist.get_model()
        binding = model[path][0]
        binding.shortcut = gtk.accelerator_name(accel_key, mods)
        self.editor.set_binding(binding)

    def _on_accel_cleared(self, renderer, path):
        model = self._objectlist.get_model()
        binding = model[path][0]
        self.editor.remove_binding(binding)
        binding.shortcut = None


class ShortcutsEditor(BasicDialog):
    size = (700, 400)
    title = _("Keyboard shortcuts")

    def __init__(self):
        BasicDialog.__init__(self, size=ShortcutsEditor.size,
                             title=ShortcutsEditor.title)
        self._create_ui()

    def _create_ui(self):
        self.cancel_button.hide()

        hbox = gtk.HBox(spacing=6)
        self.main.remove(self.main.get_child())
        self.main.add(hbox)
        hbox.show()

        self.categories = ObjectList(
            [Column('label', sorted=True, expand=True)],
            get_binding_categories(),
            gtk.SELECTION_BROWSE)
        self.categories.connect('selection-changed',
                                self._on_categories__selection_changed)
        self.categories.set_headers_visible(False)
        self.categories.set_size_request(200, -1)
        hbox.pack_start(self.categories, False, False)
        self.categories.show()

        box = gtk.VBox(spacing=6)
        hbox.pack_start(box)
        box.show()

        self.shortcuts = ObjectList(self._get_columns(), [],
                                    gtk.SELECTION_BROWSE)
        box.pack_start(self.shortcuts)
        self.shortcuts.show()

        self._label = gtk.Label(
            _("You need to restart Stoq for the changes to take effect"))
        box.pack_start(self._label, False, False, 6)

        box.show()

        defaults_button = gtk.Button(_("Reset defaults"))
        defaults_button.connect('clicked', self._on_defaults_button__clicked)
        self.action_area.pack_start(defaults_button, False, False, 6)
        self.action_area.reorder_child(defaults_button, 0)
        defaults_button.show()

    def _on_categories__selection_changed(self, categories, category):
        if not category:
            return
        self.shortcuts.add_list(get_bindings(category.name), clear=True)

    def _on_defaults_button__clicked(self, button):
        old = self.categories.get_selected()
        api.user_settings.remove('shortcuts')
        remove_user_bindings()
        self._label.show()
        self.categories.refresh()
        self.categories.select(old)

    def _get_columns(self):
        return [Column('description', _("Description"), data_type=str,
                       expand=True, sorted=True),
                ShortcutColumn('shortcut', _("Shortcut"), self)]

    def set_binding(self, binding):
        set_user_binding(binding.name, binding.shortcut)
        d = api.user_settings.get('shortcuts', {})
        d[binding.name] = binding.shortcut
        self._label.show()

    def remove_binding(self, binding):
        remove_user_binding(binding.name)
        d = api.user_settings.get('shortcuts', {})
        try:
            del d[binding.name]
        except KeyError:
            pass
        self._label.show()
