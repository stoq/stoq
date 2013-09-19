# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
#

import gtk

from kiwi.datatypes import number
from kiwi.ui.objectlist import empty_marker, ListLabel

from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

DEBUG_TREE_MODEL = False


def debug(func):
    if not DEBUG_TREE_MODEL:
        return func

    def wrapper(*args, **kwargs):
        retval = func(*args, **kwargs)
        print(func.__name__, args, kwargs, '->', retval)
        return retval

    return wrapper


class LazyObjectModelRow(object):
    def __init__(self, item, path, iter):
        self.item = item
        self.path = path
        self.parent = None  # not supported yet
        self.next = None  # not supported yet
        self.iter = iter

    def __getitem__(self, index):
        assert index == 0, index
        return self.item


# FIXME: Port to Gtk.TreeModel so it works under gi
class LazyObjectModel(gtk.GenericTreeModel, gtk.TreeSortable):

    __gtype_name__ = 'LazyObjectModel'

    def __init__(self, objectlist, result, executer, initial_count):
        """
        :param objectlist: a ObjectList
        :param result: a result set from ORM
        :param executer:
        :param initial_count: number of items to load the first time,
          this should at least be all visible rows
        """
        old_model = objectlist.get_model()
        self._objectlist = objectlist
        self._count = 0
        self._executer = executer
        self._initial_count = initial_count
        self._iters = []
        self._orig_result = result
        self._post_result = None
        self._result = None
        self._values = []
        self.old_model = old_model
        (self._sort_column_id,
         self._sort_order) = old_model.get_sort_column_id()
        if self._sort_column_id is None:
            self._sort_column_id = 0
        super(LazyObjectModel, self).__init__()
        self.props.leak_references = False
        self._load_result_set(result)

    def _load_result_set(self, result):
        self._post_result = self._executer.get_post_result(result)
        if self._post_result is not None:
            count = self._post_result.count
        else:
            count = result.count()
        self._count = count
        self._iters = list(range(0, count))
        self._result = result
        self._values = [empty_marker] * count
        self.load_items_from_results(0, self._initial_count)

    # GtkTreeModel

    @debug
    def on_get_flags(self):
        return gtk.TREE_MODEL_LIST_ONLY

    @debug
    def on_get_n_columns(self):
        return 1

    @debug
    def on_get_column_type(self, index):
        return object

    @debug
    def on_get_value(self, row, column):
        return self._values[row]

    @debug
    def on_get_iter(self, path):
        if self._iters:
            return self._iters[path[0]]

    @debug
    def on_get_path(self, row):
        return (row, )

    @debug
    def on_iter_parent(self, row):
        return None

    @debug
    def on_iter_next(self, row):
        if row + 1 < self._count:
            return self._iters[row + 1]
        else:
            return None

    @debug
    def on_iter_has_child(self, row):
        return False

    @debug
    def on_iter_children(self, row):
        if row is None and self._iters:
            return self._iters[0]
        else:
            return None

    @debug
    def on_iter_n_children(self, row):
        if row is None:
            return self._count
        else:
            return 0

    @debug
    def on_iter_nth_child(self, parent, n):
        if parent:
            return None
        else:
            return self._iters[n]

    def __len__(self):
        return self._count

    @debug
    def __getitem__(self, key):
        if isinstance(key, gtk.TreeIter):
            index = self.get_user_data(key)
        elif isinstance(key, (basestring, int)):
            index = int(key)
        elif isinstance(key, tuple):
            index = key[0]
        else:
            raise AssertionError(key)
        return LazyObjectModelRow(self._values[index], (index,), (index,))

    @debug
    def __contains__(self, value):
        return value in self._values

    # GtkTreeSortable

    if gtk.gtk_version >= (3, 0):
        @debug
        def do_get_sort_column_id(self):
            return (self._sort_order >= 0, self._sort_column_id, self._sort_order)
    else:
        # FIXME: Remove when done with gtk2
        @debug
        def do_get_sort_column_id_gtk2(self):
            return (self._sort_column_id, self._sort_order)
        do_get_sort_column_id = do_get_sort_column_id_gtk2

    @debug
    def do_set_sort_column_id(self, sort_column_id, sort_order):
        self.old_model.set_sort_column_id(sort_column_id, sort_order)
        changed_column = sort_column_id != self._sort_column_id
        self._sort_column_id = sort_column_id
        changed_order = sort_order != self._sort_order
        self._sort_order = sort_order

        if (not changed_column and
            not changed_order):
            return

        self._load_result_set(self._result)
        self.sort_column_changed()

    @debug
    def do_set_sort_func(self, sort_column_id, sort_func, user_data=None):
        pass

    @debug
    def do_set_default_sort_func(self, sort_func, user_data=None):
        pass

    @debug
    def do_has_default_sort_func(self):
        # Don't return True here, so that we can have only sorted/not sorted
        # statuses. If we return True, there is also the posibility of the
        # default order (thats when the query is not sorted)
        pass

    # Public API

    def clear(self):
        self._objectlist.set_model(self.old_model)
        self.old_model.clear()

    def load_items_from_results(self, start, end):
        """
        Fetchs rows from the database and displays in the model
        :param start: index of the first row to load
        :param end: index of the last row to load
        """
        end = min(end, self._count)
        load_total = end - start

        # Avoid loading items already loaded
        for i in range(start, end):
            if self._values[i] is empty_marker:
                break
            # Partial loading
            start = i
        else:
            return

        # If we moved the start value in the for above, also move the end value
        end = min(start + load_total, self._count)

        column = self._objectlist.get_columns()[self._sort_column_id]
        if hasattr(column, 'search_attribute'):
            # Even if it's defined, it could be None
            order_attr = column.search_attribute or column.attribute
        else:
            order_attr = column.attribute
        self._result = self._executer.get_ordered_result(self._orig_result,
                                                         order_attr)

        if self._sort_order == gtk.SORT_DESCENDING:
            # Results should be reversed, so we need to invert the start and
            # end values, and use the end of the list as a reference.
            # This should be as easy as reversed(self._results[-end:-start])
            # but storm does not support this.
            start_ = self._count - end
            end_ = self._count - start
            results = reversed(list(self._result[start_:end_]))
        else:
            results = list(self._result[start:end])

        has_loaded = False
        for i, item in enumerate(results, start):
            if self._values[i] is not empty_marker:
                continue
            has_loaded = True
            self._values[i] = item
            path = (i, )
            titer = self.create_tree_iter(i)
            # We are bypassing ObjectList to insert items in the model, but
            # ObjectList depends on knowing where the model is present for a few
            # actions. Let it know about this new item
            self._objectlist.set_instance_iter(item, titer)
            self.row_changed(path, titer)

        return has_loaded

    def get_post_data(self):
        return self._post_result


