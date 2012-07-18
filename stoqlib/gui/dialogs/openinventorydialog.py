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
        self.category = category
        self.parent = parent
        self.children = []
        self.description = category.description
        self.selected = True


class OpenInventoryDialog(BaseEditor):
    gladefile = 'OpenInventoryDialog'
    model_type = _TemporaryInventory
    title = _('Open Inventory')
    size = (750, 450)
    proxy_branch_widgets = ['open_date', 'branch_combo']

    def __init__(self, conn, branches):
        BaseEditor.__init__(self, conn, model=None)
        self._branches = branches
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
        for category in SellableCategory.get_base_categories(self.conn):
            self._append_category(category)

        self.category_tree.connect(
            'cell-edited', self._on_category_tree__cell_edited)

    def _update_widgets(self):
        all_selected = all([c.selected for c in self.category_tree])
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

    def _append_category(self, category, parent=None):
        row = self.category_tree.append(parent, _TemporaryCategory(category))

        for child in category.children:
            self._append_category(child, parent=row)

    def _get_sellables(self):
        selected = [c.category for c in self.category_tree if c.selected]
        include_uncategorized = self.include_uncategorized_check.get_active()

        return Sellable.get_unblocked_by_categories(self.conn, selected,
                                                    include_uncategorized)

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

    #
    # BaseEditorSlave
    #

    def create_model(self, conn):
        return _TemporaryInventory(conn)

    def setup_proxies(self):
        self.proxy = self.add_proxy(
            self.model, OpenInventoryDialog.proxy_branch_widgets)

    def validate_confirm(self, value=None):
        # This is a generator. It'll be evaluated to True
        # even if it's len should be 0. Use a list for comparison instead.
        if not list(self._get_sellables()):
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
            storable = sellable.product_storable
            if storable is None:
                continue
            # a sellable without stock can't be part of inventory
            if storable.get_stock_item(self.model.branch) is not None:
                recorded_quantity = storable.get_balance_for_branch(self.model.branch)
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
        self._select(list(self.category_tree), select_value=True)

    def on_unselect_all__clicked(self, widget):
        self._select(list(self.category_tree), select_value=False)

    def _on_category_tree__cell_edited(self, tree, category, attr):
        self._select([category], select_value=category.selected)
