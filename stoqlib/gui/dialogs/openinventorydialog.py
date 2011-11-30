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


import datetime

from kiwi.ui.objectlist import Column

from stoqlib.api import api
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.inventory import Inventory, InventoryItem
from stoqlib.domain.sellable import Sellable, SellableCategory
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.message import info
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _TemporaryInventory(object):
    def __init__(self, conn):
        self.open_date = datetime.datetime.now()
        self.branch = None
        self.user = api.get_current_user(conn)


class _TemporaryCategory(object):
    def __init__(self, category=None, parent=None):
        self.obj = category
        self.parent = parent
        self.children = []
        if category is not None:
            self.description = category.description
            self.selected = True
        else:
            self.description = None
            self.selected = False

    def has_children(self):
        # do not consider this special case
        # see OpenInventoryDialog._setup_category_tree
        if len(self.children) == 1 and self.children[0].obj is None:
            return False
        else:
            return self.children

    def get_subcategories(self, conn):
        """Returns the categories which I am the base category of them"""
        return SellableCategory.selectBy(category=self.obj,
                                         connection=conn)

    def _get_selected(self, categories):
        return [c.obj for c in categories if c.selected]

    def get_selected_subcategories(self, conn):
        """Returns a list of selected categories.
        If I am a parent node:
            - Return all my selected children
        If I am a child node:
            - Return all my selected siblings
        """
        if self.parent is None:
            if not self.selected:
                return []

            if not self.has_children():
                return list(self.get_subcategories(conn))
            else:
                return self._get_selected(self.children)
        else:
            siblings = self.parent.children
            return self._get_selected(siblings)


class OpenInventoryDialog(BaseEditor):
    gladefile = 'OpenInventoryDialog'
    model_type = _TemporaryInventory
    title = _('Open Inventory')
    size = (750, 450)
    proxy_branch_widgets = ['open_date', 'branch_combo']

    def __init__(self, conn, branches):
        BaseEditor.__init__(self, conn, model=None)
        self._branches = branches
        self._categories = []
        self._setup_widgets()
        self._update_widgets()

    def _setup_widgets(self):
        # open inventory button
        self.main_dialog.ok_button.set_label(_(u"_Open"))
        # select all the branches that are able to open an inventory
        branches = []
        for branch in self._branches:
            branches.append((branch.person.name, branch))
        self.branch_combo.prefill(branches)
        self.branch_combo.select(branches[0][1])

        self.username.set_text(self.model.user.person.name)
        self.open_time.set_text(self.model.open_date.strftime("%X"))
        # load categories
        self.category_tree.set_columns(self._get_columns())
        self._setup_category_tree()

        self.category_tree.connect(
            'cell-edited', self._on_category_tree__cell_edited)
        self.category_tree.connect(
            'row-expanded', self._on_category_tree__row_expanded)

    def _update_widgets(self):
        all_selected = all([c.selected for c in self._categories])
        self.select_all.set_sensitive(not all_selected)
        has_selected = self._has_selected()
        self.unselect_all.set_sensitive(has_selected)
        self.refresh_ok(has_selected)

    def _get_columns(self):
        return [Column('selected', title=" ", width=50,
                        data_type=bool, editable=True),
                Column('description', title=_(u"Description"),
                        data_type=str, expand=True, sorted=True,
                        expander=True)]

    def _setup_category_tree(self):
        base_categories = SellableCategory.get_base_categories(self.conn)
        for base_category in base_categories:
            row = self.category_tree.append(
                    None, _TemporaryCategory(base_category))
            self._categories.append(row)
            # for each node we add a dummy child, forcing the expander
            # visibility. When it be expanded, we'll query for the real
            # child of a node.
            dummy_child = _TemporaryCategory()
            self.category_tree.append(row, dummy_child)
            row.children.append(dummy_child)

    def _get_sellables(self):
        selected = []
        for category in self._categories:
            selected.extend(category.get_selected_subcategories(self.conn))

        if not selected:
            return []

        include_uncategorized = self.include_uncategorized_check.get_active()
        return Sellable.get_unblocked_by_categories(self.conn, selected,
                                                    include_uncategorized)

    def _select(self, categories, select_value):
        for category in categories:
            category.selected = select_value
            self.category_tree.update(category)
            if category.children:
                self._select(category.children, select_value)
        self._update_widgets()

    def _select_all(self):
        self._select(self._categories, True)

    def _unselect_all(self):
        self._select(self._categories, False)

    def _update_category_selection(self, category):
        if category.parent is None:
            # The children follow the father's selection value
            self._select(category.children, category.selected)
        else:
            parent = category.parent
            has_child_selected = any([c.selected for c in parent.children])
            parent.selected = has_child_selected
            self.category_tree.update(parent)

    def _expand_category_tree(self, category):
        if not category.has_children():
            children = category.children
            # remove our dummy child
            self.category_tree.remove(children[0])
            children.remove(children[0])
            # then add the real ones
            for child_category in category.get_subcategories(self.conn):
                child = _TemporaryCategory(child_category, parent=category)
                child.selected = category.selected
                self.category_tree.append(category, child)
                children.append(child)
            self.category_tree.expand(category)

    def _has_selected(self):
        return any([c.selected for c in self._categories])

    #
    # BaseEditorSlave
    #

    def create_model(self, conn):
        return _TemporaryInventory(conn)

    def setup_proxies(self):
        self.proxy = self.add_proxy(
            self.model, OpenInventoryDialog.proxy_branch_widgets)

    def validate_confirm(self, value=None):
        if not self._get_sellables():
            info(_(u'No products have been found in the selected '
                    'categories.'))
            return False

        return True

    def on_confirm(self):
        # We are using this hook as a callback for the finish button
        inventory = Inventory(open_date=self.model.open_date,
                              branch=self.model.branch,
                              connection=self.conn)
        for sellable in self._get_sellables():
            storable = IStorable(sellable.product, None)
            if storable is None:
                continue
            # a sellable without stock can't be part of inventory
            if storable.get_stock_item(self.model.branch) is not None:
                recorded_quantity = storable.get_full_balance(self.model.branch)
                InventoryItem(product=sellable.product,
                              product_cost=sellable.cost,
                              recorded_quantity=recorded_quantity,
                              inventory=inventory,
                              connection=self.conn)
        return True

    #
    # Kiwi Callback
    #

    def on_select_all__clicked(self, widget):
        self._select_all()

    def on_unselect_all__clicked(self, widget):
        self._unselect_all()

    def _on_category_tree__cell_edited(self, tree, category, attr):
        self._update_category_selection(category)
        self._update_widgets()

    def _on_category_tree__row_expanded(self, tree, parent_category):
        self._expand_category_tree(parent_category)
