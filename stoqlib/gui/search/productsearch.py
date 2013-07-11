# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
""" Search dialogs for product objects """

from decimal import Decimal

import gtk
from kiwi.currency import currency
from kiwi.ui.objectlist import Column, ColoredColumn
from storm.expr import Eq

from stoqlib.api import api
from stoqlib.database.queryexecuter import DateQueryState, DateIntervalQueryState
from stoqlib.domain.person import Branch
from stoqlib.domain.product import Product, ProductHistory
from stoqlib.domain.views import (ProductQuantityView,
                                  ProductFullStockItemView, SoldItemView,
                                  ProductFullWithClosedStockView,
                                  ProductClosedStockView,
                                  ProductBranchStockView, ProductBrandStockView)
from stoqlib.enums import SearchFilterPosition
from stoqlib.gui.base.gtkadds import change_button_appearance
from stoqlib.gui.dialogs.spreadsheetexporterdialog import SpreadSheetExporter
from stoqlib.gui.editors.producteditor import (ProductEditor,
                                               ProductStockEditor)
from stoqlib.gui.search.searchcolumns import SearchColumn
from stoqlib.gui.search.searchdialog import SearchDialog, SearchDialogPrintSlave
from stoqlib.gui.search.searcheditor import SearchEditor
from stoqlib.gui.search.searchfilters import DateSearchFilter, Today
from stoqlib.gui.utils.printing import print_report
from stoqlib.lib.defaults import sort_sellable_code
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.formatters import format_quantity, get_formatted_cost
from stoqlib.reporting.product import (ProductReport, ProductQuantityReport,
                                       ProductClosedStockReport,
                                       ProductPriceReport, ProductStockReport,
                                       ProductsSoldReport, ProductBrandReport)

_ = stoqlib_gettext


class ProductSearch(SearchEditor):
    title = _('Product Search')
    table = Product
    size = (775, 450)
    search_spec = ProductFullWithClosedStockView
    editor_class = ProductEditor
    footer_ok_label = _('Add products')

    def __init__(self, store, hide_footer=True, hide_toolbar=False,
                 selection_mode=None,
                 hide_cost_column=False, use_product_statuses=None,
                 hide_price_column=False):
        """
        Create a new ProductSearch object.
        :param store: a store
        :param hide_footer: do I have to hide the dialog footer?
        :param hide_toolbar: do I have to hide the dialog toolbar?
        :param selection_mode: the kiwi list selection mode
        :param hide_cost_column: if it's True, no need to show the
                                 column 'cost'
        :param use_product_statuses: a list instance that, if provided, will
                                     overwrite the statuses list defined in
                                     get_filter_slave method
        :param hide_price_column: if it's True no need to show the
                                  column 'price'
        """
        if selection_mode is None:
            selection_mode = gtk.SELECTION_BROWSE
        self.use_product_statuses = use_product_statuses
        self.hide_cost_column = hide_cost_column
        self.hide_price_column = hide_price_column
        SearchEditor.__init__(self, store, hide_footer=hide_footer,
                              hide_toolbar=hide_toolbar,
                              selection_mode=selection_mode)
        self._setup_print_slave()

    def _setup_print_slave(self):
        self._print_slave = SearchDialogPrintSlave()
        change_button_appearance(self._print_slave.print_price_button,
                                 gtk.STOCK_PRINT, _("_Price table"))
        self.attach_slave('print_holder', self._print_slave)
        self._print_slave.connect('print', self.on_print_price_button_clicked)
        self._print_slave.print_price_button.set_sensitive(False)
        self.results.connect('has-rows', self._has_rows)

    def on_print_button_clicked(self, button):
        print_report(ProductReport, self.results, list(self.results),
                     filters=self.search.get_search_filters())

    def on_print_price_button_clicked(self, button):
        print_report(ProductPriceReport, list(self.results),
                     filters=self.search.get_search_filters(),
                     branch_name=self.branch_filter.combo.get_active_text())

    def _has_rows(self, results, obj):
        SearchEditor._has_rows(self, results, obj)
        self._print_slave.print_price_button.set_sensitive(obj)

    #
    # SearchDialog Hooks
    #

    def setup_widgets(self):
        self.csv_button = self.add_button(label=_('Export to spreadsheet...'))
        self.csv_button.show()
        self.csv_button.set_sensitive(False)

        self.branch_stock_button = self.add_button(label=_('Stocks details'))
        self.branch_stock_button.show()
        self.branch_stock_button.set_sensitive(False)

    def create_filters(self):
        self.set_text_field_columns(['description', 'barcode',
                                     'category_description'])
        self.search.set_query(self.executer_query)

        # Branch
        branch_filter = self.create_branch_filter(_('In branch:'))
        self.add_filter(branch_filter, columns=[])
        self.branch_filter = branch_filter

        # Status
        status_filter = self.create_sellable_filter()
        self.add_filter(status_filter, columns=['status'],
                        position=SearchFilterPosition.TOP)
        self.status_filter = status_filter

    #
    # SearchEditor Hooks
    #

    def get_editor_model(self, product_full_stock_view):
        return product_full_stock_view.product

    def get_columns(self):
        cols = [SearchColumn('code', title=_('Code'), data_type=str,
                             sort_func=sort_sellable_code,
                             sorted=True),
                SearchColumn('barcode', title=_('Barcode'), data_type=str),
                SearchColumn('category_description', title=_(u'Category'),
                             data_type=str, width=120),
                SearchColumn('description', title=_(u'Description'),
                             expand=True, data_type=str),
                SearchColumn('manufacturer', title=_('Manufacturer'),
                             data_type=str, visible=False),
                SearchColumn('model', title=_('Model'), data_type=str,
                             visible=False),
                SearchColumn('location', title=_('Location'), data_type=str,
                             visible=False)]
        # The price/cost columns must be controlled by hide_cost_column and
        # hide_price_column. Since the product search will be available across
        # the applications, it's important to restrict such columns depending
        # of the context.
        if not self.hide_cost_column:
            cols.append(SearchColumn('cost', _('Cost'), data_type=currency,
                                     format_func=get_formatted_cost, width=90))
        if not self.hide_price_column:
            cols.append(Column('price', title=_('Price'),
                               data_type=currency, width=90))

        cols.append(SearchColumn('stock', title=_('Stock'),
                                 format_func=format_quantity,
                                 data_type=Decimal, width=80))
        return cols

    def executer_query(self, store):
        branch_id = self.branch_filter.get_state().value
        if branch_id is None:
            branch = None
        else:
            branch = store.get(Branch, branch_id)
        results = self.search_spec.find_by_branch(store, branch)
        return results.find(Eq(Product.is_composed, False))

    #
    # Callbacks
    #

    def on_results__has_rows(self, widget, has_rows):
        self.csv_button.set_sensitive(has_rows)

    def on_results__selection_changed(self, widget, selection):
        enable_details = selection and selection.product.storable
        self.branch_stock_button.set_sensitive(bool(enable_details))

    def on_csv_button__clicked(self, widget):
        sse = SpreadSheetExporter()
        sse.export(object_list=self.results,
                   name=_('Product'),
                   filename_prefix=_('product'))

    def on_branch_stock_button__clicked(self, widget):
        product_viewable = self.get_selection()
        if product_viewable:
            self.run_dialog(ProductBranchSearch, self, self.store,
                            product_viewable.product.storable)


