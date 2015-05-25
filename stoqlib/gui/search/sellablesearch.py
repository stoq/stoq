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
##
""" Implementation of sellable search """

from decimal import Decimal

import gtk
from kiwi.currency import currency
from storm.expr import Ne

from stoqlib.api import api
from stoqlib.database.orm import ORMObject
from stoqlib.domain.product import ProductSupplierInfo, Product
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.views import SellableFullStockView
from stoqlib.gui.dialogs.sellableimage import SellableImageViewer
from stoqlib.gui.editors.producteditor import ProductEditor
from stoqlib.gui.search.searchcolumns import (AccessorColumn, SearchColumn,
                                              QuantityColumn)
from stoqlib.gui.search.searcheditor import SearchEditor
from stoqlib.gui.wizards.productwizard import ProductCreateWizard
from stoqlib.lib.defaults import sort_sellable_code
from stoqlib.lib.formatters import format_quantity
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class SellableSearch(SearchEditor):
    title = _('Item search')
    size = (800, 500)
    model_list_lookup_attr = 'product_id'
    footer_ok_label = _('_Select item')
    search_spec = SellableFullStockView
    editor_class = None
    exclude_delivery_service = True
    text_field_columns = [SellableFullStockView.description,
                          SellableFullStockView.category_description,
                          SellableFullStockView.barcode,
                          SellableFullStockView.code]

    def __init__(self, store, hide_footer=False, hide_toolbar=True,
                 selection_mode=None, search_str=None, search_spec=None,
                 search_query=None, double_click_confirm=True, info_message=None,
                 show_closed_items=False):
        """
        :param store: a store
        :param hide_footer: do I have to hide the dialog footer?
        :param hide_toolbar: do I have to hide the dialog toolbar?
        :param selection_mode: the kiwi list selection mode
        :param search_str: If this search should already filter for some string
        :param double_click_confirm: If double click a item in the list should
            automatically confirm
        :param show_closed_items: if this parameter is True, shows sellable with
            status closed
        """
        if selection_mode is None:
            selection_mode = gtk.SELECTION_BROWSE

        self._image_viewer = None
        self._first_search = True
        self._first_search_string = search_str
        self._search_query = search_query
        self._show_closed_items = show_closed_items
        self._delivery_sellable = sysparam.get_object(
            store, 'DELIVERY_SERVICE').sellable

        SearchEditor.__init__(self, store, search_spec=search_spec,
                              editor_class=self.editor_class,
                              hide_footer=hide_footer,
                              hide_toolbar=hide_toolbar,
                              selection_mode=selection_mode,
                              double_click_confirm=double_click_confirm)

        if info_message:
            self.set_message(info_message)

        if search_str:
            self.set_searchbar_search_string(search_str)
            self.search.refresh()

    #
    #  SearchEditor
    #

    def key_shift_Return(self):
        self.confirm()

    def key_control_Return(self):
        self.confirm()

    def key_shift_KP_Enter(self):
        self.confirm()

    def key_control_KP_Enter(self):
        self.confirm()

    def close(self):
        # Make sure image viewer gets closed when this search closes
        self._close_image_viewer()
        super(SellableSearch, self).close()

    def confirm(self, retval=None):
        # FIXME: This is a hack, we need to do proper validation in the parent
        if retval is None and not self.ok_button.get_sensitive():
            return
        super(SellableSearch, self).confirm(retval=retval)

    def setup_widgets(self):
        self.image_viewer_toggler = gtk.CheckMenuItem(_("Show image viewer"))
        self.popup = gtk.Menu()
        self.popup.add(self.image_viewer_toggler)
        self.popup.show_all()

        if hasattr(self.search_spec, 'product'):
            self.branch_stock_button = self.add_button(label=_('Stock details'))
            self.branch_stock_button.show()
            self.branch_stock_button.set_sensitive(False)
        else:
            self.branch_stock_button = None

    def create_filters(self):
        self.search.set_query(self.executer_query)

    def get_columns(self):
        columns = [SearchColumn('code', title=_(u'Code'), data_type=str),
                   SearchColumn('barcode', title=_('Barcode'), data_type=str,
                                sort_func=sort_sellable_code, width=80),
                   SearchColumn('category_description', title=_('Category'),
                                data_type=str, width=120),
                   SearchColumn('description', title=_('Description'),
                                data_type=str, expand=True, sorted=True),
                   SearchColumn('manufacturer', title=_('Manufacturer'),
                                data_type=str, visible=False),
                   SearchColumn('model', title=_('Model'),
                                data_type=str, visible=False)]

        if hasattr(self.search_spec, 'price'):
            columns.append(SearchColumn('price',
                                        title=_(u'Price'),
                                        data_type=currency, visible=True))

        if hasattr(self.search_spec, 'minimum_quantity'):
            columns.append(SearchColumn('minimum_quantity',
                                        title=_(u'Minimum Qty'),
                                        data_type=Decimal, visible=False))

        if hasattr(self.search_spec, 'stock'):
            columns.append(QuantityColumn('stock', title=_(u'In Stock')))

        return columns

    def update_widgets(self):
        sellable_view = self.results.get_selected()
        self.set_edit_button_sensitive(bool(sellable_view))
        self.ok_button.set_sensitive(bool(sellable_view))

        if self.branch_stock_button is not None:
            self.branch_stock_button.set_sensitive(
                bool(self._get_selected_storable()))

    def executer_query(self, store):
        # If the viewable has a find_by_branch method, then lets use it instead
        # of the generic find, to show only the stock for the current branch.
        if hasattr(self.search_spec, 'find_by_branch'):
            branch = api.get_current_branch(store)
            results = self.search_spec.find_by_branch(store, branch)
        else:
            results = store.find(self.search_spec)

        if self._search_query:
            results = results.find(self._search_query)

        if not self._show_closed_items:
            results = results.find(
                self.search_spec.status == Sellable.STATUS_AVAILABLE)

        if self.exclude_delivery_service:
            results = results.find(
                self.search_spec.id != self._delivery_sellable.id)

        return results

    #
    #  Private
    #

    def _get_selected_storable(self):
        product = getattr(self.results.get_selected(), 'product', None)
        if product and self.fast_iter:
            product = self.store.get(Product, product.id)

        return product and product.storable

    def _open_image_viewer(self):
        assert self._image_viewer is None

        self._image_viewer = SellableImageViewer(size=(325, 325))
        self._update_image_viewer()
        self._image_viewer.toplevel.connect(
            'delete-event', self._on_image_viewer__delete_event)
        self._image_viewer.show_all()

    def _close_image_viewer(self):
        if self._image_viewer is None:
            return

        self._image_viewer.destroy()
        self._image_viewer = None

    def _update_image_viewer(self):
        if self._image_viewer is None:
            return

        row = self.results.get_selected()
        self._image_viewer.set_sellable(row and row.sellable)

    #
    # Callbacks
    #

    def _on_image_viewer__delete_event(self, window, event):
        self._image_viewer = None
        self.image_viewer_toggler.set_active(False)

    def on_image_viewer_toggler__toggled(self, item):
        if item.get_active():
            self._open_image_viewer()
        else:
            self._close_image_viewer()

    def on_results__right_click(self, klist, row, event):
        self.popup.popup(None, None, None, event.button, event.time)

    def on_results__selection_changed(self, klist, row):
        self._update_image_viewer()

    def on_branch_stock_button__clicked(self, widget):
        from stoqlib.gui.search.productsearch import ProductBranchSearch
        storable = self._get_selected_storable()
        if not storable:
            return

        self.run_dialog(ProductBranchSearch, self, self.store, storable)


