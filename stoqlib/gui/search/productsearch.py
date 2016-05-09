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

import datetime
from decimal import Decimal

import gtk
from kiwi.currency import currency
from kiwi.ui.objectlist import Column, ColoredColumn, COL_MODEL
from storm.expr import Eq

from stoqlib.api import api
from stoqlib.domain.person import Branch
from stoqlib.domain.product import (Product, ProductHistory,
                                    ProductStockItem)
from stoqlib.domain.sale import Sale
from stoqlib.domain.sellable import SellableCategory, Sellable
from stoqlib.domain.views import (ProductQuantityView,
                                  ProductFullStockItemView, SoldItemView,
                                  ProductFullWithClosedStockView,
                                  ProductClosedStockView,
                                  ProductBranchStockView,
                                  ProductBatchView, ProductBrandStockView,
                                  ProductBrandByBranchView)
from stoqlib.enums import SearchFilterPosition
from stoqlib.gui.base.gtkadds import change_button_appearance, set_bold
from stoqlib.gui.editors.producteditor import (ProductEditor,
                                               ProductStockEditor)
from stoqlib.gui.search.searchcolumns import SearchColumn, QuantityColumn
from stoqlib.gui.search.searchdialog import SearchDialog, SearchDialogPrintSlave
from stoqlib.gui.search.searcheditor import SearchEditor
from stoqlib.gui.search.searchfilters import (DateSearchFilter, ComboSearchFilter,
                                              Today)
from stoqlib.gui.search.searchresultview import SearchResultTreeView
from stoqlib.gui.search.sellablesearch import SellableSearch
from stoqlib.gui.utils.printing import print_report
from stoqlib.gui.wizards.productwizard import ProductCreateWizard
from stoqlib.lib.defaults import sort_sellable_code
from stoqlib.lib.formatters import format_quantity, get_formatted_cost
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.product import (ProductReport, ProductQuantityReport,
                                       ProductClosedStockReport,
                                       ProductPriceReport, ProductStockReport,
                                       ProductsSoldReport, ProductBrandReport,
                                       ProductBrandByBranchReport)

_ = stoqlib_gettext


class _ProductBrandResultTreeView(SearchResultTreeView):

    def __iter__(self):
        for item in self.iter_items():
            yield item

    # Overriding the method _add_results to avoid multiple consults to sql
    def add_result(self, result):
        if not isinstance(result, ProductBrandStockView):
            parent = self._cache.get(result.brand)
        else:
            parent = None
        if parent:
            self.add_result(parent)
        if not result in self:
            self.append(parent, result)
            if parent:
                self.expand(parent)

    def search_completed(self, results):
        if not results.is_empty():
            self._cache = {}
            for item in results[0].store.find(ProductBrandStockView):
                self._cache[item.brand] = item

        super(_ProductBrandResultTreeView, self).search_completed(results)

    def iter_items(self, include_parents=False):
        """ Set include_parents=True if the parents are needed """
        for obj in self.get_model():
            if include_parents:
                yield obj[COL_MODEL]
            for child in obj.iterchildren():
                yield child[COL_MODEL]


