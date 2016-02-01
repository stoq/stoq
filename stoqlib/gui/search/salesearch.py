# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2015 Async Open Source <http://www.async.com.br>
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
""" Search dialogs for sale objects """


import datetime
from decimal import Decimal

import pango
import gtk
from kiwi.currency import currency
from kiwi.ui.objectlist import Column
from storm.expr import Count, And

from stoqlib.api import api
from stoqlib.domain.sale import (Sale,
                                 SaleView,
                                 SalePaymentMethodView,
                                 SoldItemsByClient,
                                 SaleToken)
from stoqlib.domain.person import Branch
from stoqlib.domain.till import Till
from stoqlib.domain.views import SoldItemsByBranchView, UnconfirmedSaleItemsView
from stoqlib.domain.workorder import WorkOrder
from stoqlib.exceptions import TillError
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.gtkadds import set_bold
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.editors.saleeditor import SaleTokenEditor
from stoqlib.gui.search.searchcolumns import (IdentifierColumn, SearchColumn,
                                              QuantityColumn)
from stoqlib.gui.search.searcheditor import SearchEditor
from stoqlib.gui.search.searchfilters import (ComboSearchFilter,
                                              DateSearchFilter)
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.formatters import (format_quantity, get_formatted_price,
                                    format_phone_number)
from stoqlib.gui.slaves.saleslave import SaleListToolbar
from stoqlib.reporting.sale import (SoldItemsByBranchReport,
                                    SoldItemsByClientReport)

_ = stoqlib_gettext


class _BaseSaleSearch(SearchDialog):
    title = _("Search for Sales")
    size = (-1, 450)
    search_spec = SaleView
    text_field_columns = [SaleView.client_name, SaleView.salesperson_name,
                          SaleView.identifier_str]
    branch_filter_column = SaleView.branch_id

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        items = [(value, key) for key, value in Sale.statuses.items()]
        items.insert(0, (_('Any'), None))

        status_filter = ComboSearchFilter(_('Show sales with status'), items)
        self.add_filter(status_filter, columns=[SaleView.status])

    def get_columns(self):
        return [IdentifierColumn('identifier', title=_('Sale #'), sorted=True,
                                 order=gtk.SORT_DESCENDING),
                SearchColumn('open_date', title=_('Date Started'), width=110,
                             data_type=datetime.date, justify=gtk.JUSTIFY_RIGHT),
                SearchColumn('client_name', title=_('Client'),
                             data_type=str, expand=True,
                             ellipsize=pango.ELLIPSIZE_END),
                SearchColumn('salesperson_name', title=_('Salesperson'),
                             data_type=str, width=150),
                SearchColumn('total_quantity', title=_('Items'),
                             data_type=Decimal, width=60,
                             format_func=format_quantity),
                SearchColumn('total', title=_('Total'), data_type=currency,
                             width=90)]


class SaleWithToolbarSearch(_BaseSaleSearch):

    #
    # _BaseSaleSearch
    #

    def setup_widgets(self):
        self._sale_toolbar = SaleListToolbar(self.store, self.results, self)
        self._sale_toolbar.connect('sale-returned', self._on_sale__returned)
        self._sale_toolbar.update_buttons()
        self.attach_slave("extra_holder", self._sale_toolbar)
        self.results.connect(
            'selection-changed', self._on_results__selection_changed)

        self.search.set_summary_label('total', label=_(u'Total:'),
                                      format='<b>%s</b>')

    #
    # Private
    #

    def _update_widgets(self, sale_view):
        sale = sale_view and sale_view.sale
        try:
            till = Till.get_current(self.store)
        except TillError:
            till = None

        can_edit = bool(sale and sale.can_edit())
        # We need an open till to return sales
        if sale and till:
            can_return = sale.can_return() or sale.can_cancel()
        else:
            can_return = False

        self._sale_toolbar.return_sale_button.set_sensitive(can_return)
        self._sale_toolbar.edit_button.set_sensitive(can_edit)

    #
    # Callbacks
    #

    def _on_results__selection_changed(self, results, sale_view):
        self._update_widgets(sale_view)

    def _on_sale__returned(self, slave, sale_returned):
        if sale_returned:
            self._update_widgets(self.results.get_selected())


