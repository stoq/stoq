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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Search dialogs for purchase receiving"""

import datetime

import gtk
from kiwi.currency import currency

from stoqlib.domain.views import PurchaseReceivingView
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.search.searchcolumns import IdentifierColumn, SearchColumn
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.gui.dialogs.receivingdialog import ReceivingOrderDetailsDialog
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.reporting.purchasereceival import PurchaseReceivalReport

_ = stoqlib_gettext


class PurchaseReceivingSearch(SearchDialog):
    title = _('Purchase Receiving Search')
    size = (750, 500)
    search_spec = PurchaseReceivingView
    report_class = PurchaseReceivalReport
    selection_mode = gtk.SELECTION_MULTIPLE
    branch_filter_column = PurchaseReceivingView.branch_id
    text_field_columns = [PurchaseReceivingView.supplier_name,
                          PurchaseReceivingView.responsible_name,
                          PurchaseReceivingView.purchase_responsible_name,
                          PurchaseReceivingView.purchase_identifier_str]

    def __init__(self, store):
        SearchDialog.__init__(self, store)
        self._setup_widgets()

    def _show_receiving_order(self, receiving_order_view):
        order = receiving_order_view.order
        run_dialog(ReceivingOrderDetailsDialog, self, self.store, order)

    #
    # SearchDialog Hooks
    #

    def get_columns(self):
        return [IdentifierColumn('purchase_identifier', _('Purchase #')),
                SearchColumn('receival_date', _('Receival date'),
                             data_type=datetime.date, sorted=True, width=110),
                SearchColumn('supplier_name', _('Supplier'), data_type=str,
                             expand=True),
                SearchColumn('responsible_name', _('Responsible'),
                             data_type=str, visible=False, expand=True),
                SearchColumn('purchase_responsible_name', _('Purchaser'),
                             data_type=str, visible=False, expand=True),
                SearchColumn('invoice_number', _('Invoice #'), data_type=int,
                             width=80),
                SearchColumn('invoice_total', _('Invoice total'),
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

    def on_details_button_clicked(self, button):
        items = self.results.get_selected_rows()
        if not len(items) == 1:
            raise ValueError("You should have only one item selected at "
                             "this point ")
        selected = items[0]
        self._show_receiving_order(selected)

    def update_widgets(self, *args):
        items = self.results.get_selected_rows()
        has_one_selected = len(items) == 1
        self.set_details_button_sensitive(has_one_selected)