class LazyObjectListUpdater(object):
    """This is a helper that updates the list automatically when you
    scroll down in it. Similar to what twisted / facebook does (as of 2012)
    """

    # How many extra rows we should fetch, before and after the current page
    EXTRA_ROWS = 30

    # How many ms we should wait before loading items from the list
    SCROLL_TIMEOUT = 10

    # How many rows should we initially load
    INITIAL_ROWS = 50

    # If the quantity of results is less or equal than this, load
    # everything as it will be better than doing a lot of slices
    THRESHOLD = 250

    def __init__(self, search, objectlist):
        self._executer = search.get_query_executer()
        self._model = None
        self._objectlist = objectlist
        self._row_height = -1
        self._search = search
        self._timeout_queue = []
        self._treeview = self._objectlist.get_treeview()

        self._objectlist.connect(
            'sorting-changed', self._on_resuls__sorting_changed)
        self._vadj = self._objectlist.get_scrolled_window().get_vadjustment()
        self._vadj.connect(
            'value-changed', self._on_vadjustment__value_changed)

        # Limits doesn't make sense when using lazy search, the idea
        # is to always show everything.
        self._executer.set_limit(-1)

    def add_results(self, results):
        self._model = LazyObjectModel(self._objectlist, results,
                                      self._executer,
                                      initial_count=self.INITIAL_ROWS)
        self._objectlist.set_model(self._model)

    def _load_result_set(self, start, end):
        self._treeview.freeze_notify()

        count = len(self._model)
        if count <= self.THRESHOLD:
            start = 0
            end = count
        else:
            start = max(start[0] - self.EXTRA_ROWS, 0)
            end = min(end[0] + self.EXTRA_ROWS, count)

        loaded = self._model.load_items_from_results(start, end)
        if loaded:
            self._objectlist.update_selection()

        self._treeview.thaw_notify()

    def _get_row_height(self):
        if self._row_height == -1:
            column = self._treeview.get_columns()[0]
            self._row_height = column.cell_get_size()[-1]
        return self._row_height

    def _get_current_adjustment_upper(self):
        adjustment = self._vadj
        return (adjustment.value +
                adjustment.page_increment +
                adjustment.step_increment)

    def _maybe_load_more_search_results(self):
        # First check if we've already loaded all items
        res = self._treeview.get_visible_range()
        if res is None:
            return
        start, end = res

        def timeout_func(timeout):
            self._timeout_queue.remove(timeout)
            # If there are other timeouts, eg, the user scrolled very
            # quickly, don't do anything for a little while
            if self._timeout_queue:
                return False
            self._load_result_set(start, end)
            return False

        timeout = {}
        timeout['source_id'] = gtk.timeout_add(
            self.SCROLL_TIMEOUT, timeout_func, timeout)
        self._timeout_queue.append(timeout)

    def _on_vadjustment__value_changed(self, adjustment):
        self._maybe_load_more_search_results()

    def _on_resuls__sorting_changed(self, objectlist, attribute, sort_type):
        self._treeview.scroll_to_point(0, 0)


class LazySummaryLabel(ListLabel):
    def __init__(self, klist, column, label=_('Total:'), value_format='%s',
                 font_desc=None):
        ListLabel.__init__(self, klist, column, label, value_format, font_desc)
        if not issubclass(self._column.data_type, number):
            raise TypeError("data_type of column must be a number, not %r",
                            self._column.data_type)

    # Public API

    def update_total(self, value=None):
        """Recalculate the total value of all columns"""
        if value is None:
            return
        column = self._column
        self.set_value(column.as_string(value))
