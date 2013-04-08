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

import datetime
from decimal import Decimal

import gobject
import gtk
from kiwi.currency import currency
from kiwi.utils import gsignal
from kiwi.ui.objectlist import (ObjectList, ObjectTree,
                                SummaryLabel)

from stoqlib.database.queryexecuter import (NumberQueryState, StringQueryState,
                                            DateQueryState, DateIntervalQueryState,
                                            NumberIntervalQueryState, BoolQueryState,
                                            QueryExecuter)
from stoqlib.enums import SearchFilterPosition
from stoqlib.gui.columns import SearchColumn
from stoqlib.gui.search.searchfilters import (StringSearchFilter, ComboSearchFilter,
                                              DateSearchFilter, NumberSearchFilter,
                                              BoolSearchFilter, SearchFilter)
from stoqlib.gui.widgets.lazyobjectlist import (LazyObjectListUpdater,
                                                LazySummaryLabel)
from stoqlib.gui.widgets.searchfilterbutton import SearchFilterButton
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class SearchResults(ObjectList):
    def __init__(self, columns):
        ObjectList.__init__(self, columns)

    def add_results(self, results):
        self.extend(results)


class SearchResultsTree(ObjectTree):
    def __init__(self, columns):
        ObjectTree.__init__(self, columns)

    def add_results(self, results):
        for result in results:
            self._add_result(result)

    def _add_result(self, result):
        parent = result.get_parent()
        if parent:
            self._add_result(parent)
        if not result in self:
            self.append(parent, result)
            if parent:
                self.expand(parent)