def format_data(data):
    # must return zero or report printed show None instead of 0
    if data is None:
        return 0
    return format_quantity(data)


class ProductSearchQuantity(SearchDialog):
    title = _('Product History Search')
    size = (775, 450)
    table = search_spec = ProductQuantityView
    advanced_search = False
    show_production_columns = False

    #
    # SearchDialog Hooks
    #

    def on_print_button_clicked(self, button):
        print_report(ProductQuantityReport, self.results, list(self.results),
                     filters=self.search.get_search_filters())

    def create_filters(self):
        self.set_text_field_columns(['description'])

        # Date
        date_filter = DateSearchFilter(_('Date:'))
        date_filter.select(Today)
        columns = [ProductHistory.sold_date,
                   ProductHistory.received_date,
                   ProductHistory.production_date,
                   ProductHistory.decreased_date]
        self.add_filter(date_filter, columns=columns)
        self.date_filter = date_filter

        # Branch
        self.branch_filter = self.create_branch_filter(_('In branch:'))
        self.add_filter(self.branch_filter, columns=['branch'],
                        position=SearchFilterPosition.TOP)
        # remove 'Any' option from branch_filter
        self.branch_filter.combo.remove_text(0)

    #
    # SearchEditor Hooks
    #

    def get_columns(self):
        return [Column('code', title=_('Code'), data_type=str,
                       sort_func=sort_sellable_code,
                       sorted=True, width=130),
                Column('description', title=_('Description'), data_type=str,
                       expand=True),
                Column('quantity_sold', title=_('Sold'),
                       format_func=format_data, data_type=Decimal,
                       visible=not self.show_production_columns),
                Column('quantity_transfered', title=_('Transfered'),
                       format_func=format_data, data_type=Decimal,
                       visible=not self.show_production_columns),
                Column('quantity_received', title=_('Received'),
                       format_func=format_data, data_type=Decimal,
                       visible=not self.show_production_columns),
                Column('quantity_produced', title=_('Produced'),
                       format_func=format_data, data_type=Decimal,
                       visible=self.show_production_columns),
                Column('quantity_consumed', title=_('Consumed'),
                       format_func=format_data, data_type=Decimal,
                       visible=self.show_production_columns),
                Column('quantity_decreased', title=_('Manualy Decreased'),
                       format_func=format_data, data_type=Decimal,
                       visible=self.show_production_columns),
                Column('quantity_lost', title=_('Lost'),
                       format_func=format_data, data_type=Decimal,
                       visible=self.show_production_columns, )]


