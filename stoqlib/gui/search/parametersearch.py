# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2013 Async Open Source <http://www.async.com.br>
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

import decimal

from kiwi.python import strip_accents
from kiwi.ui.objectlist import Column
from zope.interface import providedBy

from stoqlib.api import api
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import IDescribable
from stoqlib.lib.defaults import quantize
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext, dgettext
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

    def __init__(self, store):
        BaseEditor.__init__(self, store, model=object())
        # FIXME: Maybe we should use the is_editable from the database in the
        # future?
        self._parameters = [d for d in sysparam.get_details() if d.is_editable]
        self._setup_widgets()

    def _setup_widgets(self):
        self.results.set_columns(self._get_columns())
        self._reset_results()
        self.edit_button.set_sensitive(False)
        # Hiding the button to avoid confusion about discarding the changes
        self.main_dialog.cancel_button.hide()

    def _reset_results(self):
        self.results.clear()
        self.results.add_list(self._parameters)

    def _get_columns(self):
        return [Column('group', title=_('Group'), data_type=str, width=100,
                       sorted=True),
                Column('short_desc', title=_('Parameter'),
                       data_type=str, expand=True),
                AccessorColumn('field_value', title=_('Current value'),
                               accessor=self._get_parameter_value,
                               data_type=str, width=200)]

    def _get_parameter_value(self, detail):
        """Given a ParameterData object, returns a string representation of
        its current value.
        """
        data = sysparam.get(detail.key, detail.type, self.store)
        if isinstance(data, Domain):
            if not (IDescribable in providedBy(data)):
                raise TypeError(u"Parameter `%s' must implement IDescribable "
                                "interface." % detail.key)
            return data.get_description()
        elif detail.options:
            return detail.options[int(data)]
        elif isinstance(data, bool):
            return [_(u"No"), _(u"Yes")][data]
        elif isinstance(data, decimal.Decimal):
            return quantize(data)
        elif detail.key == u'COUNTRY_SUGGESTED':
            return dgettext("iso_3166", data)
        elif isinstance(data, unicode):
            # FIXME: workaround to handle locale specific data
            return _(data)

        if data is None:
            return ''
        return unicode(data)

    def _edit_item(self, item):
        store = api.new_store()
        retval = run_dialog(SystemParameterEditor, self, store, item)
        if store.confirm(retval):
            self.results.update(item)
        store.close()

    def _filter_results(self, text):
        text = strip_accents(text)
        query = text.lower()
        query = query.split()
        self._reset_results()

        if not query:
            # Nothing to look for
            return

        for param in self._parameters:
            group = strip_accents(param.group).lower()
            desc = strip_accents(param.short_desc).lower()

            group_matches = all(i in group for i in query)
            desc_matches = all(i in desc for i in query)
            if not group_matches and not desc_matches:
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

    def on_results__row_activated(self, list, data):
        self._edit_item(data)

    def on_entry__activate(self, widget):
        self._filter_results(widget.get_text())

    def on_show_all_button__clicked(self, widget):
        self.entry.set_text('')
        self._reset_results()

    def on_search_button__clicked(self, widget):
        self._filter_results(self.entry.get_text())
