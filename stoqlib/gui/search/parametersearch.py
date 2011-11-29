# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2009 Async Open Source <http://www.async.com.br>
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
""" Listing dialog for system parameters """

from kiwi.argcheck import argcheck
from kiwi.ui.objectlist import Column
from zope.interface import providedBy

from stoqlib.api import api
from stoqlib.domain.base import AbstractModel
from stoqlib.domain.interfaces import IDescribable
from stoqlib.domain.parameter import ParameterData
from stoqlib.lib.imageutils import ImageHelper
from stoqlib.lib.parameters import sysparam, DirectoryParameter
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.columns import AccessorColumn
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.editors.parameterseditor import SystemParameterEditor

_ = stoqlib_gettext


class ParameterSearch(BaseEditor):
    gladefile = 'ParameterSearch'
    model_type = object
    size = (750, 450)
    title = _(u"Stoq System Parameters")

    def __init__(self, conn):
        BaseEditor.__init__(self, conn, model=object())
        self._parameters = []
        self._setup_widgets()

    def _setup_widgets(self):
        self.results.set_columns(self._get_columns())
        self._parameters = ParameterData.select(connection=self.conn)
        self._reset_results()
        self.edit_button.set_sensitive(False)

    def _reset_results(self):
        self.results.clear()
        self.results.add_list(self._parameters)

    def _get_columns(self):
        return [Column('group', title=_('Group'), data_type=str, width=100,
                       sorted=True),
                Column('short_description', title=_('Parameter'),
                       data_type=str, expand=True),
                AccessorColumn('field_value', title=_('Current value'),
                               accessor=self._get_parameter_value,
                               data_type=str, width=200)]

    @argcheck(ParameterData)
    def _get_parameter_value(self, obj):
        """Given a ParameterData object, returns a string representation of
        its current value.
        """
        constant = sysparam(self.conn).get_parameter_constant(
                                                        obj.field_name)
        data = getattr(sysparam(self.conn), obj.field_name)
        if isinstance(data, AbstractModel):
            if not (IDescribable in providedBy(data)):
                raise TypeError("Parameter `%s' must implement IDescribable "
                                "interface." % obj.field_name)
            return data.get_description()
        elif constant.options:
            return constant.options[int(obj.field_value)]
        elif isinstance(data, ImageHelper):
            return data.image_path
        elif isinstance(data, DirectoryParameter):
            return data.path
        elif isinstance(data, bool):
            return [_("No"), _("Yes")][data]
        elif isinstance(data, unicode):
            #FIXME: workaround to handle locale specific data
            return _(data)
        return data

    def _edit_item(self, item):
        trans = api.new_transaction()
        parameter = trans.get(item)
        retval = run_dialog(SystemParameterEditor, self, trans, parameter)
        if api.finish_transaction(trans, retval):
            sysparam(trans).rebuild_cache_for(item.field_name)
            self.results.update(item)
        trans.close()

    def _filter_results(self, text):
        query = text.lower()
        if not query:
            self._reset_results()

        for param in self._parameters:
            if (query in param.get_group().lower() or
                query in param.get_short_description().lower()):
                if param not in self.results:
                    self.results.append(param)
            else:
                if param in self.results:
                    self.results.remove(param)

    #
    # Kiwi Callbacks
    #

    def on_results__selection_changed(self, list, data):
        self.edit_button.set_sensitive(data is not None)

    def on_edit_button__clicked(self, widget):
        self._edit_item(self.results.get_selected())

    def on_results__double_click(self, list, data):
        self._edit_item(data)

    def on_entry__activate(self, widget):
        self._filter_results(widget.get_text())

    def on_show_all_button__clicked(self, widget):
        self._reset_results()
