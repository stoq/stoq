# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
##
""" Search dialogs for purchase receiving"""

import datetime

import gtk
from kiwi.datatypes import currency
from kiwi.enums import SearchFilterPosition
from kiwi.ui.search import DateSearchFilter
from kiwi.ui.objectlist import SearchColumn

from stoqlib.domain.receiving import ReceivingOrder
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.search import SearchDialog
from stoqlib.gui.dialogs.receivingdialog import ReceivingOrderDetailsDialog
from stoqlib.gui.printing import print_report
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.reporting.purchase_receival import PurchaseReceivalReport

_ = stoqlib_gettext


class PurchaseReceivingSearch(SearchDialog):
    title = _('Purchase Receiving Search')
    size = (750, 500)
    table = ReceivingOrder
    selection_mode = gtk.SELECTION_MULTIPLE
    searchbar_result_strings = _('receiving order'), _('receiving orders')

    def __init__(self, conn):
        SearchDialog.__init__(self, conn, self.search_table,
                              title=self.title)
        self._setup_widgets()

    def _show_receiving_order(self, receiving_order):
        run_dialog(ReceivingOrderDetailsDialog, self, self.conn,
                   receiving_order)

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_searchbar_labels(_('matching:'))
        self.set_text_field_columns(['id'])

        # Branch
        branch_filter = self.create_branch_filter(_(u"In branch"))
        self.add_filter(branch_filter, columns=['branchID'],
                        position=SearchFilterPosition.TOP)

    def get_columns(self):
        return [SearchColumn('purchase.id', _('Purchase Order #'),
                             data_type=int, width=120),
                SearchColumn('receival_date', _('Receival Date'),
                             data_type=datetime.date, sorted=True, width=110),
                SearchColumn('supplier_name', _('Supplier'), data_type=unicode,
                             expand=True),
                SearchColumn('invoice_number', _('Invoice #'), data_type=int,
                             width=80),
                SearchColumn('invoice_total', _('Invoice Total'),
                             data_type=currency, width=120)]

    #
    # Private
    #

    def _setup_widgets(self):
        self.results.connect('row_activated', self.on_row_activated)
        self.set_details_button_sensitive(False)

    #
    # Callbacks
    #

    def on_row_activated(self, klist, receiving_order):
        self._show_receiving_order(receiving_order)

    def on_print_button_clicked(self, button):
        print_report(PurchaseReceivalReport, self.results,
                     filters=self.search.get_search_filters())

    def on_details_button_clicked(self, button):
        items = self.results.get_selected_rows()
        if  not len(items) == 1:
            raise ValueError("You should have only one item selected at "
                             "this point ")
        selected = items[0]
        order = ReceivingOrder.get(selected.id, connection=self.conn)
        self._show_receiving_order(order)

    def update_widgets(self, *args):
        items = self.results.get_selected_rows()
        has_one_selected = len(items) == 1
        self.set_details_button_sensitive(has_one_selected)
