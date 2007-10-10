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
## Author(s):       Johan Dahlin            <jdahlin@async.com.br>
##
""" Implementation of classes related to till operations.  """


import datetime

import gtk
from kiwi.datatypes import currency
from kiwi.ui.search import DateSearchFilter, Today
from kiwi.ui.widgets.list import Column, ColoredColumn

from stoqlib.database.runtime import finish_transaction
from stoqlib.domain.till import TillEntry
from stoqlib.gui.base.search import SearchDialog
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.tilleditor import (CashAdvanceEditor, CashInEditor,
                                            CashOutEditor)
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import payment_value_colorize

_ = stoqlib_gettext


class TillHistoryDialog(SearchDialog):
    size = (780, -1)
    table = TillEntry
    selection_mode = gtk.SELECTION_MULTIPLE
    searchbar_labels = _('Till Entries matching:')
    title = _('Till history')

    #
    # SearchDialog
    #

    def get_columns(self, *args):
        return [Column('id', _('Number'), data_type=int, width=80,
                        format='%03d', sorted=True),
                Column('date', _('Date'),
                       data_type=datetime.date, width=110),
                Column('description', _('Description'), data_type=str,
                       expand=True,
                       width=300),
                ColoredColumn('value', _('Value'), data_type=currency,
                              color='red', data_func=payment_value_colorize,
                              width=140)]
    def create_filters(self):
        self.set_text_field_columns(['description'])

        date_filter = DateSearchFilter(_('Date:'))
        date_filter.select(Today)
        self.add_filter(date_filter, columns=['date'])
        # add summary label
        value_format = '<b>%s</b>'
        total_label = '<b>%s</b>' % _(u'Total:')
        self.search.set_summary_label('value', total_label, value_format)

    def setup_widgets(self):
        self.results.set_visible_rows(10)
        self._add_editor_button(_('Cash _Advance...'), CashAdvanceEditor)
        self._add_editor_button(_('Cash _In...'), CashInEditor)
        self._add_editor_button(_('Cash _Out...'), CashOutEditor)

    def _add_editor_button(self, name, editor_class):
        b = gtk.Button(name)
        b.connect('clicked', lambda b: self._run_editor(editor_class))
        b.set_use_underline(True)
        self.action_area.set_layout(gtk.BUTTONBOX_START)
        self.action_area.pack_start(b, False, False, 6)
        b.show()

    #
    # Private API
    #

    def _run_editor(self, editor_class):
        model = run_dialog(editor_class, self, self.conn)
        if finish_transaction(self.conn, model):
            self.search.refresh()
            self.results.unselect_all()
            if len(self.results):
                self.results.select(self.results[-1])

