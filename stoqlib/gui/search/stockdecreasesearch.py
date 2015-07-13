# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
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
##
""" Search dialogs for stock decreases"""

import datetime
from decimal import Decimal

import gtk
from kiwi.ui.objectlist import Column

from stoqlib.domain.stockdecrease import StockDecrease
from stoqlib.domain.views import StockDecreaseView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.stockdecreasedialog import StockDecreaseDetailsDialog
from stoqlib.gui.search.searchcolumns import IdentifierColumn, SearchColumn
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.gui.search.searchfilters import DateSearchFilter
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.stockdecrease import StockDecreaseReport

_ = stoqlib_gettext


class StockDecreaseSearch(SearchDialog):
    title = _(u"Manual Stock Decrease Search")
    size = (750, 500)
    search_spec = StockDecreaseView
    report_class = StockDecreaseReport
    selection_mode = gtk.SELECTION_MULTIPLE
    text_field_columns = [StockDecreaseView.removed_by_name,
                          StockDecreaseView.branch_name,
                          StockDecreaseView.reason]
    branch_filter_column = StockDecrease.branch_id

    def __init__(self, store):
        SearchDialog.__init__(self, store)
        self._setup_widgets()

    def _show_details(self, item):
        run_dialog(StockDecreaseDetailsDialog, self, self.store,
                   item.stock_decrease)

    def _setup_widgets(self):
        self.results.connect('row_activated', self.on_row_activated)
        self.update_widgets()

    #
    # SearchDialog Hooks
    #

    def update_widgets(self):
        orders = self.results.get_selected_rows()
        has_one_selected = len(orders) == 1
        self.set_details_button_sensitive(has_one_selected)

    def create_filters(self):
        date_filter = DateSearchFilter(_('Date:'))
        self.add_filter(date_filter, columns=['confirm_date'])

    def get_columns(self):
        return [IdentifierColumn('identifier', title=_('Decrease #')),
                Column('confirm_date', title=_('Date'),
                       data_type=datetime.date, sorted=True, width=100),
                Column('branch_name', title=_('Branch'),
                       data_type=str, expand=True),
                SearchColumn('removed_by_name', title=_('Removed By'),
                             data_type=str, width=120),
                SearchColumn('sent_to_name', title=_('Sent To'),
                             data_type=str, visible=False),
                Column('total_items_removed', title=_('Items removed'),
                       data_type=Decimal, width=110),
                Column('cfop_description', title=_('CFOP'), data_type=str,
                       expand=True),
                SearchColumn('reason', title=_('Reason'), data_type=str),
                ]

    #
    # Callbacks
    #

    def on_row_activated(self, klist, item):
        self._show_details(item)

    def on_details_button_clicked(self, button):
        orders = self.results.get_selected_rows()
        self._show_details(orders[0])