class ProductSearch(SellableSearch):
    title = _('Product Search')
    search_spec = ProductFullWithClosedStockView
    editor_class = ProductEditor
    report_class = ProductReport
    has_branch_filter = True
    has_status_filter = True
    has_print_price_button = True
    csv_data = (_("Product"), _("product"))
    footer_ok_label = _('Add products')

    def __init__(self, store, hide_footer=True, hide_toolbar=False,
                 hide_cost_column=False, hide_price_column=False,
                 double_click_confirm=False):
        """
        :param store: a store
        :param hide_footer: do I have to hide the dialog footer?
        :param hide_toolbar: do I have to hide the dialog toolbar?
        :param hide_cost_column: if it's True, no need to show the
                                 column 'cost'
        :param hide_price_column: if it's True no need to show the
                                  column 'price'
        """
        # We only want to display data as a tree for ProductSearch, but
        # not setting 'tree = True' on the class definition as it has too many
        # subclasses for us to manually set to False on each one
        if self.__class__ is ProductSearch:
            self.tree = True

        self.hide_cost_column = hide_cost_column
        self.hide_price_column = hide_price_column
        SellableSearch.__init__(self, store, hide_footer=hide_footer,
                                hide_toolbar=hide_toolbar,
                                double_click_confirm=double_click_confirm)
        if self.has_print_price_button:
            self._setup_print_slave()
        else:
            self._print_slave = None

    def _setup_print_slave(self):
        self._print_slave = SearchDialogPrintSlave()
        change_button_appearance(self._print_slave.print_price_button,
                                 gtk.STOCK_PRINT, _("_Price table"))
        self.attach_slave('print_holder', self._print_slave)
        self._print_slave.connect('print', self.on_print_price_button_clicked)
        self._print_slave.print_price_button.set_sensitive(False)

    def on_print_price_button_clicked(self, button):
        print_report(ProductPriceReport, list(self.results),
                     filters=self.search.get_search_filters(),
                     branch_name=self.branch_filter.combo.get_active_text())

    #
    #  ProductSearch
    #

    def setup_widgets(self):
        super(ProductSearch, self).setup_widgets()

        if self.csv_data is not None:
            self.add_csv_button(*self.csv_data)

    def create_filters(self):
        super(ProductSearch, self).create_filters()

        if self.has_branch_filter:
            branch_filter = self.create_branch_filter(_('In branch:'))
            self.add_filter(branch_filter, columns=[])
            self.branch_filter = branch_filter
        else:
            self.branch_filter = None

        if self.has_status_filter:
            status_filter = self.create_sellable_filter()
            self.add_filter(status_filter, columns=['status'],
                            position=SearchFilterPosition.TOP)
            self.status_filter = status_filter
        else:
            self.status_filter = None

    def get_editor_class_for_object(self, obj):
        if obj is None:
            return ProductCreateWizard

        return self.editor_class

    def get_editor_model(self, product_full_stock_view):
        return product_full_stock_view.product

    def run_editor(self, obj):
        editor_class = self.get_editor_class_for_object(obj)
        if obj is None and issubclass(editor_class, ProductCreateWizard):
            return editor_class.run_wizard(self)

        return super(ProductSearch, self).run_editor(obj)

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
                SearchColumn('ncm', title=_('NCM'), data_type=str,
                             visible=False),
                Column('unit', title=_('Unit'), data_type=str, visible=False),
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
            cols.append(SearchColumn('price', title=_('Price'),
                                     data_type=currency, width=90))

        cols.append(QuantityColumn('stock', title=_('Stock')))
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

    def on_results__has_rows(self, results, obj):
        if self._print_slave is not None:
            self._print_slave.print_price_button.set_sensitive(obj)


class ProductSearchQuantity(ProductSearch):
    title = _('Product History Search')
    search_spec = ProductQuantityView
    report_class = ProductQuantityReport
    csv_data = None
    advanced_search = False
    has_print_price_button = False
    show_production_columns = False
    text_field_columns = [ProductQuantityView.description]
    branch_filter_column = ProductQuantityView.branch

    def __init__(self, store, hide_footer=True, hide_toolbar=True):
        ProductSearch.__init__(self, store, hide_footer=hide_footer,
                               hide_toolbar=hide_toolbar)

    #
    #  ProductSearch
    #

    def create_filters(self):
        # Date
        date_filter = DateSearchFilter(_('Date:'))
        date_filter.select(Today)
        columns = [ProductHistory.sold_date,
                   ProductHistory.received_date,
                   ProductHistory.production_date,
                   ProductHistory.decreased_date]
        self.add_filter(date_filter, columns=columns)
        self.date_filter = date_filter

    def get_columns(self):
        return [Column('code', title=_('Code'), data_type=str,
                       sort_func=sort_sellable_code,
                       sorted=True, width=130),
                Column('description', title=_('Description'), data_type=str,
                       expand=True),
                QuantityColumn('quantity_sold', title=_('Sold'), visible=not
                               self.show_production_columns),
                QuantityColumn('quantity_transfered', title=_('Transfered'),
                               visible=not self.show_production_columns),
                QuantityColumn('quantity_received', title=_('Received'),
                               visible=not self.show_production_columns),
                QuantityColumn('quantity_produced', title=_('Produced'),
                               visible=self.show_production_columns),
                QuantityColumn('quantity_consumed', title=_('Consumed'),
                               visible=self.show_production_columns),
                QuantityColumn('quantity_decreased',
                               title=_('Manualy Decreased'),
                               visible=self.show_production_columns),
                QuantityColumn('quantity_lost', title=_('Lost'),
                               visible=self.show_production_columns, )]