class SaleSellableSearch(SellableSearch):
    footer_ok_label = _('_Add sale items')
    has_new_button = False

    def __init__(self, store, hide_footer=False, hide_toolbar=True,
                 search_str=None, search_query=None, info_message=None,
                 sale_items=None, quantity=None):
        """
        :param sale_items: optionally, a list of sellables which will be
            used to deduct stock values
        :param quantity: the quantity of stock to add to the order,
            is necessary to supply if you supply an order.
        """
        self._quantity = quantity
        self._first_search = True
        self._first_search_string = search_str
        self._current_sale_stock = {}

        if sale_items:
            if self._quantity is None:
                raise TypeError("You need to specify a quantity "
                                "when supplying an order")
            for item in sale_items:
                if item.sellable.product_storable:
                    quantity = self._current_sale_stock.get(item.sellable.id, 0)
                    quantity += item.quantity
                    self._current_sale_stock[item.sellable.id] = quantity

        SellableSearch.__init__(self, store, hide_footer=hide_footer,
                                hide_toolbar=hide_toolbar,
                                search_str=search_str,
                                search_query=search_query,
                                info_message=info_message)

    #
    #  SellableSearch
    #

    def search_completed(self, results, states):
        if not self._first_search:
            if self._first_search_string != self.get_searchbar_search_string():
                self.set_message(None)

        if len(results) >= 1:
            results.select(results[0])

        self.search.focus_search_entry()
        self._first_search = False

    def executer_query(self, store):
        results = super(SaleSellableSearch, self).executer_query(store)

        # if we select a quantity which is not an integer, filter out
        # sellables without a unit set
        if self._quantity is not None and (self._quantity % 1) != 0:
            results = results.find(Ne(Sellable.unit_id, None))

        return results

    def update_widgets(self):
        super(SaleSellableSearch, self).update_widgets()

        sellable_view = self.results.get_selected()
        if not sellable_view:
            return

        sellable = sellable_view.sellable
        if (sellable.product_storable and
                self._quantity > self._get_available_stock(sellable_view)):
            self.ok_button.set_sensitive(False)
        else:
            self.ok_button.set_sensitive(True)

    def get_columns(self):
        return [SearchColumn('code', title=_('Code'), data_type=str,
                             sort_func=sort_sellable_code,
                             sorted=True),
                SearchColumn('barcode', title=_('Barcode'), data_type=str,
                             visible=False),
                SearchColumn('description', title=_('Description'),
                             data_type=str, expand=True),
                SearchColumn('manufacturer', title=_('Manufacturer'),
                             data_type=str, visible=False),
                SearchColumn('model', title=_('Model'),
                             data_type=str, visible=False),
                SearchColumn('price', title=_('Price'), data_type=currency,
                             justify=gtk.JUSTIFY_RIGHT, width=120),
                SearchColumn('category_description', title=_('Category'),
                             data_type=str, visible=False),
                AccessorColumn('stock', title=_(u'Stock'),
                               accessor=self._get_available_stock,
                               format_func=format_quantity, width=90,
                               data_type=Decimal)]

    #
    #  Private
    #

    def _get_available_stock(self, sellable_view):
        return sellable_view.stock - self._current_sale_stock.get(
            sellable_view.id, 0)