class ProductsSoldSearch(SearchDialog):
    title = _('Products Sold Search')
    size = (775, 450)
    table = search_spec = SoldItemView
    advanced_search = False

    def on_print_button_clicked(self, button):
        print_report(ProductsSoldReport, self.results, list(self.results),
                     filters=self.search.get_search_filters())

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['description'])
        self.search.set_query(self.executer_query)

        # Date
        date_filter = DateSearchFilter(_('Date:'))
        date_filter.select(Today)
        self.add_filter(date_filter)
        self.date_filter = date_filter

        # Branch
        branch_filter = self.create_branch_filter(_('In branch:'))
        self.add_filter(branch_filter, columns=[],
                        position=SearchFilterPosition.TOP)
        self.branch_filter = branch_filter

    def executer_query(self, store):
        # We have to do this manual filter since adding this columns to the
        # view would also group the results by those fields, leading to
        # duplicate values in the results.
        branch_id = self.branch_filter.get_state().value
        if branch_id is None:
            branch = None
        else:
            branch = store.get(Branch, branch_id)

        date = self.date_filter.get_state()
        if isinstance(date, DateQueryState):
            date = date.date
        elif isinstance(date, DateIntervalQueryState):
            date = (date.start, date.end)

        return self.table.find_by_branch_date(store, branch, date)
    #
    # SearchEditor Hooks
    #

    def get_columns(self):
        return [Column('code', title=_('Code'), data_type=str,
                       sorted=True, width=130),
                Column('description', title=_('Description'), data_type=str,
                       width=300),
                Column('quantity', title=_('Sold'),
                       format_func=format_data,
                       data_type=Decimal),
                Column('average_cost', title=_('Avg. Cost'),
                       data_type=currency), ]


class ProductStockSearch(SearchEditor):
    title = _('Product Stock Search')
    size = (800, 450)
    # FIXME: This search needs another viewable, since ProductFullStockView
    # cannot filter the branch of the purchase, when counting the number of
    # purchased orders by branch
    table = search_spec = ProductFullStockItemView
    editor_class = ProductStockEditor
    has_new_button = False
    advanced_search = True

    #
    # SearchDialog Hooks
    #

    def setup_widgets(self):
        difference_label = gtk.Label()
        difference_label.set_markup(
            "<small><b>%s</b></small>"
            % api.escape(_(u"The DIFFERENCE column is equal to "
                           "IN STOCK minus MINIMUM columns")))
        difference_label.show()
        self.search.vbox.pack_end(difference_label, False, False, 6)

    def create_filters(self):
        self.set_text_field_columns(['description', 'category_description'])
        self.search.set_query(self.executer_query)

        branch_filter = self.create_branch_filter(_('In branch:'))
        self.add_filter(branch_filter, columns=[])
        self.branch_filter = branch_filter

    def on_print_button_clicked(self, widget):
        print_report(ProductStockReport, self.results, list(self.results),
                     filters=self.search.get_search_filters())

    #
    # SearchEditor Hooks
    #

    def get_editor_model(self, model):
        return model.product

    def get_columns(self):
        return [SearchColumn('code', title=_('Code'), data_type=str,
                             sort_func=sort_sellable_code),
                SearchColumn('category_description', title=_('Category'),
                             data_type=str, width=100),
                SearchColumn('description', title=_('Description'),
                             data_type=str,
                             expand=True, sorted=True),
                SearchColumn('manufacturer', title=_('Manufacturer'),
                             data_type=str,
                             visible=False),
                SearchColumn('model', title=_('Model'), data_type=str,
                             visible=False),
                SearchColumn('location', title=_('Location'), data_type=str,
                             visible=False),
                SearchColumn('maximum_quantity', title=_('Maximum'),
                             visible=False, format_func=format_data,
                             data_type=Decimal),
                SearchColumn('minimum_quantity', title=_('Minimum'),
                             format_func=format_data, data_type=Decimal),
                SearchColumn('stock', title=_('In Stock'),
                             format_func=format_data, data_type=Decimal),
                SearchColumn('to_receive_quantity', title=_('To Receive'),
                             format_func=format_data,
                             data_type=Decimal),
                ColoredColumn('difference', title=_('Difference'), color='red',
                              format_func=format_data, data_type=Decimal,
                              data_func=lambda x: x <= Decimal(0))]

    def executer_query(self, store):
        branch_id = self.branch_filter.get_state().value
        if branch_id is None:
            branch = None
        else:
            branch = store.get(Branch, branch_id)
        return self.table.find_by_branch(store, branch)