class SaleSearch(_BaseSaleSearch):

    #
    # Callbacks
    #

    def on_details_button_clicked(self, button):
        sale_view = self.results.get_selected()
        if not sale_view:
            return

        run_dialog(SaleDetailsDialog, self, self.store, sale_view)


class SalesByPaymentMethodSearch(SaleWithToolbarSearch):
    title = _(u'Search for Sales by Payment Method')
    search_spec = SalePaymentMethodView
    search_label = _('Items matching:')
    size = (800, 450)
    branch_filter_column = Branch.id
    text_field_columns = [SalePaymentMethodView.client_name,
                          SalePaymentMethodView.salesperson_name]

    def create_filters(self):
        self.search.set_query(self.executer_query)

        payment_filter = self.create_payment_filter(_('Payment Method:'))
        self.add_filter(payment_filter, columns=[])
        self.payment_filter = payment_filter

    # TODO: Maybe this can be removed
    def executer_query(self, store):
        method = self.payment_filter.get_state().value
        resultset = self.search_spec.find_by_payment_method(store, method)
        return resultset

    def get_columns(self):
        columns = SaleWithToolbarSearch.get_columns(self)
        branches = api.get_branches_for_filter(self.store, use_id=True)
        branch_column = SearchColumn('branch_name', title=_('Branch'), width=110,
                                     data_type=str, search_attribute='branch_id',
                                     valid_values=branches)
        columns.insert(3, branch_column)
        return columns


class SoldItemsByBranchSearch(SearchDialog):
    title = _(u'Sold Items by Branch')
    report_class = SoldItemsByBranchReport
    search_spec = SoldItemsByBranchView
    search_label = _('Items matching:')
    size = (800, 450)
    unlimited_results = True
    text_field_columns = [SoldItemsByBranchView.description]
    branch_filter_column = Sale.branch_id

    def setup_widgets(self):
        self.add_csv_button(_('Sales'), _('sales'))
        self._setup_summary()

    def _setup_summary(self):
        hbox = gtk.HBox()
        hbox.set_spacing(6)

        self.vbox.pack_start(hbox, False, True)
        self.vbox.reorder_child(hbox, 2)
        self.vbox.set_spacing(6)

        hbox.pack_start(gtk.Label(), True, True)

        # Create some labels to show a summary for the search (kiwi's
        # SummaryLabel supports only one column)
        self.items_label = gtk.Label()
        self.quantity_label = gtk.Label()
        self.items_per_sale_label = gtk.Label()
        self.total_label = gtk.Label()
        for widget in [self.items_label, self.quantity_label,
                       self.items_per_sale_label, self.total_label]:
            hbox.pack_start(widget, False, False)
            set_bold(widget)

        hbox.show_all()

    def _update_summary(self, results):
        total_quantity = total = 0
        for obj in results:
            total_quantity += obj.quantity
            total += obj.total

        queries, having = self.search.parse_states()
        sale_results = self.store.using(*self.search_spec.tables)
        sale_results = sale_results.find(Count(Sale.id, distinct=True))
        if queries:
            sale_results = sale_results.find(And(*queries))

        sales = sale_results.one()
        items_per_sale = total_quantity / sales if sales > 0 else 0

        self.items_label.set_label(_(u'Sales: %s') %
                                   format_quantity(sales))
        self.quantity_label.set_label(_(u'Quantity: %s') %
                                      format_quantity(total_quantity))
        self.items_per_sale_label.set_label(_(u'Items per sale: %s') %
                                            format_quantity(items_per_sale))
        self.total_label.set_label(_(u'Total: %s') %
                                   get_formatted_price(total))

    def create_filters(self):
        date_filter = DateSearchFilter(_('Date:'))
        self.search.add_filter(date_filter, columns=[Sale.confirm_date])
        self.date_filter = date_filter

    def get_columns(self):
        return [SearchColumn('code', title=_('Code'), data_type=str,
                             sorted=True, order=gtk.SORT_DESCENDING),
                SearchColumn('description', title=_('Product'), data_type=str,
                             expand=True),
                SearchColumn('category', title=_('Category'), data_type=str,
                             visible=False),
                SearchColumn('branch_name', title=_('Branch'), data_type=str,
                             width=200),
                Column('quantity', title=_('Quantity'), data_type=Decimal,
                       format_func=format_quantity, width=100),
                Column('total', title=_('Total'), data_type=currency, width=80)
                ]

    def on_search__search_completed(self, search, result_view, states):
        self._update_summary(result_view)


