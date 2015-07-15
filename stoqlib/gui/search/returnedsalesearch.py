# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013-2015 Async Open Source <http://www.async.com.br>
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
""" Search dialogs for returned sales """

import datetime

from stoqlib.domain.person import Branch
from stoqlib.domain.sale import Sale
from stoqlib.domain.views import (ReturnedSalesView, PendingReturnedSalesView,
                                  ReturnedItemView)
from stoqlib.domain.returnedsale import ReturnedSale
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.returnedsaledialog import ReturnedSaleDialog
from stoqlib.gui.search.searchcolumns import (QuantityColumn, SearchColumn,
                                              IdentifierColumn)
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.sale import ReturnedSalesReport, ReturnedItemReport


_ = stoqlib_gettext


class ReturnedSaleSearch(SearchDialog):
    title = _(u"Returned Sale Search")
    size = (830, 520)
    search_spec = ReturnedSalesView
    report_class = ReturnedSalesReport
    branch_filter_column = Branch.id
    text_field_columns = [ReturnedSalesView.identifier_str,
                          ReturnedSalesView.sale_identifier_str,
                          ReturnedSalesView.client_name,
                          ReturnedSalesView.responsible_name]

    def __init__(self, store):
        SearchDialog.__init__(self, store)
        self._setup_widgets()

    def _setup_widgets(self):
        self.results.connect('row_activated', self.on_row_activated)
        self.update_widgets()

    def _show_details(self, item_view):
        run_dialog(ReturnedSaleDialog, self, self.store, item_view)

    def _get_status_values(self):
        items = [(value, key) for key, value in ReturnedSale.statuses.items()]
        items.insert(0, (_('Any'), None))
        return items

    #
    # SearchDialog Hooks
    #

    def update_widgets(self):
        selected = self.get_selection()
        self.set_details_button_sensitive(bool(selected))
        self.set_print_button_sensitive(bool(selected))

    def get_columns(self):
        # TODO: Add status column
        return [IdentifierColumn('identifier', title=_(u"Item #")),
                IdentifierColumn('sale_identifier', _('Sale #')),
                SearchColumn('status_str', _('Status'),
                             data_type=str, search_attribute='status',
                             valid_values=self._get_status_values()),
                SearchColumn('client_name', _('Client'), expand=True,
                             data_type=str),
                SearchColumn('return_date', _('Return Date'),
                             data_type=datetime.date, sorted=True),
                SearchColumn('reason', _('Return Reason'),
                             data_type=str, visible=False),
                SearchColumn('responsible_name', _('Responsible'),
                             data_type=str),
                SearchColumn('branch_name', _('Branch'),
                             data_type=str, visible=False),
                SearchColumn('invoice_number', _('Invoice number'),
                             data_type=int, visible=False),
                ]

    #
    # Callbacks
    #

    def on_row_activated(self, klist, item_view):
        self._show_details(item_view)

    def on_details_button_clicked(self, button):
        selected_returns = self.results.get_selected_rows()
        if len(selected_returns) > 1:
            raise ValueError("You should have only one item selected at "
                             "this point ")
        self._show_details(selected_returns[0])


class PendingReturnedSaleSearch(ReturnedSaleSearch):
    title = _(u"Pending Returned Sale Search")
    size = (830, 520)
    search_spec = PendingReturnedSalesView
    branch_filter_column = Sale.branch_id

    def _show_pending_returned_sale_details(self, order_view):
        run_dialog(ReturnedSaleDialog, self, self.store, order_view)

    def get_columns(self):
        return [IdentifierColumn('identifier', title=_(u"Returned #")),
                IdentifierColumn('sale_identifier', _('Sale #')),
                SearchColumn('client_name', _('Client'), expand=True,
                             data_type=str),
                SearchColumn('return_date', _('Return Date'),
                             data_type=datetime.date, sorted=True),
                SearchColumn('reason', _('Return Reason'),
                             data_type=str),
                SearchColumn('responsible_name', _('Responsible'),
                             data_type=str),
                SearchColumn('branch_name', _('Returned on Branch'),
                             data_type=str),
                SearchColumn('invoice_number', _('Invoice number'),
                             data_type=int, visible=False),
                ]

    def on_details_button_clicked(self, button):
        self._show_pending_returned_sale_details(self.results.get_selected())

    def on_row_activated(self, klist, item_view):
        self._show_pending_returned_sale_details(item_view)


class ReturnedItemSearch(ReturnedSaleSearch):
    title = _(u"Returned Sale Item Search")
    search_spec = ReturnedItemView
    report_class = ReturnedItemReport
    branch_filter_column = Sale.branch_id
    text_field_columns = [ReturnedItemView.item_description,
                          ReturnedItemView.responsible_name]

    def get_columns(self):
        return [IdentifierColumn('identifier', title=_(u"Returned #")),
                SearchColumn('status_str', _('Status'),
                             data_type=str, search_attribute='status',
                             valid_values=self._get_status_values()),
                SearchColumn('item_description', title=_(u"Item")),
                QuantityColumn('item_quantity', title=_(u"Qty")),
                SearchColumn('client_name', _('Client'), expand=True,
                             data_type=str),
                SearchColumn('return_date', _('Return Date'),
                             data_type=datetime.date, sorted=True),
                SearchColumn('reason', _('Return Reason'),
                             data_type=str, visible=False),
                SearchColumn('responsible_name', _('Responsible'),
                             data_type=str),
                SearchColumn('branch_name', _('Return branch'),
                             data_type=str, visible=False),
                SearchColumn('invoice_number', _('Invoice number'),
                             data_type=int, visible=False),
                ]