class ProductClosedStockSearch(ProductSearch):
    """A SearchEditor for Closed Products"""

    title = _('Closed Product Stock Search')
    table = search_spec = ProductClosedStockView
    has_new_button = False

    def __init__(self, store, hide_footer=True, hide_toolbar=True,
                 selection_mode=None,
                 hide_cost_column=True, use_product_statuses=None,
                 hide_price_column=True):
        if selection_mode is None:
            selection_mode = gtk.SELECTION_BROWSE
        ProductSearch.__init__(self, store, hide_footer, hide_toolbar,
                               selection_mode, hide_cost_column,
                               use_product_statuses, hide_price_column)

    def create_filters(self):
        self.set_text_field_columns(['description', 'barcode',
                                     'category_description'])
        self.search.set_query(self.executer_query)

        # Branch
        branch_filter = self.create_branch_filter(_('In branch:'))
        self.add_filter(branch_filter, columns=[])
        self.branch_filter = branch_filter

    def _setup_print_slave(self):
        pass

    def _has_rows(self, results, obj):
        SearchEditor._has_rows(self, results, obj)

    #
    # SearchDialog Hooks
    #

    def on_print_button_clicked(self, widget):
        print_report(ProductClosedStockReport, self.results,
                     filters=self.search.get_search_filters(),
                     branch_name=self.branch_filter.combo.get_active_text())


class ProductBrandSearch(SearchEditor):
    title = _('Brand Search')
    table = Product
    size = (775, 450)
    search_spec = ProductBrandStockView
    editor_class = ProductEditor

    def __init__(self, store):
        SearchEditor.__init__(self, store, hide_footer=True,
                              hide_toolbar=True)

    #
    # SearchDialog Hooks
    #

    def setup_widgets(self):
        self.csv_button = self.add_button(label=_('Export to spreadsheet...'))
        self.csv_button.show()
        self.csv_button.set_sensitive(False)

    def create_filters(self):
        self.set_text_field_columns(['brand'])
        self.search.set_query(self.executer_query)

        # Branch
        branch_filter = self.create_branch_filter(_('In branch:'))
        self.add_filter(branch_filter, columns=[])
        self.branch_filter = branch_filter

    #
    # SearchEditor Hooks
    #

    def get_columns(self):
        cols = [SearchColumn('brand', title=_('Brand'), data_type=str,
                             sorted=True, expand=True),
                Column('quantity', title=_('Quantity'), data_type=Decimal)]
        return cols

    def executer_query(self, store):
        branch_id = self.branch_filter.get_state().value
        if branch_id is None:
            branch = None
        else:
            branch = store.get(Branch, branch_id)

        return self.search_spec.find_by_branch(store, branch)

    #
    # Callbacks
    #

    def on_results__has_rows(self, widget, has_rows):
        self.csv_button.set_sensitive(has_rows)

    def on_csv_button__clicked(self, widget):
        sse = SpreadSheetExporter()
        sse.export(object_list=self.results,
                   name=_('Brands'),
                   filename_prefix=_('brands'))

    def on_print_button_clicked(self, button):
        print_report(ProductBrandReport, self.results, list(self.results),
                     filters=self.search.get_search_filters())


class ProductBranchSearch(SearchDialog):
    """Show products in stock on all branchs
    """
    title = _('Product Branch Search')
    size = (600, 500)
    search_spec = ProductBranchStockView
    advanced_search = False

    def __init__(self, store, storable):
        self._storable = storable
        dialog_title = _("Stock of %s") % storable.product.description
        SearchDialog.__init__(self, store, title=dialog_title)
        self.search.refresh()

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['branch_name'])
        self.search.set_query(self.executer_query)

    #
    # SearchEditor Hooks
    #

    def get_columns(self):
        return [Column('branch_name', title=_('Branch'), data_type=str,
                       expand=True),
                Column('stock', title=_('In Stock'), data_type=Decimal,
                       format_func=format_data)]

    def executer_query(self, store):
        return self.search_spec.find_by_storable(store, self._storable)


def test():  # pragma: no cover
    from stoqlib.api import api
    from stoqlib.gui.base.dialogs import run_dialog
    ec = api.prepare_test()
    run_dialog(ProductSearch, None, ec.store)


if __name__ == '__main__':
    test()
