# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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


import gtk
import datetime

from kiwi.db.query import DateQueryState, DateIntervalQueryState
from kiwi.ui.search import DateSearchFilter
from kiwi.ui.objectlist import SearchColumn, Column

from stoqlib.api import api
from stoqlib.domain.interfaces import IClient
from stoqlib.domain.person import CallsView, ClientCallsView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.search import SearchEditor
from stoqlib.gui.dialogs.csvexporterdialog import CSVExporterDialog
from stoqlib.gui.editors.callseditor import CallsEditor
from stoqlib.gui.printing import print_report
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.calls_report import CallsReport

_ = stoqlib_gettext


class CallsSearch(SearchEditor):
    """This search can be used directly, to show calls to any kind of person in
    the system.

    Subclasses can also override I{person_interface} to set the person type that
    will be available when creating a new call, and I{person_name}, that will be
    the column title in this search.
    """
    title = _("Calls Search")
    search_table = CallsView
    editor_class = CallsEditor
    searching_by_date = True
    person_interface = None
    person_name = _('Person')
    size = (700, 450)

    def __init__(self, conn, person=None, date=None, reuse_transaction=False):
        """
        @param person: If not None, the search will show only call made to
            this person.
        @param date: If not None, the search will be filtered using this date by
            default
        @param reuse_transaction: When False, a new transaction will be
            created/commited when creating a new call. When True, no transaction
            will be created. In this case, I{conn} will be utilized.
        """
        self.conn = conn
        self.person = person
        self._date = date
        self._reuse_transaction = reuse_transaction
        SearchEditor.__init__(self, conn)

    #
    # SearchEditor Hooks
    #

    def get_editor_model(self, calls):
        return calls.call

    def setup_widgets(self):
        self.csv_button = self.add_button(label=_("Export CSV..."))
        self.csv_button.connect('clicked', self._on_export_csv_button__clicked)
        self.csv_button.show()
        self.csv_button.set_sensitive(False)

        self.print_button = self.add_button(label=_("Print"))
        self.print_button.connect('clicked', self._on_print_button__clicked)
        self.print_button.set_sensitive(False)
        self.print_button.show()

        # To separate the csv and print buttons.
        self.action_area.set_layout(gtk.BUTTONBOX_EDGE)

        self.results.connect('has_rows', self._on_results__has_rows)

    def create_filters(self):
        self.set_text_field_columns(['description', 'message'])
        self.set_searchbar_labels(_('matching:'))
        self.executer.set_query(self.executer_query)

        # Date
        date_filter = DateSearchFilter(_("Date:"))
        self.search.add_filter(date_filter)
        self.date_filter = date_filter
        if self._date:
            date_filter.mode.select_item_by_position(5)
            date_filter.start_date.set_date(self._date)
            self.search.refresh()

    def get_columns(self):
        columns = [Column('date', title=_('Date'),
                       data_type=datetime.date, width=150, sorted=True),
                SearchColumn('description', title=_('Description'),
                             data_type=str, width=150, expand=True),
                SearchColumn('attendant', title=_('Attendant'),
                             data_type=str, width=100, expand=True)]
        if not self.person:
            columns.insert(1,
                SearchColumn('person', title=self.person_name,
                             data_type=str, width=150, expand=True))
        return columns

    def executer_query(self, query, having, conn):
        client = self.person

        date = self.date_filter.get_state()
        if isinstance(date, DateQueryState):
            date = date.date
        elif isinstance(date, DateIntervalQueryState):
            date = (date.start, date.end)

        # Use the current connection ('self.conn') to show inserted calls,
        # before confirm the new person.
        return self.search_table.select_by_client_date(query, client, date,
                                                       connection=self.conn)

    def update_widgets(self, *args):
        call_view = self.results.get_selected()
        self.set_edit_button_sensitive(call_view is not None)

    def run_editor(self, obj):
        if self._reuse_transaction:
            self.conn.savepoint('before_run_editor')
            retval = run_dialog(self.editor_class, self, self.conn,
                                self.conn.get(obj), self.person,
                                self.person_interface)
            if not retval:
                self.conn.rollback_to_savepoint('before_run_editor')
        else:
            trans = api.new_transaction()
            retval = run_dialog(self.editor_class, self, trans,
                                trans.get(obj), self.person,
                                self.person_interface)
            api.finish_transaction(trans, retval)
            trans.close()
        return retval

    #
    # Callbacks
    #

    def _on_export_csv_button__clicked(self, widget):
        run_dialog(CSVExporterDialog, self, self.conn, self.search_table,
                   self.results)

    def _on_results__has_rows(self, widget, has_rows):
        self.print_button.set_sensitive(has_rows)
        self.csv_button.set_sensitive(has_rows)

    def _on_print_button__clicked(self, widget):
        print_report(CallsReport, self.results, list(self.results),
                     filters=self.search.get_search_filters(),
                     person=self.person)


class ClientCallsSearch(CallsSearch):
    title = _("Calls Search")
    search_table = ClientCallsView
    person_interface = IClient
    person_name = _('Client')
