# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
from stoqlib.domain.sale import SaleView
from stoqlib.domain.views import ReturnedSalesView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.search.searchcolumns import SearchColumn, IdentifierColumn
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.sale import ReturnedSalesReport


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
        sale_view = self.store.find(SaleView, id=item_view.sale_id).one()
        run_dialog(SaleDetailsDialog, self, self.store,
                   sale_view)

    #
    # SearchDialog Hooks
    #

    def update_widgets(self):
        selected = self.get_selection()
        self.set_details_button_sensitive(bool(selected))
        self.set_print_button_sensitive(bool(selected))

    def get_columns(self):
        return [IdentifierColumn('identifier', title=_(u"Item #")),
                IdentifierColumn('sale_identifier', _('Sale #')),
                SearchColumn('client_name', _('Client'), expand=True,
                             data_type=str),
                SearchColumn('return_date', _('Return Date'),
                             data_type=datetime.date, sorted=True),
                SearchColumn('reason', _('Return Reason'),
                             data_type=str),
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