class SoldItemsByClientSearch(SearchDialog):
    title = _(u'Sold Items by Client')
    report_class = SoldItemsByClientReport
    search_spec = SoldItemsByClient
    size = (800, 450)
    unlimited_results = True
    text_field_columns = [SoldItemsByClient.client_name,
                          SoldItemsByClient.description,
                          SoldItemsByClient.code]
    branch_filter_column = Sale.branch_id

    def setup_widgets(self):
        self.add_csv_button(_('Sale items'), _('sale items'))

    def create_filters(self):
        self._date_filter = DateSearchFilter(_("Date:"))
        self._date_filter.select(data=DateSearchFilter.Type.USER_INTERVAL)
        self.add_filter(self._date_filter, columns=[Sale.confirm_date])
        self.search.set_summary_label('quantity', label=_(u'Total:'),
                                      format='<b>%s</b>')

    def get_columns(self):
        columns = [
            SearchColumn('code', title=_('Code'), data_type=str, sorted=True,
                         order=gtk.SORT_DESCENDING),
            SearchColumn('description', title=_('Description'),
                         data_type=str, expand=True),
            SearchColumn('client_name', title=_('Client'), data_type=str),
            SearchColumn('phone_number', title=_('Phone'), data_type=str,
                         visible=False, format_func=format_phone_number),
            SearchColumn('email', title=_('Email'), data_type=str,
                         visible=False),
            SearchColumn('sellable_category', title=_('Category'), data_type=str,
                         visible=False),
            QuantityColumn('quantity', title=_('Qty'), use_having=True),
            SearchColumn('price', title=_('Avg price'), data_type=currency,
                         use_having=True),
            SearchColumn('total', title=_('Total'), data_type=currency,
                         use_having=True)
        ]
        return columns


