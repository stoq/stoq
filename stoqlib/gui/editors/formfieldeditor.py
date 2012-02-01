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
from stoqlib.domain.uiform import UIForm, UIField
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class FormFieldEditor(BasicDialog):
    size = (700, 400)
    title = _("Form fields")

    def __init__(self, conn):
        self.conn = conn
        BasicDialog.__init__(self)
        self._initialize(size=FormFieldEditor.size, title=FormFieldEditor.title)
        self._create_ui()

    def _create_ui(self):
        hbox = gtk.HBox()
        self.main.remove(self.main.get_child())
        self.main.add(hbox)
        hbox.show()

        self.forms = ObjectList(
            [Column('description', sorted=True, expand=True)],
            UIForm.select(connection=self.conn),
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
        self.fields.add_list(UIField.selectBy(connection=self.conn,
                                              ui_form=form), clear=True)

    def _get_columns(self):
        return [Column('description', data_type=str,
                       expand=True, sorted=True),
                Column('visible', data_type=bool,
                       width=120, editable=True),
                Column('mandatory', data_type=bool,
                       width=120, editable=True)]

    def confirm(self, *args):
        api.finish_transaction(self.conn, True)
        BasicDialog.confirm(self, *args)

    def cancel(self, *args):
        api.rollback_and_begin(self.conn)
        BasicDialog.confirm(self, *args)
