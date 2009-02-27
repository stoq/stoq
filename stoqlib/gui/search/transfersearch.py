# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   George Kussumoto     <george@async.com.br>
##
##
""" Search dialogs for transfer order"""

import datetime
from decimal import Decimal

import gtk
from kiwi.ui.search import DateSearchFilter
from kiwi.ui.objectlist import Column

from stoqlib.domain.transfer import TransferOrder, TransferOrderItem
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.search import SearchDialog
from stoqlib.gui.dialogs.transferorderdialog import TransferOrderDetailsDialog
from stoqlib.gui.printing import print_report
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.transfer_receipt import TransferOrderReceipt

_ = stoqlib_gettext


class TransferOrderSearch(SearchDialog):
    title = _(u"Transfer Order Search")
    size = (750, 500)
    search_table = TransferOrder
    selection_mode = gtk.SELECTION_MULTIPLE
    searchbar_result_strings = _(u"transfer order"), _(u"transfer orders")
    search_by_date = True
    advanced_search = False

    def __init__(self, conn):
        SearchDialog.__init__(self, conn, self.search_table,
                              title=self.title)
        self._setup_widgets()

    def _show_transfer_order_details(self, transfer_order):
        run_dialog(TransferOrderDetailsDialog, self, self.conn,
                   transfer_order)

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
        self.set_text_field_columns(['id'])
        self.set_searchbar_labels(_('matching:'))

        # Date
        date_filter = DateSearchFilter(_('Date:'))
        self.add_filter(date_filter, columns=['open_date', 'receival_date'])

    def get_columns(self):
        return [Column('id', _('#'), data_type=int, width=50),
                Column('open_date', _('Open Date'),
                       data_type=datetime.date, sorted=True, width=100),
                Column('source_branch_name', _('Source'),
                       data_type=unicode, expand=True),
                Column('destination_branch_name', _('Destination'),
                       data_type=unicode, width=220),
                Column('total_items_transfer',
                       _('Number of items transferred'), data_type=Decimal, width=110)]

    #
    # Callbacks
    #

    def on_row_activated(self, klist, transfer_order):
        self._show_transfer_order_details(transfer_order)

    def on_print_button_clicked(self, button):
        orders = self.results.get_selected_rows()
        if len(orders) == 1:
            items = TransferOrderItem.selectBy(transfer_order=orders[0],
                                               connection=self.conn)
            print_report(TransferOrderReceipt, orders[0], items,
                         filters=self.search.get_search_filters())

    def on_details_button_clicked(self, button):
        orders = self.results.get_selected_rows()
        if len(orders) > 1:
            raise ValueError("You should have only one item selected at "
                             "this point ")
        self._show_transfer_order_details(orders[0])
