# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Implementation of classes related to till operations.  """


import datetime

import gtk
from kiwi.currency import currency
from kiwi.ui.objectlist import Column, ColoredColumn

from stoqlib.api import api
from stoqlib.domain.till import TillEntry
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.tilleditor import (CashAdvanceEditor, CashInEditor,
                                            CashOutEditor)
from stoqlib.gui.stockicons import (STOQ_MONEY, STOQ_MONEY_ADD,
                                    STOQ_MONEY_REMOVE)
from stoqlib.gui.search.searchcolumns import IdentifierColumn
from stoqlib.gui.search.searchfilters import DateSearchFilter
from stoqlib.gui.search.searchoptions import Today
from stoqlib.gui.utils.printing import print_report
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import payment_value_colorize
from stoqlib.reporting.till import TillHistoryReport

_ = stoqlib_gettext


class TillHistoryDialog(SearchDialog):
    size = (780, -1)
    search_spec = TillEntry
    selection_mode = gtk.SELECTION_MULTIPLE
    searchbar_labels = _('Till Entries matching:')
    title = _('Till history')

    #
    # SearchDialog
    #

    def get_columns(self, *args):
        return [IdentifierColumn('identifier', title=_('Entry #'), sorted=True),
                Column('date', _('Date'), data_type=datetime.date),
                Column('time', _('Time'), data_type=datetime.time),
                Column('description', _('Description'), data_type=str,
                       expand=True),
                ColoredColumn('value', _('Value'), data_type=currency,
                              color='red', data_func=payment_value_colorize,
                              width=140)]

    def create_filters(self):
        self.set_text_field_columns(['description'])

        self.date_filter = DateSearchFilter(_('Date:'))
        self.date_filter.select(Today)
        self.add_filter(self.date_filter, columns=['date'])
        # add summary label
        value_format = '<b>%s</b>'
        total_label = '<b>%s</b>' % api.escape(_(u'Total:'))
        self.search.set_summary_label('value', total_label, value_format)

    def setup_widgets(self):
        self.results.set_visible_rows(10)
        self.results.connect('has-rows', self._has_rows)

        self._add_editor_button(_('Cash _Add...'), CashAdvanceEditor,
                                STOQ_MONEY)
        self._add_editor_button(_('Cash _In...'), CashInEditor,
                                STOQ_MONEY_ADD)
        self._add_editor_button(_('Cash _Out...'), CashOutEditor,
                                STOQ_MONEY_REMOVE)

        self.print_button = gtk.Button(None, gtk.STOCK_PRINT, True)
        self.print_button.set_property("use-stock", True)
        self.print_button.connect('clicked', self._print_button_clicked)
        self.action_area.set_layout(gtk.BUTTONBOX_START)
        self.action_area.pack_end(self.print_button, False, False, 6)
        self.print_button.show()
        self.print_button.set_sensitive(False)

    #
    # Private API
    #

    def _add_editor_button(self, name, editor_class, stock):
        button = self.add_button(name, stock=stock)
        button.connect('clicked', self._run_editor, editor_class)
        button.show()

    def _print_button_clicked(self, button):
        print_report(TillHistoryReport, self.results, list(self.results),
                     filters=self.search.get_search_filters())

    def _run_editor(self, button, editor_class):
        with api.new_store() as store:
            run_dialog(editor_class, self, store)
        if store.committed:
            self.search.refresh()
            self.results.unselect_all()
            if len(self.results):
                self.results.select(self.results[-1])

    def _has_rows(self, results, obj):
        self.print_button.set_sensitive(obj)