class UnconfirmedSaleItemsSearch(SearchDialog):
    title = _(u'Unconfirmed Sale Items Search')
    search_spec = UnconfirmedSaleItemsView
    size = (850, 450)
    branch_filter_column = Sale.branch_id
    unlimited_results = True
    text_field_columns = [UnconfirmedSaleItemsView.description,
                          UnconfirmedSaleItemsView.salesperson_name,
                          UnconfirmedSaleItemsView.client_name]

    def setup_widgets(self):
        self.sale_details_button = self.add_button(label=_('Sale Details'))
        self.sale_details_button.show()
        self.sale_details_button.set_sensitive(False)
        self.add_csv_button(_('Sale items'), _('sale-items'))
        self._setup_summary()

    def update_widgets(self):
        reserved_product_view = self.results.get_selected()
        self.sale_details_button.set_sensitive(bool(reserved_product_view))

    def get_columns(self):
        return [IdentifierColumn('identifier', title=_('Sale #'),
                                 sorted=True, order=gtk.SORT_DESCENDING),
                SearchColumn('status_str', title=_('Status'),
                             search_attribute='status',
                             valid_values=self._get_status_values(), data_type=str),
                SearchColumn('product_code', title=_('Code'), data_type=str),
                SearchColumn('product_category', title=_('Category'), data_type=str),
                SearchColumn('description', title=_('Product'), data_type=str,
                             expand=True),
                SearchColumn('manufacturer_name', title=_('Manufacturer'),
                             data_type=str, expand=True, visible=False),
                SearchColumn('salesperson_name', title=_('Sales Person'),
                             data_type=str, visible=False),
                SearchColumn('client_name', title=_('Client'), data_type=str,
                             visible=False),
                SearchColumn('open_date', title=_('Open Date'),
                             data_type=datetime.date),
                SearchColumn('price', title=_('Price'), data_type=currency,),
                SearchColumn('quantity', title=_('Quantity'), data_type=Decimal,
                             format_func=format_quantity),
                SearchColumn('quantity_decreased', title=_('Delivered'),
                             data_type=Decimal, format_func=format_quantity,
                             visible=False),
                SearchColumn('total', title=_('Total'), data_type=currency,),
                IdentifierColumn('wo_identifier', title=_('WO #'),
                                 visible=False, justify=gtk.JUSTIFY_RIGHT),
                SearchColumn('wo_status_str', title=_('WO Status'), data_type=str,
                             search_attribute='wo_status', visible=False,
                             valid_values=self._get_wo_status_values()),
                SearchColumn('wo_estimated_finish', title=_('Estimated finish'),
                             data_type=datetime.date, visible=False),
                SearchColumn('wo_finish', title=_('WO Finish date'),
                             data_type=datetime.date, visible=False)]

    def _setup_summary(self):
        hbox = gtk.HBox()
        hbox.set_spacing(6)

        self.vbox.pack_start(hbox, False, True)
        self.vbox.reorder_child(hbox, 2)
        self.vbox.set_spacing(6)

        hbox.pack_start(gtk.Label(), True, True)

        # Create some labels to show a summary for the search (kiwi's
        # SummaryLabel supports only one column)
        self.quantity_label = gtk.Label()
        self.reserved_label = gtk.Label()
        self.total_label = gtk.Label()
        for widget in [self.quantity_label, self.reserved_label,
                       self.total_label]:
            hbox.pack_start(widget, False, False)
            set_bold(widget)

        hbox.show_all()

    def _update_summary(self, results):
        total_quantity = reserved_quantity = total_price = 0
        for obj in results:
            total_quantity += obj.quantity
            reserved_quantity += obj.quantity_decreased
            total_price += obj.total

        self.quantity_label.set_label(_(u'Quantity: %s') %
                                      format_quantity(total_quantity))
        self.reserved_label.set_label(_(u'Delivered: %s') %
                                      format_quantity(reserved_quantity))
        self.total_label.set_label(_(u'Total: %s') %
                                   get_formatted_price(total_price))

    def _get_status_values(self):
        items = [(value, key) for key, value in Sale.statuses.items()
                 if key in [Sale.STATUS_ORDERED, Sale.STATUS_QUOTE]]
        items.insert(0, (_('Any'), None))
        return items

    def _get_wo_status_values(self):
        items = [(value, key) for key, value in WorkOrder.statuses.items()]
        items.insert(0, (_('Any'), None))
        return items

    def on_sale_details_button__clicked(self, widget):
        reserved_product_view = self.results.get_selected()
        sale_view = self.store.find(SaleView, id=reserved_product_view.sale_id).one()
        run_dialog(SaleDetailsDialog, self, self.store, sale_view)

    def on_search__search_completed(self, search, result_view, states):
        self._update_summary(result_view)


class SaleTokenSearch(SearchEditor):
    title = _(u'Sale Token Search')
    size = (500, 400)
    search_spec = SaleToken
    editor_class = SaleTokenEditor
    text_field_columns = [SaleToken.code]

    def __init__(self, store, search_str=None, hide_toolbar=False,
                 hide_footer=False):
        SearchEditor.__init__(self, store, search_spec=self.search_spec,
                              editor_class=self.editor_class,
                              hide_toolbar=hide_toolbar,
                              hide_footer=hide_footer)

    def get_columns(self):
        return [SearchColumn('code', title=_('Code'), data_type=str,
                             sorted=True, expand=True),
                Column('status_str', title=_('Status'), data_type=str)]
