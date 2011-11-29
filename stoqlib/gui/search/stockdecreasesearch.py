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
from kiwi.ui.search import DateSearchFilter
from kiwi.ui.objectlist import Column

from stoqlib.domain.stockdecrease import StockDecrease
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.search import SearchDialog
from stoqlib.gui.dialogs.stockdecreasedialog import StockDecreaseDetailsDialog
from stoqlib.gui.printing import print_report
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.stockdecreasereceipt import StockDecreaseReceipt

_ = stoqlib_gettext


class StockDecreaseSearch(SearchDialog):
    title = _(u"Manual Stock Decrease Search")
    size = (750, 500)
    search_table = StockDecrease
    selection_mode = gtk.SELECTION_MULTIPLE
    searchbar_result_strings = _(u"manual stock decrease"), _(u"manual stock decreases")
    search_by_date = True
    advanced_search = False

    def __init__(self, conn):
        SearchDialog.__init__(self, conn, self.search_table,
                              title=self.title)
        self._setup_widgets()

    def _show_details(self, item):
        run_dialog(StockDecreaseDetailsDialog, self, self.conn,
                   item)

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
        self.set_print_button_sensitive(has_one_selected)

    def _has_rows(self, results, obj):
        pass

    def create_filters(self):
        self.set_text_field_columns(['reason'])
        self.set_searchbar_labels(_('matching:'))

        # Date
        date_filter = DateSearchFilter(_('Date:'))
        self.add_filter(date_filter, columns=['confirm_date'])

    def get_columns(self):
        return [Column('id', _('#'), data_type=int, width=50),
                Column('confirm_date', _('Date'),
                       data_type=datetime.date, sorted=True, width=100),
                Column('branch_name', _('Branch'),
                       data_type=unicode, expand=True),
                Column('removed_by_name', _('Removed By'),
                       data_type=unicode, width=120),
                Column('total_items_removed',
                       _('Items removed'), data_type=Decimal, width=110),
                Column('cfop_description', u'CFOP', data_type=unicode,
                       expand=True)
                       ]

    #
    # Callbacks
    #

    def on_row_activated(self, klist, item):
        self._show_details(item)

    def on_print_button_clicked(self, button):
        orders = self.results.get_selected_rows()
        if len(orders) == 1:
            print_report(StockDecreaseReceipt, orders[0])

    def on_details_button_clicked(self, button):
        orders = self.results.get_selected_rows()
        if len(orders) > 1:
            raise ValueError("You should have only one item selected at "
                             "this point ")
        self._show_details(orders[0])
