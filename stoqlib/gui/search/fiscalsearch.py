# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Search dialogs for fiscal objects """

import datetime

import gtk
from kiwi.currency import currency
from kiwi.python import enum

from stoqlib.api import api
from stoqlib.domain.fiscal import CfopData, IcmsIpiView, IssView
from stoqlib.enums import SearchFilterPosition
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.fiscaleditor import (CfopEditor,
                                              FiscalBookEntryEditor)
from stoqlib.gui.search.searchcolumns import SearchColumn
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.gui.search.searcheditor import SearchEditor
from stoqlib.gui.search.searchfilters import ComboSearchFilter
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class FiscalBookEntryType(enum):
    (ICMS,
     IPI,
     ISS) = range(3)

fiscal_book_entries = {FiscalBookEntryType.ICMS: _("ICMS"),
                       FiscalBookEntryType.IPI: _("IPI"),
                       FiscalBookEntryType.ISS: _("ISS")}


class CfopSearch(SearchEditor):
    title = _("C.F.O.P. Search")
    search_spec = CfopData
    editor_class = CfopEditor
    size = (-1, 390)

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['description', 'code'])

    def get_columns(self):
        return [SearchColumn('code', _('C.F.O.P.'), data_type=str, sorted=True,
                             width=90),
                SearchColumn('description', _('Description'), data_type=str,
                             searchable=True, expand=True)]


class FiscalBookEntrySearch(SearchDialog):
    title = _("Search for fiscal entries")
    size = (-1, 450)
    search_spec = IcmsIpiView
    text_field_columns = []
    branch_filter_column = IcmsIpiView.branch_id

    def _setup_columns(self, column, table, col_name, summary_label_text):
        columns = self.get_columns() + [column]
        self.results.set_columns(columns)
        self.search.set_search_spec(table)

    def _setup_icms_columns(self):
        col = SearchColumn('icms_value',
                           title=_('ICMS Total'),
                           justify=gtk.JUSTIFY_RIGHT,
                           data_type=currency, width=100)
        self._setup_columns(col, IcmsIpiView, 'icms_value',
                            _("ICMS Total:"))

    def _setup_ipi_columns(self):
        col = SearchColumn('ipi_value',
                           title=_('IPI Total'),
                           justify=gtk.JUSTIFY_RIGHT,
                           data_type=currency, width=100)
        self._setup_columns(col, IcmsIpiView, 'ipi_value',
                            _("IPI Total:"))

    def _setup_iss_columns(self):
        col = SearchColumn('iss_value',
                           title=_('ISS Total'),
                           justify=gtk.JUSTIFY_RIGHT,
                           data_type=currency, width=100)
        self._setup_columns(col, IssView, 'iss_value',
                            _("ISS Total:"))

    #
    # SearchBar Hooks
    #

    def get_columns(self):
        return [SearchColumn('date', title=_('Date'), width=80,
                             data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT),
                SearchColumn('invoice_number', title=_('Invoice'),
                             data_type=int, width=100, sorted=True),
                SearchColumn('cfop_code', title=_('C.F.O.P.'),
                             data_type=str, width=75),
                SearchColumn('drawee_name', title=_('Drawee'),
                             data_type=str, expand=True)]

    def _get_entry_type_query(self, state):
        entry_type = state.value
        if entry_type == FiscalBookEntryType.ICMS:
            self._setup_icms_columns()
        elif entry_type == FiscalBookEntryType.ISS:
            self._setup_iss_columns()
        elif entry_type == FiscalBookEntryType.IPI:
            self._setup_ipi_columns()
        else:
            raise ValueError("Invalid fical book entry type, got %s"
                             % entry_type)

    #
    # SearchDialog Hooks
    #

    def setup_widgets(self):
        self.edit_button = self.add_button(_('Edit'))
        self.edit_button.connect('clicked', self._on_edit_button__clicked)
        self.edit_button.show()
        self.edit_button.set_sensitive(False)

        self.add_csv_button(_('Fiscal book'), _('fiscal-book'))

    def update_widgets(self):
        can_edit = bool(self.results.get_selected())
        self.edit_button.set_sensitive(can_edit)

    def create_filters(self):
        items = [(v, k)
                 for k, v in fiscal_book_entries.items()]
        self.entry_type = ComboSearchFilter(_('Show entries of type'), items)
        self.add_filter(self.entry_type, callback=self._get_entry_type_query,
                        position=SearchFilterPosition.TOP)

    #
    # Callbacks
    #

    def _on_edit_button__clicked(self, widget):
        entry = self.results.get_selected()
        assert entry is not None

        store = api.new_store()
        retval = run_dialog(FiscalBookEntryEditor, self, store,
                            store.fetch(entry.book_entry))
        store.confirm(retval)
        store.close()
