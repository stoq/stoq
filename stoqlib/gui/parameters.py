# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s): Henrique Romano <henrique@async.com.br>
##
##
""" Listing dialog for system parameters """

import gtk
from kiwi.ui.objectlist import Column, ObjectList
from kiwi.argcheck import argcheck
from zope.interface import providedBy

from stoqlib.database.runtime import rollback_and_begin
from stoqlib.domain.base import AbstractModel
from stoqlib.domain.interfaces import IDescribable
from stoqlib.domain.parameter import ParameterData
from stoqlib.lib.imageutils import ImageHelper
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.dialogs import BasicDialog
from stoqlib.gui.base.search import SearchEditorToolBar
from stoqlib.gui.base.columns import AccessorColumn
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.parameterseditor import SystemParameterEditor

_ = stoqlib_gettext

#
# This class implementation will be improved after bug #2406 is fixed
#
class ParametersListingDialog(BasicDialog):
    size = (700, 400)
    title = _("Stoq System Parameters")

    def __init__(self, conn):
        BasicDialog.__init__(self)
        self._initialize(hide_footer=True, size=ParametersListingDialog.size,
                         title=ParametersListingDialog.title)
        self.conn = conn
        self._setup_list()
        self._setup_slaves()

    def _setup_slaves(self):
        self._toolbar_slave = SearchEditorToolBar()
        self._toolbar_slave.connect("edit", self._on_edit_button__clicked)
        self._toolbar_slave.new_button.hide()
        self._toolbar_slave.edit_button.set_sensitive(False)
        self.attach_slave("extra_holder", self._toolbar_slave)

    def _setup_list(self):
        self.klist = ObjectList(self._get_columns(), self._get_data(),
                                gtk.SELECTION_BROWSE)
        self.klist.connect("selection-changed",
                           self._on_klist__selection_changed)
        self.klist.connect("double-click", self._on_klist__double_click)
        self.main.remove(self.main.get_child())
        self.main.add(self.klist)
        self.klist.show()

    def _get_columns(self):
        return [Column('group', title=_('Group'), data_type=str, width=100,
                       sorted=True),
                Column('short_description', title=_('Parameter Name'),
                       data_type=str, expand=True),
                AccessorColumn('field_value', title=_('Current Value'),
                               accessor=self._get_parameter_value,
                               data_type=str, width=200)]

    @argcheck(ParameterData)
    def _get_parameter_value(self, obj):
        """ Given a ParameterData object, returns a string representation of
        its current value.
        """
        data = getattr(sysparam(self.conn), obj.field_name)
        if isinstance(data, AbstractModel):
            if not (IDescribable in providedBy(data)):
                raise TypeError("Parameter `%s' must implement IDescribable "
                                "interface." % obj.field_name)
            return data.get_description()
        elif isinstance(data, ImageHelper):
            return data.image_path
        elif isinstance(data, bool):
            return [_("No"), _("Yes")][data]
        return data

    def _get_data(self):
        return ParameterData.select(ParameterData.q.is_editable == True,
                                    connection=self.conn)

    def _edit_item(self, item):
        res = run_dialog(SystemParameterEditor, self, self.conn, item)
        if res:
            self.conn.commit()
            sysparam(self.conn).rebuild_cache_for(item.field_name)
            self.klist.update(res)
        else:
            rollback_and_begin(self.conn)

    #
    # Callbacks
    #

    def _on_klist__selection_changed(self, list, data):
        self._toolbar_slave.edit_button.set_sensitive(data is not None)

    def _on_edit_button__clicked(self, toolbar_slave):
        self._edit_item(self.klist.get_selected())

    def _on_klist__double_click(self, list, data):
        self._edit_item(data)