class ProductsSoldSearch(ProductSearch):
    title = _('Products Sold Search')
    search_spec = SoldItemView
    report_class = ProductsSoldReport
    csv_data = None
    has_print_price_button = False
    advanced_search = False
    text_field_columns = [SoldItemView.description]
    branch_filter_column = Sale.branch_id

    def __init__(self, store, hide_footer=True, hide_toolbar=True):
        ProductSearch.__init__(self, store, hide_footer=hide_footer,
                               hide_toolbar=hide_toolbar)

    #
    # Private API
    #

    def _update_summary(self, klist):
        quantity = total = 0
        for obj in klist:
            quantity += obj.quantity
            total += obj.total_sold

        self.quantity_label.set_label(_(u'Total quantity: %s') % format_quantity(quantity))
        self.total_sold_label.set_label(_(u'Total sold: %s') % get_formatted_cost(total))

    #
    # ProductSearch
    #

    def setup_widgets(self):
        super(ProductSearch, self).setup_widgets()
        hbox = gtk.HBox()
        hbox.set_spacing(6)

        self.vbox.pack_start(hbox, False, True)
        self.vbox.reorder_child(hbox, 2)
        self.vbox.set_spacing(6)

        hbox.pack_start(gtk.Label(), True, True)

        # Create two labels to show a summary for the search (kiwi's
        # SummaryLabel supports only one column)
        self.quantity_label = gtk.Label()
        hbox.pack_start(self.quantity_label, False, False)

        self.total_sold_label = gtk.Label()
        hbox.pack_start(self.total_sold_label, False, False)
        hbox.show_all()

        set_bold(self.quantity_label)
        set_bold(self.total_sold_label)

    def create_filters(self):
        self.date_filter = DateSearchFilter(_('Date:'))
        self.date_filter.select(Today)
        self.add_filter(self.date_filter, columns=[Sale.confirm_date])

    def get_columns(self):
        return [Column('code', title=_('Code'), data_type=str,
                       sorted=True),
                Column('description', title=_('Description'),
                       data_type=str, expand=True),
                QuantityColumn('quantity', title=_('Sold')),
                Column('average_cost', title=_('Avg. Cost'),
                       data_type=currency),
                Column('total_sold', title=_('Total sold'),
                       data_type=currency)]

    #
    # Callbacks
    #

    def on_search__search_completed(self, search, result_view, states):
        self._update_summary(result_view)


class ProductStockSearch(ProductSearch):
    title = _('Product Stock Search')
    # FIXME: This search needs another viewable, since ProductFullStockView
    # cannot filter the branch of the purchase, when counting the number of
    # purchased orders by branch
    search_spec = ProductFullStockItemView
    editor_class = ProductStockEditor
    report_class = ProductStockReport
    csv_data = None
    has_print_price_button = False
    has_new_button = False
    has_status_filter = False
    advanced_search = True

    #
    #  ProductSearch
    #

    def setup_widgets(self):
        super(ProductStockSearch, self).setup_widgets()

        difference_label = gtk.Label()
        difference_label.set_markup(
            "<small><b>%s</b></small>"
            % api.escape(_(u"The DIFFERENCE column is equal to "
                           "IN STOCK minus MINIMUM columns")))
        difference_label.show()
        self.search.vbox.pack_end(difference_label, False, False, 6)

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
                QuantityColumn('maximum_quantity', title=_('Maximum'),
                               visible=False),
                QuantityColumn('minimum_quantity', title=_('Minimum')),
                QuantityColumn('stock', title=_('In Stock')),
                QuantityColumn('to_receive_quantity', title=_('To Receive')),
                ColoredColumn('difference', title=_('Difference'), color='red',
                              format_func=format_quantity, data_type=Decimal,
                              data_func=lambda x: x <= Decimal(0))]

    def executer_query(self, store):
        branch_id = self.branch_filter.get_state().value
        if branch_id is None:
            branch = None
        else:
            branch = store.get(Branch, branch_id)
        return self.search_spec.find_by_branch(store, branch)


class ProductClosedStockSearch(ProductSearch):
    """A SearchEditor for Closed Products"""

    title = _('Closed Product Stock Search')
    search_spec = ProductClosedStockView
    report_class = ProductClosedStockReport
    has_status_filter = False
    has_print_price_button = False
    has_new_button = False

    def __init__(self, store, hide_footer=True, hide_toolbar=True,
                 hide_cost_column=True, hide_price_column=True):
        ProductSearch.__init__(self, store, hide_footer, hide_toolbar,
                               hide_cost_column=hide_cost_column,
                               hide_price_column=hide_price_column)


class ProductBatchSearch(ProductSearch):
    title = _('Batch Search')
    search_spec = ProductBatchView
    has_print_price_button = False
    csv_data = (_('Batch'), _('batch'))
    fast_iter = True
    text_field_columns = [ProductBatchView.description,
                          ProductBatchView.batch_number]
    branch_filter_column = ProductStockItem.branch_id
    unlimited_results = True

    def __init__(self, store, hide_footer=True, hide_toolbar=True):
        ProductSearch.__init__(self, store, hide_footer=hide_footer,
                               hide_toolbar=hide_toolbar)

    #
    #  ProductSearch
    #

    def create_filters(self):
        # We need to overide to prevent the ProductSearch.setup_filters being
        # called
        pass

    def setup_widgets(self):
        super(ProductBatchSearch, self).setup_widgets()
        self.search.set_summary_label('quantity', label=(u'Total:'),
                                      format='<b>%s</b>')

    def get_columns(self):
        cols = [SearchColumn('category', title=_('Category'), data_type=str),
                SearchColumn('description', title=_('Description'), data_type=str,
                             sorted=True, expand=True),
                SearchColumn('branch_name', title=_('Branch'), data_type=str,
                             visible=False),
                SearchColumn('manufacturer', title=_('Manufacturer'),
                             data_type=str, visible=False),
                SearchColumn('brand', title=_('Brand'), data_type=str,
                             visible=False),
                SearchColumn('model', title=_('Model'), data_type=str,
                             visible=False),
                SearchColumn('batch_number', title=_('Batch'), data_type=str),
                SearchColumn('batch_date', title=_('Date'),
                             data_type=datetime.date),
                SearchColumn('quantity', title=_('Qty'), data_type=Decimal)]
        return cols


