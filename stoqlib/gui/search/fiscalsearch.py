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
from kiwi.datatypes import currency
from kiwi.enums import SearchFilterPosition
from kiwi.python import enum
from kiwi.ui.search import ComboSearchFilter
from kiwi.ui.objectlist import SearchColumn

from stoqlib.api import api
from stoqlib.domain.fiscal import CfopData, IcmsIpiView, IssView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.search import SearchEditor, SearchDialog
from stoqlib.gui.dialogs.csvexporterdialog import CSVExporterDialog
from stoqlib.gui.editors.fiscaleditor import (CfopEditor,
                                              FiscalBookEntryEditor)
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
    table = CfopData
    editor_class = CfopEditor
    size = (-1, 390)
    searchbar_result_strings = _("C.F.O.P."), _("C.F.O.P.s")

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
    search_table = IcmsIpiView
    searching_by_date = True
    searchbar_result_strings = _("fiscal entry"), _("fiscal entries")

    def _setup_columns(self, column, table, col_name, summary_label_text):
        columns = self.get_columns() + [column]
        self.results.set_columns(columns)
        self.set_table(table)

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
        return [SearchColumn('id', title=_('#'), width=80,
                             data_type=int, sorted=True),
                SearchColumn('date', title=_('Date'), width=80,
                             data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT),
                SearchColumn('invoice_number', title=_('Invoice'),
                             data_type=int, width=100),
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
        self.edit_button = self.add_button('Edit')
        self.edit_button.connect('clicked', self._on_edit_button__clicked)
        self.edit_button.show()
        self.edit_button.set_sensitive(False)

        self.csv_button = self.add_button(label=_(u'Export CSV...'))
        self.csv_button.connect('clicked', self._on_export_csv_button__clicked)
        self.csv_button.show()
        self.csv_button.set_sensitive(False)

        self.results.connect('has_rows', self._on_results__has_rows)

    def update_widgets(self):
        can_edit = bool(self.results.get_selected())
        self.edit_button.set_sensitive(can_edit)

    def create_filters(self):
        self.set_text_field_columns([])

        branch_filter = self.create_branch_filter(_('In branch:'))
        branch_filter.select(None)
        self.add_filter(branch_filter, columns=['branch_id'])

        items = [(v, k)
                    for k, v in fiscal_book_entries.items()]
        entry_type = ComboSearchFilter(_('Show entries of type'), items)
        self.add_filter(entry_type, callback=self._get_entry_type_query,
                        position=SearchFilterPosition.TOP)

    #
    # Callbacks
    #

    def _on_edit_button__clicked(self, widget):
        entry = self.results.get_selected()
        assert entry is not None

        trans = api.new_transaction()
        retval = run_dialog(FiscalBookEntryEditor, self, trans,
                            trans.get(entry.book_entry))
        api.finish_transaction(trans, retval)
        trans.close()

    def _on_export_csv_button__clicked(self, widget):
        run_dialog(CSVExporterDialog, self, self.conn, self.search_table,
                   self.results)

    def _on_results__has_rows(self, widget, has_rows):
        self.csv_button.set_sensitive(has_rows)
