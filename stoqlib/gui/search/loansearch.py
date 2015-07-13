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
""" Search dialogs for loans and related objects """

import datetime
from decimal import Decimal

import gtk
from kiwi.currency import currency
from kiwi.ui.objectlist import Column

from stoqlib.domain.loan import Loan
from stoqlib.domain.views import LoanView, LoanItemView
from stoqlib.enums import SearchFilterPosition
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.loandetails import LoanDetailsDialog
from stoqlib.gui.search.productsearch import ProductSearch
from stoqlib.gui.search.searchcolumns import SearchColumn, IdentifierColumn
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.gui.search.searchfilters import ComboSearchFilter, DateSearchFilter
from stoqlib.gui.utils.printing import print_report
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.loanreceipt import LoanReceipt

_ = stoqlib_gettext


class LoanItemSearch(ProductSearch):
    title = _(u'Loan Items Search')
    search_spec = LoanItemView
    has_print_price_button = False
    text_field_columns = [LoanItemView.description, LoanItemView.identifier_str]

    def __init__(self, store, hide_footer=True, hide_toolbar=True):
        ProductSearch.__init__(self, store, hide_footer=hide_footer,
                               hide_toolbar=hide_toolbar)

    #
    #  ProductSearch
    #

    def create_filters(self):
        # status filter
        statuses = [(desc, i) for i, desc in Loan.statuses.items()]
        statuses.insert(0, (_(u'Any'), None))
        status_filter = ComboSearchFilter(_(u'with status:'), statuses)
        status_filter.select(None)
        self.add_filter(status_filter, columns=['loan_status'],
                        position=SearchFilterPosition.TOP)

    def get_columns(self):
        return [IdentifierColumn('loan_identifier', title=_('Loan #'), sorted=True),
                SearchColumn('opened', title=_(u'Open date'),
                             data_type=datetime.date, visible=False),
                SearchColumn('closed', title=_(u'Close date'),
                             data_type=datetime.date, ),
                SearchColumn('code', title=_(u'Code'), data_type=str,
                             visible=False),
                SearchColumn('category_description', title=_(u'Category'),
                             data_type=str, visible=False),
                SearchColumn('description', title=_(u'Description'),
                             data_type=str, expand=True),
                SearchColumn('quantity', title=_(u'Quantity'),
                             data_type=Decimal),
                SearchColumn('sale_quantity', title=_(u'Sold'),
                             data_type=Decimal),
                SearchColumn('return_quantity', title=_(u'Returned'),
                             data_type=Decimal),
                SearchColumn('price', title=_(u'Price'),
                             data_type=currency),
                SearchColumn('total', title=_(u'Total'),
                             data_type=currency)]


class LoanSearch(SearchDialog):
    title = _(u"Loan Search")
    size = (750, 500)
    search_spec = LoanView
    report_class = LoanReceipt
    selection_mode = gtk.SELECTION_MULTIPLE
    advanced_search = False

    def __init__(self, store):
        SearchDialog.__init__(self, store)
        self._setup_widgets()

    def _show_details(self, item):
        run_dialog(LoanDetailsDialog, self, self.store,
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
        self.set_text_field_columns(['client_name', 'removed_by',
                                     'identifier_str'])

        # Date
        self.date_filter = DateSearchFilter(_('Date:'))
        self.add_filter(self.date_filter, columns=['expire_date', 'open_date'])

    def get_columns(self):
        return [IdentifierColumn('identifier', title=_(u"Loan #")),
                Column('open_date', _('Open date'),
                       data_type=datetime.date, sorted=True, width=100),
                Column('expire_date', _('Expire date'),
                       data_type=datetime.date, width=100),
                Column('branch_name', _('Branch'),
                       data_type=unicode, expand=True),
                Column('client_name', _('Client'),
                       data_type=unicode, width=120),
                Column('removed_by', _('Removed by'), data_type=unicode,
                       width=120),
                ]

    def print_report(self):
        orders = self.results.get_selected_rows()
        if len(orders) == 1:
            loan = self.store.get(Loan, orders[0].id)
            print_report(self.report_class, loan)

    #
    # Callbacks
    #

    def on_row_activated(self, klist, item_view):
        item = item_view.loan
        self._show_details(item)

    def on_details_button_clicked(self, button):
        orders = self.results.get_selected_rows()
        if len(orders) > 1:
            raise ValueError("You should have only one item selected at "
                             "this point ")
        loan = self.store.get(Loan, orders[0].id)
        self._show_details(loan)