class SearchContainer(gtk.VBox):
    """
    A search container is a widget which consists of:
    - search entry (w/ a label) (:class:`StringSearchFilter`)
    - search button
    - objectlist result (:class:`SearchResults` or class:`SearchResultsTree)
    - a query executer (:class:`stoqlib.database.queryexecuter.QueryExecuter`)

    Additionally you can add a number of search filters to the SearchContainer.
    You can chose if you want to add the filter in the top-left corner
    of bottom, see :class:`SearchFilterPosition`
    """
    __gtype_name__ = 'SearchContainer'
    filter_label = gobject.property(type=str)
    results_class = SearchResults
    gsignal("search-completed", object, object)

    def __init__(self, columns=None, tree=False, chars=25):
        """
        Create a new SearchContainer object.
        :param columns: a list of :class:`kiwi.ui.objectlist.Column`
        :param tree: if we should list the results as a tree
        :param chars: maximum number of chars used by the search entry
        """
        if tree:
            self.results_class = SearchResultsTree

        gtk.VBox.__init__(self)
        self._auto_search = True
        self._columns = columns
        self._lazy_updater = None
        self._model = None
        self._query_executer = None
        self._search_filters = []
        self._summary_label = None
        self.menu = None

        search_filter = StringSearchFilter(_('Search:'), chars=chars,
                                           container=self)
        search_filter.connect('changed', self._on_search_filter__changed)
        self._search_filters.append(search_filter)
        self._primary_filter = search_filter

        self._create_ui()

    #
    # GObject
    #

    def do_set_property(self, pspec, value):
        if pspec.name == 'filter-label':
            self._primary_filter.set_label(value)
        else:
            raise AssertionError(pspec.name)

    def do_get_property(self, pspec):
        if pspec.name == 'filter-label':
            return self._primary_filter.get_label()
        else:
            raise AssertionError(pspec.name)

    #
    # Public API
    #

    def add_filter(self, search_filter, position=SearchFilterPosition.BOTTOM,
                   columns=None, callback=None, use_having=False):
        """
        Adds a search filter
        :param search_filter: the search filter
        :param postition: a :class:`SearchFilterPosition` enum
        :param columns:
        :param callback:
        """
        if not isinstance(search_filter, SearchFilter):
            raise TypeError("search_filter must be a SearchFilter subclass, "
                            "not %r" % (search_filter,))

        executer = self.get_query_executer()
        if executer:
            if callback:
                if not callable(callback):
                    raise TypeError("callback must be callable")
                executer.add_filter_query_callback(search_filter, callback,
                                                   use_having=use_having)
            elif columns:
                executer.set_filter_columns(search_filter, columns,
                                            use_having=use_having)
        else:
            if columns or callback:
                raise TypeError(
                    "You need to set an executor before calling set_filters "
                    "with columns or callback set")

        assert not search_filter.get_parent()
        self.set_filter_position(search_filter, position)
        search_filter.connect('changed', self._on_search_filter__changed)
        search_filter.connect('removed', self._on_search_filter__remove)
        self._search_filters.append(search_filter)

    def remove_filter(self, filter):
        self.filters_box.remove(filter)
        self._search_filters.remove(filter)
        filter.destroy()

        if self._auto_search:
            self.search()

    def add_filter_by_column(self, column):
        """Add a filter accordingly to the column specification

        :param column: a SearchColumn instance
        """
        title = column.get_search_label()
        if column.data_type is not bool:
            title += ':'

        if column.data_type == datetime.date:
            filter = DateSearchFilter(title)
            if column.valid_values:
                filter.clear_options()
                filter.add_custom_options()
                for opt in column.valid_values:
                    filter.add_option(opt)
                filter.select(column.valid_values[0])

        elif (column.data_type == Decimal or
              column.data_type == int or
              column.data_type == currency):
            filter = NumberSearchFilter(title)
            if column.data_type != int:
                filter.set_digits(2)
        elif column.data_type == str:
            if column.valid_values:
                filter = ComboSearchFilter(title, column.valid_values)
            else:
                filter = StringSearchFilter(title)
                filter.enable_advanced()
        elif column.data_type == bool:
            filter = BoolSearchFilter(title)
        else:
            raise NotImplementedError(title, column.data_type)

        filter.set_removable()
        attr = column.search_attribute or column.attribute
        self.add_filter(filter, columns=[attr],
                        callback=column.search_func,
                        use_having=column.use_having)

        if column.data_type is not bool:
            label = filter.get_title_label()
            label.set_alignment(1.0, 0.5)
            self.label_group.add_widget(label)
        combo = filter.get_mode_combo()
        if combo:
            self.combo_group.add_widget(combo)

        return filter

    def get_search_filters(self):
        return self._search_filters

    def get_search_filter_by_label(self, label):
        for search_filter in self._search_filters:
            if search_filter.label == label:
                return search_filter

    def set_filter_position(self, search_filter, position):
        """
        Set the the filter position.
        :param search_filter:
        :param position:
        """
        if search_filter.get_parent():
            search_filter.get_parent().remove(search_filter)

        if position == SearchFilterPosition.TOP:
            self.hbox.pack_start(search_filter, False, False)
            self.hbox.reorder_child(search_filter, 0)
        elif position == SearchFilterPosition.BOTTOM:
            self.filters_box.pack_start(search_filter, False, False)
        search_filter.show()

    def get_filter_position(self, search_filter):
        """
        Get filter by position.
        :param search_filter:
        """
        if search_filter.get_parent() == self.hbox:
            return SearchFilterPosition.TOP
        elif search_filter.get_parent() == self:
            return SearchFilterPosition.BOTTOM
        else:
            raise AssertionError(search_filter)

    def set_query_executer(self, query_executer):
        """
        Ties a QueryExecuter instance to the SearchContainer class
        :param querty_executer: a querty executer
        :type querty_executer: a :class:`QueryExecuter` subclass
        """
        if not isinstance(query_executer, QueryExecuter):
            raise TypeError("query_executer must be a QueryExecuter instance")

        self._query_executer = query_executer

    def get_query_executer(self):
        """
        Fetchs the QueryExecuter for the SearchContainer
        :returns: a querty executer
        :rtype: a :class:`QueryExecuter` subclass
        """
        return self._query_executer

    def get_primary_filter(self):
        """
        Fetches the primary filter for the SearchContainer.
        The primary filter is the filter attached to the standard entry
        normally used to do free text searching
        :returns: the primary filter
        """
        return self._primary_filter

    def search(self, clear=True):
        """
        Starts a search.
        Fetches the states of all filters and send it to a query executer and
        finally puts the result in the result class
        """
        if not self._query_executer:
            raise ValueError("A query executer needs to be set at this point")
        states = [(sf.get_state()) for sf in self._search_filters]
        results = self._query_executer.search(states)
        self.add_results(results, clear=clear)
        self.emit("search-completed", self.results, states)
        if self._summary_label:
            if self._lazy_updater and len(self.results):
                post = self.results.get_model().get_post_data()
                if post is not None:
                    self._summary_label.update_total(post.sum)
            else:
                self._summary_label.update_total()

    def enable_lazy_search(self):
        self._lazy_updater = LazyObjectListUpdater(
            executer=self._query_executer,
            search=self)
        # Limits doesn't make sense when using lazy search, the idea
        # is to always show everything.
        self._query_executer.set_limit(-1)

    def set_auto_search(self, auto_search):
        """
        Enables/Disables auto search which means that the search result box
        is automatically populated when a filter changes
        :param auto_search: True to enable, False to disable
        """
        self._auto_search = auto_search

    def set_text_field_columns(self, columns):
        if self._primary_filter is None:
            raise ValueError("The primary filter is disabled")

        if not self._query_executer:
            raise ValueError("A query executer needs to be set at this point")

        self._query_executer.set_filter_columns(self._primary_filter, columns)

    def disable_search_entry(self):
        """
        Disables the search entry
        """
        self.search_entry.hide()
        self._primary_filter.hide()
        self._search_filters.remove(self._primary_filter)
        self._primary_filter = None

    def set_summary_label(self, column, label='Total:', format='%s',
                          parent=None):
        """
        Adds a summary label to the result set
        :param column: the column to sum from
        :param label: the label to use, defaults to 'Total:'
        :param format: the format, defaults to '%%s', must include '%%s'
        :param parent: the parent widget a label should be added to or
           None if it should be added to the SearchContainer
        """
        if not '%s' in format:
            raise ValueError("format must contain %s")

        try:
            self.results.get_column_by_name(column)
        except LookupError:
            raise ValueError("%s is not a valid column" % (column,))

        if not parent:
            parent = self
        elif not isinstance(parent, gtk.Box):
            raise TypeError("parent %r must be a GtkBox subclass" % (
                parent))

        if self._summary_label:
            self._summary_label.get_parent().remove(self._summary_label)
        if self._lazy_updater:
            summary_label_class = LazySummaryLabel
        else:
            summary_label_class = SummaryLabel
        self._summary_label = summary_label_class(klist=self.results,
                                                  column=column,
                                                  label=label,
                                                  value_format=format)
        parent.pack_start(self._summary_label, False, False)
        self._summary_label.show()

    @property
    def summary_label(self):
        return self._summary_label

    def enable_advanced_search(self):
        self._create_advanced_search()

    def add_results(self, results, clear=True):
        if clear:
            self.results.clear()

        if self._lazy_updater:
            self._lazy_updater.add_results(results)
        else:
            self.results.add_results(results)

    def get_filter_states(self):
        dict_state = {}
        for search_filter in self._search_filters:
            dict_state[search_filter.label] = data = {}
            state = search_filter.get_state()
            if isinstance(state, DateQueryState):
                data['start'] = state.date
            elif isinstance(state, BoolQueryState):
                data['value'] = state.value
            elif isinstance(state, DateIntervalQueryState):
                data['start'] = state.start
                data['end'] = state.end
            elif isinstance(state, NumberQueryState):
                data['value'] = state.value
                if hasattr(state, 'value_id'):
                    data['value_id'] = state.value_id
                    data['value'] = None
            elif isinstance(state, NumberIntervalQueryState):
                data['start'] = state.start
                data['end'] = state.end
            elif isinstance(state, StringQueryState):
                data['text'] = state.text
                data['mode'] = state.mode
            else:
                raise NotImplementedError(state)
        return dict_state

    def set_filter_states(self, dict_state):
        for label, filter_state in dict_state.items():
            search_filter = self.get_search_filter_by_label(label)
            if search_filter is None:
                continue
            search_filter.set_state(**filter_state)

    #
    # Callbacks
    #

    def _on_search_button__clicked(self, button):
        self.search()

    def _on_search_entry__activate(self, button):
        self.search()

    def _on_search_filter__remove(self, filter):
        self.remove_filter(filter)

    def _on_search_filter__changed(self, search_filter):
        if self._auto_search:
            self.search()

    #
    # Private
    #

    def _create_ui(self):
        self._create_basic_search()

        self.results = self.results_class(self._columns)
        self.pack_start(self.results, True, True, 0)
        self.results.show()

    def _create_basic_search(self):
        filters_box = gtk.VBox()
        filters_box.show()
        self.pack_start(filters_box, expand=False)

        hbox = gtk.HBox()
        hbox.set_border_width(3)
        filters_box.pack_start(hbox, False, False)
        hbox.show()
        self.hbox = hbox

        widget = self._primary_filter
        self.hbox.pack_start(widget, False, False)
        widget.show()

        self.search_entry = self._primary_filter.entry
        self.search_entry.connect('activate',
                                  self._on_search_entry__activate)

        self.search_button = SearchFilterButton(stock=gtk.STOCK_FIND)
        self.search_button.connect('clicked', self._on_search_button__clicked)
        hbox.pack_start(self.search_button, False, False)
        self.search_button.show()

        self.filters_box = filters_box

    def _create_advanced_search(self):
        self.label_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        self.combo_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)

        self.menu = gtk.Menu()
        for column in self._columns:
            if not isinstance(column, SearchColumn):
                continue

            if column.data_type not in (datetime.date, Decimal, int, currency,
                                        str, bool):
                continue

            title = column.get_search_label()

            menu_item = gtk.MenuItem(title)
            menu_item.set_data('column', column)
            menu_item.show()
            menu_item.connect('activate', self._on_menu_item_activate)
            self.menu.append(menu_item)

    def _on_menu_item_activate(self, item):
        column = item.get_data('column')
        if column is None:
            return

        self.add_filter_by_column(column)
