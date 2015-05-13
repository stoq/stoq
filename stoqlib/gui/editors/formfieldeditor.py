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
from kiwi.ui.objectlist import ObjectList, Column

from stoqlib.gui.base.dialogs import BasicDialog
from stoqlib.domain.uiform import UIForm, UIField
from stoqlib.lib.message import info
from stoqlib.lib.pluginmanager import get_plugin_manager
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class FormFieldEditor(BasicDialog):
    size = (700, 400)
    title = _("Form fields")

    def __init__(self, store):
        self.store = store
        BasicDialog.__init__(self, size=FormFieldEditor.size,
                             title=FormFieldEditor.title)
        self._create_ui()

    def _create_ui(self):
        hbox = gtk.HBox()
        self.main.remove(self.main.get_child())
        self.main.add(hbox)
        hbox.show()

        self.forms = ObjectList(
            [Column('description', title=_('Description'), sorted=True,
                    expand=True, format_func=stoqlib_gettext)],
            self.store.find(UIForm),
            gtk.SELECTION_BROWSE)
        self.forms.connect('selection-changed',
                           self._on_forms__selection_changed)
        self.forms.set_headers_visible(False)
        self.forms.set_size_request(200, -1)
        hbox.pack_start(self.forms, False, False)
        self.forms.show()

        box = gtk.VBox()
        hbox.pack_start(box)
        box.show()

        self.fields = ObjectList(self._get_columns(), [],
                                 gtk.SELECTION_BROWSE)
        box.pack_start(self.fields)
        self.fields.show()

        box.show()

    def _on_forms__selection_changed(self, forms, form):
        if not form:
            return
        self.fields.add_list(self.store.find(UIField,
                                             ui_form=form), clear=True)
        self.fields.set_cell_data_func(self._uifield__cell_data_func)

    def _uifield__cell_data_func(self, column, renderer, obj, text):
        if isinstance(renderer, gtk.CellRendererText):
            return text

        manager = get_plugin_manager()
        if manager.is_active('nfe'):
            is_editable = obj.field_name not in [u'street', u'district',
                                                 u'city', u'state',
                                                 u'country', u'street_number']

            renderer.set_property('sensitive', is_editable)
            renderer.set_property('activatable', is_editable)
        return text

    def _get_columns(self):
        return [Column('description', title=_('Description'), data_type=str,
                       expand=True, sorted=True,
                       format_func=stoqlib_gettext),
                Column('visible', title=_('Visible'), data_type=bool,
                       width=120, editable=True),
                Column('mandatory', title=_('Mandatory'), data_type=bool,
                       width=120, editable=True)]

    def confirm(self, *args):
        self.store.confirm(True)
        BasicDialog.confirm(self, *args)
        info(_("Changes will be applied after all instances of Stoq are restarted."))

    def cancel(self, *args):
        self.store.rollback(close=False)
        BasicDialog.confirm(self, *args)
