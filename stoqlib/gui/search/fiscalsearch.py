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
##  Author(s): Evandro Vale Miquelito   <evandro@async.com.br>
##             Johan Dahlin             <jdahlin@async.com.br>
##
""" Search dialogs for fiscal objects """

import datetime

import gtk
from kiwi.datatypes import currency
from kiwi.enums import SearchFilterPosition
from kiwi.python import enum
from kiwi.ui.search import ComboSearchFilter
from kiwi.ui.widgets.list import Column

from stoqlib.domain.fiscal import CfopData, IcmsIpiView, IssView
from stoqlib.gui.base.search import SearchEditor
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
    title = _("CFOP Search")
    table = CfopData
    editor_class = CfopEditor
    size = (465, 390)
    searchbar_result_strings = _("CFOP"), _("CFOPs")

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['description', 'code'])

    def get_columns(self):
        return [Column('code', _('CFOP'), data_type=str, sorted=True,
                       width=90),
                Column('description', _('Description'), data_type=str,
                       searchable=True, expand=True)]


class FiscalBookEntrySearch(SearchEditor):
    title = _("Search for fiscal entries")
    size = (750, 450)
    search_table = IcmsIpiView
    editor_class = FiscalBookEntryEditor
    searching_by_date = True
    has_new_button = False
    searchbar_result_strings = _("fiscal entry"), _("fiscal entries")

    def _setup_columns(self, column, table, col_name, summary_label_text):
        label_text = '<b>%s</b>' % summary_label_text
        columns = self.get_columns() + [column]
        self.results.set_columns(columns)
        self.set_table(table)
        #self.setup_summary_label(col_name, label_text)

    def _setup_icms_columns(self):
        col = Column('icms_value',
                     title=_('ICMS Total'),
                     justify=gtk.JUSTIFY_RIGHT,
                     data_type=currency, width=120)
        self._setup_columns(col, IcmsIpiView, 'icms_value',
                            _("ICMS Total:"))

    def _setup_ipi_columns(self):
        col = Column('ipi_value',
                     title=_('IPI Total'),
                     justify=gtk.JUSTIFY_RIGHT,
                     data_type=currency, width=120)
        self._setup_columns(col, IcmsIpiView, 'ipi_value',
                            _("IPI Total:"))

    def _setup_iss_columns(self):
        col = Column('iss_value',
                     title=_('ISS Total'),
                     justify=gtk.JUSTIFY_RIGHT,
                     data_type=currency, width=120)
        self._setup_columns(col, IssView, 'iss_value',
                            _("ISS Total:"))

    #
    # SearchBar Hooks
    #

    def get_columns(self):
        return [Column('id', title=_('#'), width=80,
                       data_type=int, sorted=True),
                Column('date', title=_('Date'), width=80,
                       data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT),
                Column('invoice_number', title=_('Invoice'),
                       data_type=int, width=110),
                Column('cfop_code', title=_('CFOP'), data_type=str, width=90),
                Column('drawee_name', title=_('Drawee'),
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

    def get_editor_model(self, view_object):
        return view_object.book_entry

