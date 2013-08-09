# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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
""" Dialog to open the inventory """

from kiwi.ui.objectlist import Column
from storm.expr import And

from stoqlib.api import api
from stoqlib.domain.inventory import Inventory
from stoqlib.domain.product import Product, ProductManufacturer
from stoqlib.domain.sellable import Sellable, SellableCategory
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.dateutils import localnow
from stoqlib.lib.message import info
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _TemporaryInventory(object):
    def __init__(self, store):
        self.open_date = localnow()
        self.branch = api.get_current_branch(store)
        self.branch_name = self.branch.get_description()
        self.user = api.get_current_user(store)
        self.product_manufacturer = None
        self.product_brand = None
        self.product_family = None


class _TemporaryCategory(object):
    def __init__(self, category=None, parent=None):
        self.category = category
        self.parent = parent
        self.children = []
        self.description = category.description
        self.selected = True


class _UncategorizedProductsCategory(object):
    def __init__(self):
        self.description = u'(%s)' % (_("Uncategorized products"), )
        self.children = []


class InventoryOpenEditor(BaseEditor):
    gladefile = 'InventoryOpenEditor'
    model_type = _TemporaryInventory
    title = _('Open Inventory')
    size = (750, 450)
    proxy_widgets = [
        'open_date',
        'branch_name',
        'product_manufacturer',
        'product_brand',
        'product_family',
    ]

    def __init__(self, store):
        BaseEditor.__init__(self, store, model=None)

        self.register_validate_function(self._validate)
        self.main_dialog.ok_button.set_label(_(u"_Open"))

    #
    # Private
    #

    def _setup_widgets(self):
        self.product_manufacturer.prefill(
            api.for_combo(self.store.find(ProductManufacturer)))

        self.product_brand.prefill(
            [(m, m) for m in
             sorted(Product.find_distinct_values(self.store, Product.brand))])

        self.product_family.prefill(
            [(m, m) for m in
             sorted(Product.find_distinct_values(self.store, Product.family))])

        self.username.set_text(self.model.user.person.name)
        self.open_time.set_text(self.model.open_date.strftime("%X"))
        # load categories
        self.category_tree.set_columns(self._get_columns())
        for category in SellableCategory.get_base_categories(self.store):
            self._append_category(category)

        self._uncategorized_products = self._append_category(
            _UncategorizedProductsCategory())

    def _update_widgets(self):
        all_selected = all([c.selected for c in self.category_tree])
        self.select_all.set_sensitive(not all_selected)
        has_selected = self._has_selected()
        self.unselect_all.set_sensitive(has_selected)
        self.force_validation()

    def _get_columns(self):
        return [Column('selected', title="Include",
                       data_type=bool, editable=True),
                Column('description', title=_(u"Description"),
                       data_type=str, expand=True, sorted=True,
                       expander=True)]

    def _append_category(self, category, parent=None):
        tmp_category = _TemporaryCategory(category)
        row = self.category_tree.append(parent, tmp_category)

        for child in category.children:
            self._append_category(child, parent=row)

        return tmp_category

    def _get_sellables_query(self):
        categories = [c.category for c in self.category_tree if
                      c.selected and c is not self._uncategorized_products]
        include_uncategorized = self._uncategorized_products.selected

        query = Sellable.get_unblocked_by_categories_query(
            self.store, categories, include_uncategorized)

        queries = [query]
        if self.model.product_manufacturer:
            queries.append(Product.manufacturer == self.model.product_manufacturer)
        if self.model.product_brand:
            queries.append(Product.brand == self.model.product_brand)
        if self.model.product_family:
            queries.append(Product.family == self.model.product_family)

        return And(*queries)

    def _select(self, categories, select_value):
        if not categories:
            return

        for category in categories:
            category.selected = select_value
            self.category_tree.update(category)
            # (un)select all row's children too
            self._select(self.category_tree.get_descendants(category),
                         select_value)

        self._update_widgets()

    def _has_selected(self):
        return any([c.selected for c in self.category_tree])

    def _validate(self, value):
        self.refresh_ok(value and self._has_selected())

    #
    # BaseEditorSlave
    #

    def create_model(self, store):
        return _TemporaryInventory(store)

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)
        self._update_widgets()

    def validate_confirm(self):
        query = self._get_sellables_query()
        sellables = Inventory.get_sellables_for_inventory(self.store, self.model.branch, query)
        if sellables.is_empty():
            info(_(u'No products have been found in the selected '
                   'categories.'))
            return False

        return True

    def on_confirm(self):
        # We are using this hook as a callback for the finish button
        branch = self.store.fetch(self.model.branch)
        responsible = self.store.fetch(self.model.user)
        query = self._get_sellables_query()
        return Inventory.create_inventory(self.store, branch, responsible, query)

    #
    # Kiwi Callback
    #

    def on_select_all__clicked(self, widget):
        self._select(list(self.category_tree), select_value=True)

    def on_unselect_all__clicked(self, widget):
        self._select(list(self.category_tree), select_value=False)

    def on_category_tree__cell_edited(self, tree, category, attr):
        self._select([category], select_value=category.selected)