class ProductBrandSearch(SearchEditor):
    title = _('Brand Search')
    size = (775, 450)
    search_spec = ProductBrandStockView
    editor_class = ProductEditor
    report_class = ProductBrandReport
    text_field_columns = [ProductBrandStockView.brand]
    branch_filter_column = ProductStockItem.branch_id

    def __init__(self, store):
        SearchEditor.__init__(self, store, hide_footer=True,
                              hide_toolbar=True)

    #
    # SearchDialog Hooks
    #

    def setup_widgets(self):
        self.add_csv_button(_('Brands'), _('brands'))
        self.search.set_summary_label('quantity', label=_(u'Total:'),
                                      format='<b>%s</b>')

    def create_filters(self):
        # Category
        categories = self.store.find(SellableCategory)
        items = api.for_combo(categories, attr='full_description')
        items.insert(0, (_('Any'), None))
        category_filter = ComboSearchFilter(_('Category'), items)
        self.add_filter(category_filter, columns=[Sellable.category])

    #
    # SearchEditor Hooks
    #

    def get_columns(self):
        cols = [SearchColumn('brand', title=_('Brand'), data_type=str,
                             sorted=True, expand=True),
                Column('quantity', title=_('Quantity'), data_type=Decimal)]
        return cols


class ProductBrandByBranchSearch(SearchDialog):
    title = _('Brand by Branch Search')
    size = (775, 450)
    search_spec = ProductBrandByBranchView
    report_class = ProductBrandByBranchReport
    result_view_class = _ProductBrandResultTreeView
    unlimited_results = True
    text_field_columns = [ProductBrandByBranchView.brand,
                          ProductBrandByBranchView.company]

    #
    # SearchDialog Hooks
    #

    def setup_widgets(self):
        self.add_csv_button(_('Brands'), _('brands'))

        self.search.set_summary_label('quantity', label=_(u'Total:'),
                                      format='<b>%s</b>')

    def create_filters(self):
        self.search.set_query(self.executer_query)

        # Category
        categories = self.store.find(SellableCategory)
        items = api.for_combo(categories, attr='full_description')
        items.insert(0, (_('Any'), None))
        category_filter = ComboSearchFilter(_('Category'), items)
        self.add_filter(category_filter, position=SearchFilterPosition.TOP)
        self.category_filter = category_filter

    #
    # SearchEditor Hooks
    #

    def get_columns(self):
        return [SearchColumn('brand', title=_('Brand'), data_type=str,
                             sorted=True, expand=True),
                SearchColumn('company', title=_('Branch'), data_type=str),
                SearchColumn('manufacturer', title=_('Manufacturer'), data_type=str),
                SearchColumn('product_category', title=_('Category'), data_type=str),
                Column('quantity', title=_('Quantity'), data_type=Decimal)]

    def executer_query(self, store):
        category_description = self.category_filter.get_state().value
        if category_description:
            category = category_description
        else:
            category = None

        return self.search_spec.find_by_category(store, category)

    def print_report(self):
        print_report(self.report_class, self.results,
                     list(self.results.iter_items(include_parents=True)),
                     filters=self.search.get_search_filters())


class ProductBranchSearch(SearchDialog):
    """Show products in stock on all branchs
    """
    title = _('Product Branch Search')
    size = (600, 500)
    search_spec = ProductBranchStockView
    advanced_search = False
    text_field_columns = [ProductBranchStockView.branch_name]

    def __init__(self, store, storable):
        self._storable = storable
        dialog_title = _("Stock of %s") % storable.product.description
        SearchDialog.__init__(self, store, title=dialog_title)
        self.search.refresh()

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.search.set_query(self.executer_query)

    #
    # SearchEditor Hooks
    #

    def get_columns(self):
        return [Column('branch_name', title=_('Branch'), data_type=str,
                       expand=True),
                QuantityColumn('stock', title=_('In Stock'))]

    def executer_query(self, store):
        return self.search_spec.find_by_storable(store, self._storable)


def test():  # pragma: no cover
    from stoqlib.gui.base.dialogs import run_dialog
    ec = api.prepare_test()
    run_dialog(ProductSearch, None, ec.store)


if __name__ == '__main__':
    test()
