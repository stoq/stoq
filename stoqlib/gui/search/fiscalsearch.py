# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
##
##
""" Search dialogs for fiscal objects """

import datetime

import gtk
from kiwi.ui.widgets.list import Column
from kiwi.datatypes import currency

from stoqlib.enums import FiscalBookEntry
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import ALL_ITEMS_INDEX
from stoqlib.gui.base.search import SearchEditor
from stoqlib.gui.editors.fiscaleditor import CfopEditor
from stoqlib.gui.slaves.fiscalslave import FiscalBookEntryFilterSlave
from stoqlib.gui.editors.fiscaleditor import FiscalBookEntryEditor
from stoqlib.domain.fiscal import CfopData, IcmsIpiView, IssView


_ = stoqlib_gettext


class CfopSearch(SearchEditor):
    title = _("CFOP Search")
    table = CfopData
    editor_class = CfopEditor
    size = (465, 390)
    searchbar_result_strings = _("CFOP"), _("CFOPs")

    #
    # SearchDialog Hooks
    #

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

    def _setup_columns(self, columns, table, col_name, summary_label_text):
        label_text = '<b>%s</b>' % summary_label_text
        self.klist.set_columns(columns)
        self.set_searchtable(table)
        self.set_searchbar_columns(columns)
        self.setup_summary_label(col_name, label_text)

    def _setup_icms_columns(self):
        cols = self.get_columns() + [Column('icms_value',
                                            title=_('ICMS Total'),
                                            justify=gtk.JUSTIFY_RIGHT,
                                            data_type=currency, width=120)]
        self._setup_columns(cols, IcmsIpiView, 'icms_value',
                            _("ICMS Total:"))

    def _setup_ipi_columns(self):
        cols = self.get_columns() + [Column('ipi_value',
                                            title=_('IPI Total'),
                                            justify=gtk.JUSTIFY_RIGHT,
                                            data_type=currency, width=120)]
        self._setup_columns(cols, IcmsIpiView, 'ipi_value',
                            _("IPI Total:"))

    def _setup_iss_columns(self):
        cols = self.get_columns() + [Column('iss_value',
                                            title=_('ISS Total'),
                                            justify=gtk.JUSTIFY_RIGHT,
                                            data_type=currency, width=120)]
        self._setup_columns(cols, IssView, 'iss_value',
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


    def get_extra_query(self):
        branch = self.filter_slave.get_selected_branch()
        entry_type = self.filter_slave.get_selected_entry_type()
        if entry_type == FiscalBookEntry.ICMS:
            self._setup_icms_columns()
        elif entry_type == FiscalBookEntry.ISS:
            self._setup_iss_columns()
        elif entry_type == FiscalBookEntry.IPI:
            self._setup_ipi_columns()
        else:
            raise ValueError("Invalid fical book entry type, got %s"
                             % entry_type)
        if branch != ALL_ITEMS_INDEX:
            return self.search_table.q.branch_id == branch.id

    #
    # SearchDialog Hooks
    #

    def get_filter_slave(self):
        self.filter_slave = FiscalBookEntryFilterSlave(self.conn)
        return self.filter_slave

    def after_search_bar_created(self):
        self.filter_slave.connect('status-changed',
                                  self.search_bar.search_items)
