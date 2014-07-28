# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2013 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import gobject
from kiwi.ui.objectlist import ObjectList, ObjectTree
from kiwi.utils import gsignal
from zope.interface import implementer

from stoqlib.gui.interfaces import ISearchResultView
from stoqlib.gui.widgets.lazyobjectlist import LazyObjectListUpdater


def _serialize_columns(treeview, d):
    for position, col in enumerate(treeview.get_columns()):
        # Can happen if there's an empty space on columns' header.
        # Normally on searchs that doesn't have an expand column.
        if not hasattr(col, 'attribute'):
            continue
        d[col.attribute] = (
            col.get_visible(),
            col.get_width(),
            col.get_sort_indicator(),
            int(col.get_sort_order()),  # enums are not serializable
            position,
        )


@implementer(ISearchResultView)
class SearchResultListView(ObjectList):
    """
    This class implements the ISearchResultView interface on top of
    a ObjectList.

    """
    __gtype_name__ = 'SearchResultListView'

    gsignal("item-activated", object)
    gsignal("item-popup-menu", object, object)

    def __init__(self):
        self._lazy_updater = None
        ObjectList.__init__(self)
        self.connect('double-click', self._on__double_click)
        self.connect('row-activated', self._on__row_activated)
        self.connect('right-click', self._on__right_click)

    #
    # ISearchResultView
    #

    def attach(self, search, columns):
        self._search = search
        self.set_columns(columns)

    def enable_lazy_search(self):
        self._lazy_updater = LazyObjectListUpdater(
            search=self._search,
            objectlist=self)

    def get_n_items(self):
        return len(self.get_model())

    def search_completed(self, results):
        if self._lazy_updater:
            self._lazy_updater.add_results(results)
        else:
            self.extend(results)

        summary_label = self._search.get_summary_label()
        if summary_label is None:
            return
        if self._lazy_updater and len(self):
            post = self.get_model().get_post_data()
            if post is not None:
                summary_label.update_total(post.sum)
        else:
            summary_label.update_total()

    def get_settings(self):
        d = {}
        _serialize_columns(self.get_treeview(), d)
        return d

    def get_selected_item(self):
        return self.get_selected()

    #
    # Callbacks
    #

    def _on__double_click(self, object_list, item):
        self.emit('item-activated', item)

    def _on__row_activated(self, object_list, item):
        self.emit('item-activated', item)

    def _on__right_click(self, object_list, results, event):
        self.emit('item-popup-menu', results, event)

gobject.type_register(SearchResultListView)


# Used by SellableCategorySearch

@implementer(ISearchResultView)
class SearchResultTreeView(ObjectTree):

    __gtype_name__ = 'SearchResultTreeView'

    gsignal("item-activated", object)
    gsignal("item-popup-menu", object, object)

    def __init__(self):
        ObjectTree.__init__(self)
        self.connect('double-click', self._on__double_click)
        self.connect('row-activated', self._on__row_activated)
        self.connect('right-click', self._on__right_click)

    #
    # Public API
    #

    def add_result(self, result):
        parent = result.get_parent()
        if parent:
            self.add_result(parent)
        if not result in self:
            self.append(parent, result)
            if parent:
                self.expand(parent)

    #
    # ISearchResultView
    #

    def attach(self, search, columns):
        self._search = search
        self.set_columns(columns)

    def enable_lazy_search(self):
        pass

    def get_n_items(self):
        return len(self.get_model())

    def search_completed(self, results):
        for result in results:
            self.add_result(result)

        summary_label = self._search.get_summary_label()
        if summary_label is not None:
            summary_label.update_total()

    def get_settings(self):
        d = {}
        _serialize_columns(self.get_treeview(), d)
        return d

    def get_selected_item(self):
        return self.get_selected()

    #
    # Callbacks
    #

    def _on__double_click(self, object_list, item):
        self.emit('item-activated', item)

    def _on__row_activated(self, object_list, item):
        self.emit('item-activated', item)

    def _on__right_click(self, object_list, results, event):
        self.emit('item-popup-menu', results, event)