class PurchaseSellableSearch(SellableSearch):
    editor_class = ProductEditor

    def __init__(self, store, hide_footer=False, hide_toolbar=False,
                 search_str=None, search_spec=None, search_query=None,
                 info_message=None, supplier=None):
        self._supplier = supplier

        SellableSearch.__init__(self, store, hide_footer=hide_footer,
                                hide_toolbar=hide_toolbar,
                                search_str=search_str, search_spec=search_spec,
                                search_query=search_query,
                                info_message=info_message)

    def get_editor_model(self, model):
        return model.product

    def run_editor(self, obj=None):
        store = api.new_store()
        if not obj:
            self.editor_class = ProductCreateWizard
            product = self.editor_class.run_wizard(self)
            product = product and store.fetch(product)
        else:
            self.editor_class = ProductEditor
            product = self.run_dialog(self.editor_class, self, store,
                                      store.fetch(obj), visual_mode=self._read_only)

        # This means we are creating a new product. After that, add the
        # current supplier as the supplier for this product
        if (obj is None and product and
                not product.is_supplied_by(self._supplier)):
            ProductSupplierInfo(store=store,
                                supplier=store.fetch(self._supplier),
                                product=product,
                                base_cost=product.sellable.cost,
                                is_main_supplier=True)

        if store.confirm(product):
            # If the return value is an ORMObject, fetch it from
            # the right connection
            if isinstance(product, ORMObject):
                product = self.store.get(type(product), product.id)

            # If we created a new object, confirm the dialog automatically
            if obj is None:
                self.confirm(product)
                store.close()
                return
        store.close()

        return product
