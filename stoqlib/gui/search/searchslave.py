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
import decimal
import logging
import os
import warnings

import gtk
from kiwi.currency import currency
from kiwi.ui.objectlist import SummaryLabel
from kiwi.ui.delegates import SlaveDelegate
from kiwi.utils import gsignal
from zope.interface.verify import verifyClass

from stoqlib.api import api
from stoqlib.database.queryexecuter import (NumberQueryState, StringQueryState,
                                            DateQueryState, DateIntervalQueryState,
                                            NumberIntervalQueryState, BoolQueryState,
                                            QueryExecuter, MultiQueryState)
from stoqlib.enums import SearchFilterPosition
from stoqlib.gui.interfaces import ISearchResultView
from stoqlib.gui.search.searchcolumns import SearchColumn
from stoqlib.gui.search.searchfilters import (StringSearchFilter, ComboSearchFilter,
                                              DateSearchFilter, NumberSearchFilter,
                                              BoolSearchFilter, SearchFilter,
                                              MultiSearchFilter)
from stoqlib.gui.search.searchresultview import (SearchResultListView,
                                                 SearchResultTreeView)
from stoqlib.gui.widgets.lazyobjectlist import LazySummaryLabel
from stoqlib.gui.widgets.searchfilterbutton import SearchFilterButton
from stoqlib.lib.osutils import get_application_dir
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

log = logging.getLogger(__name__)


# TODO:
# * Improve SearchResultView selection API
# * Simplify all call sites, esp application.py

class SearchSlave(SlaveDelegate):
    """
    A search container is a widget which consists of:
    - search entry (w/ a label) (:class:`StringSearchFilter`)
    - search button
    - result view (:class:`SearchResultListView` or class:`SearchResultTreeView`)
    - a query executer (:class:`stoqlib.database.queryexecuter.QueryExecuter`)

    Additionally you can add a number of search filters to the SearchContainer.
    You can chose if you want to add the filter in the top-left corner
    of bottom, see :class:`SearchFilterPosition`
    """
    result_view_class = SearchResultListView

    gsignal("search-completed", object, object)
    gsignal("result-item-activated", object)
    gsignal("result-item-popup-menu", object, object)
    gsignal("result-selection-changed")

    def __init__(self, columns=None,
                 tree=False,
                 restore_name=None,
                 chars=25,
                 store=None,
                 search_spec=None,
                 fast_iter=False,
                 result_view_class=None):
        """
        Create a new SearchContainer object.
        :param columns: a list of :class:`kiwi.ui.objectlist.Column`
        :param tree: if we should list the results as a tree
        :param restore_name:
        :param chars: maximum number of chars used by the search entry
        :param store: a database store
        :param search_spec: a search spec for store to find on
        """
        if tree:
            self.result_view_class = SearchResultTreeView

        if result_view_class:
            self.result_view_class = result_view_class

        self._auto_search = True
        self._lazy_search = False
        self._last_results = None
        self._model = None
        self._query_executer = None
        self._restore_name = restore_name
        self._search_filters = []
        self._selected_item = None
        self._summary_label = None
        self._search_spec = search_spec
        self._fast_iter = fast_iter
        self.store = store
        self.menu = None
        self.result_view = None
        self._settings_key = 'search-columns-%s' % (
            api.get_current_user(self.store).username, )
        self.columns = self.restore_columns(columns)

        self.vbox = gtk.VBox()
        SlaveDelegate.__init__(self, toplevel=self.vbox)
        self.vbox.show()

        search_filter = StringSearchFilter(_('Search:'), chars=chars,
                                           container=self)
        search_filter.connect('changed', self._on_search_filter__changed)
        self._search_filters.append(search_filter)
        self._primary_filter = search_filter

        self._create_ui()
        self.focus_search_entry()

    #
    # Private API
    #

    def _create_ui(self):
        self._create_basic_search()

        self.set_result_view(self.result_view_class, refresh=False)

    def _create_basic_search(self):
        # This hbox is here so we can have a padding on the filters
        # from the left window edge
        filters_container = gtk.HBox()
        filters_container.show()

        filters_box = gtk.VBox(spacing=6)
        filters_container.pack_start(filters_box, False, False, 6)
        filters_box.show()

        self.vbox.pack_start(filters_container, False, True, 6)

        hbox = gtk.HBox()
        filters_box.pack_start(hbox, False, False)
        hbox.show()
        self.hbox = hbox

        widget = self._primary_filter
        self.hbox.pack_start(widget, False, False)
        widget.show()

        self.search_entry = self._primary_filter.entry

        self.search_button = SearchFilterButton(stock=gtk.STOCK_FIND)
        hbox.pack_start(self.search_button, False, False)
        self.search_button.show()

        self.filters_box = filters_box

    def _migrate_from_pickle(self):
        username = api.get_current_user(self.store).username
        filename = os.path.join(get_application_dir(), 'columns-%s' % username,
                                self._restore_name + '.pickle')
        log.info("Migrating columns from pickle: %s" % (filename, ))
        try:
            with open(filename) as fd:
                import cPickle
                return cPickle.load(fd)
        except Exception, e:
            log.info("Exception while migrating: %r" % (e, ))
            return {}

    def _set_filter_position(self, search_filter, position):
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

    #
    # Properties
    #

    @property
    def results(self):
        warnings.warn("Use .result_view instead", DeprecationWarning, stacklevel=2)
        return self.result_view

    @property
    def summary_label(self):
        return self._summary_label

    #
    # Public API
    #

    def clear(self):
        """
        Clears the result list
        """
        self.result_view.clear()

    def refresh(self):
        """
        Triggers a search again with the currently selected inputs
        """
        self.search()

    def search(self, clear=True):
        """
        Starts a search.
        Fetches the states of all filters and send it to a query executer and
        finally puts the result in the result class
        """
        executer = self.get_query_executer()
        states = [(sf.get_state()) for sf in self._search_filters]
        results = executer.search(states)
        if clear:
            self.result_view.clear()
        if self._fast_iter:
            results = results.fast_iter()
        self.result_view.search_completed(results)

        if self.result_view.get_n_items() == 0:
            self.set_message(_("Nothing found."))
        self.emit("search-completed", self.result_view, states)
        if self._selected_item:
            self.result_view.select(self._selected_item)

        self._last_results = results
        self._last_states = states

    def select(self, item):
        self.result_view.select(item)

    def get_selected_item(self):
        return self.result_view.get_selected_item()

    def focus_search_entry(self):
        """
        Grabs the focus of the search entry
        """
        self.search_entry.grab_focus()

    def disable_search_entry(self):
        """
        Disables the search entry
        """
        self.search_entry.hide()
        self._primary_filter.hide()
        self._search_filters.remove(self._primary_filter)
        self._primary_filter = None

    def enable_advanced_search(self):
        """
        Enables an advanced search
        """
        self.label_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        self.combo_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)

        self.menu = gtk.Menu()
        for column in self.columns:
            if not isinstance(column, SearchColumn):
                continue

            if column.data_type not in (datetime.date, decimal.Decimal, int, currency,
                                        str, bool):
                continue

            attr = column.search_attribute or column.attribute
            self.add_filter_option(attr, column.get_search_label(),
                                   column.data_type, column.valid_values,
                                   column.search_func, column.use_having,
                                   column.multiple_selection)

    def add_filter_option(self, attr, title, data_type, valid_values=None,
                          callback=None, use_having=False,
                          multiple_selection=False):
        """Adds a new advanced filter option

        Use this if you need a filter option in the advanced filters when you
        don't have a equivalente SearchColumn in the object list. If its
        possible to add the column, you should probably do that.

        See add_filter_by_attribute for more information
        """
        assert data_type in (datetime.date, decimal.Decimal, int, currency, str,
                             bool)
        menu_item = gtk.MenuItem(title)
        menu_item.show()
        menu_item.connect('activate', self._on_menu_item__activate, attr, title,
                          data_type, valid_values, callback, use_having,
                          multiple_selection)
        self.menu.append(menu_item)

    def set_message(self, message):
        self.result_view.set_message(message)

    def get_column_by_attribute(self, attribute):
        """Returns a column by its model attribute."""
        for column in self.columns:
            if column.attribute == attribute:
                return column

    def set_query(self, callback):
        """
        Overrides the default query mechanism.

        :param callback: a callable which till take two arguments (query, store)
        """
        executer = self.get_query_executer()
        executer.set_query(callback)

    def set_search_spec(self, search_spec):
        """
        Update the search spec this search uses to search

        :param search_spec: a search spec for store to find on
        """
        executer = self.get_query_executer()
        executer.set_search_spec(search_spec)

    def get_query_executer(self):
        """
        Fetchs the QueryExecuter for the SearchContainer

        :returns: a querty executer
        :rtype: a :class:`QueryExecuter` subclass
        """
        if self._query_executer is None:
            executer = QueryExecuter(self.store)
            if not self._lazy_search:
                executer.set_limit(sysparam.get_int('MAX_SEARCH_RESULTS'))
            if self._search_spec is not None:
                executer.set_search_spec(self._search_spec)
            self._query_executer = executer
        return self._query_executer

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
        self._set_filter_position(search_filter, position)
        search_filter.connect('changed', self._on_search_filter__changed)
        search_filter.connect('removed', self._on_search_filter__remove)
        self._search_filters.append(search_filter)

    def remove_filter(self, filter):
        self.filters_box.remove(filter)
        self._search_filters.remove(filter)
        filter.destroy()

        if self._auto_search:
            self.search()

    def add_filter_by_attribute(self, attr, title, data_type, valid_values=None,
                                callback=None, use_having=False,
                                multiple_selection=False):
        """Add a filter accordingly to the attributes specified

        :param attr: attribute that will be filtered. This can be either the
          name of the attribute or the attribute itself.
        :param title: the title of the filter that will be visible in the
                      interface
        :param data_type: the attribute type (str, bool, decimal, etc)
        :param callback: the callback function that will be triggered
        :param use_having: use having expression in the query
        """
        if data_type is not bool:
            title += ':'

        if data_type == datetime.date:
            filter = DateSearchFilter(title)
            if valid_values:
                filter.clear_options()
                filter.add_custom_options()
                for opt in valid_values:
                    filter.add_option(opt)
                filter.select(valid_values[0])

        elif (data_type == decimal.Decimal or
              data_type == int or
              data_type == currency):
            filter = NumberSearchFilter(title)
            if data_type != int:
                filter.set_digits(2)
        elif data_type == str:
            if multiple_selection:
                assert valid_values, "need valid_values for multiple_selection"
                filter = MultiSearchFilter(title, valid_values)
            elif valid_values:
                filter = ComboSearchFilter(title, valid_values)
                filter.enable_advanced()
            else:
                filter = StringSearchFilter(title)
                filter.enable_advanced()
        elif data_type == bool:
            filter = BoolSearchFilter(title)
        else:
            raise NotImplementedError(title, data_type)

        filter.set_removable()
        self.add_filter(filter, columns=[attr],
                        callback=callback,
                        use_having=use_having)

        if data_type is not bool:
            label = filter.get_title_label()
            label.set_alignment(1.0, 0.5)
            self.label_group.add_widget(label)
        combo = filter.get_mode_combo()
        if combo:
            self.combo_group.add_widget(combo)

        return filter

    def parse_states(self):
        """ Returns the states as clauses
        """
        states = [(sf.get_state()) for sf in self._search_filters]
        return self.get_query_executer().parse_states(states)

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
                data['mode'] = state.mode
                if hasattr(state, 'value_id'):
                    data['value_id'] = state.value_id
                    data['value'] = None
            elif isinstance(state, NumberIntervalQueryState):
                data['start'] = state.start
                data['end'] = state.end
            elif isinstance(state, StringQueryState):
                data['text'] = state.text
                data['mode'] = state.mode
            elif isinstance(state, MultiQueryState):
                # Converting to list since set is not serializable
                data['values'] = list(state.values)
            else:
                raise NotImplementedError(state)
        return dict_state

    def set_filter_states(self, dict_state):
        for label, filter_state in dict_state.items():
            search_filter = self.get_search_filter_by_label(label)
            if search_filter is None:
                continue
            search_filter.set_state(**filter_state)

    def get_search_filters(self):
        return self._search_filters

    def get_search_filter_by_label(self, label):
        for search_filter in self._search_filters:
            if search_filter.label == label:
                return search_filter

    def get_primary_filter(self):
        """
        Fetches the primary filter for the SearchContainer.
        The primary filter is the filter attached to the standard entry
        normally used to do free text searching
        :returns: the primary filter
        """
        return self._primary_filter

    def enable_lazy_search(self):
        if self.result_view:
            self.result_view.enable_lazy_search()
        self._lazy_search = True

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

        executer = self.get_query_executer()
        executer.set_filter_columns(self._primary_filter, columns)

    def set_summary_label(self, column, label='Total:', format='%s',
                          parent=None):
        """
        Adds a summary label to the result set

        :param column: the column to sum from
        :param label: the label to use, defaults to 'Total:'
        :param format: the format, defaults to '%%s', must include '%%s'
        :param parent: the parent widget a label should be added to or
           ``None`` if it should be added to the SearchContainer
        """
        if not '%s' in format:
            raise ValueError("format must contain %s")

        try:
            self.result_view.get_column_by_name(column)
        except LookupError:
            raise ValueError("%s is not a valid column" % (column,))

        if not parent:
            parent = self.vbox
        elif not isinstance(parent, gtk.Box):
            raise TypeError("parent %r must be a GtkBox subclass" % (
                parent))

        if self._summary_label:
            self._summary_label.get_parent().remove(self._summary_label)
        if self._lazy_search:
            summary_label_class = LazySummaryLabel
        else:
            summary_label_class = SummaryLabel
        self._summary_label = summary_label_class(klist=self.result_view,
                                                  column=column,
                                                  label=label,
                                                  value_format=format)
        parent.pack_start(self._summary_label, False, False)
        self._summary_label.show()

    def get_summary_label(self):
        return self._summary_label

    def get_last_results(self):
        return self._last_results

    def set_result_view(self, result_view_class, refresh=False):
        """
        Creates a new result view and attaches it to this search container.

        If a previous view was created it will be destroyed.
        :param result_view_class: a result view factory
        :param refresh: ``True`` if the results should be updated
        """

        if not verifyClass(ISearchResultView, result_view_class):
            raise TypeError("%s needs to implement ISearchResultView" % (
                result_view_class, ))

        if self.result_view:
            item = self.result_view.get_selected_item()
            self.vbox.remove(self.result_view)
            self.result_view = None
        else:
            item = None

        self.result_view = result_view_class()
        self.result_view.attach(search=self,
                                columns=self.columns)

        if self._lazy_search:
            self.result_view.enable_lazy_search()

        self.vbox.pack_start(self.result_view, True, True, 0)

        if refresh:
            if item is not None:
                self._selected_item = item
            self.search()

        self.result_view.show()

    def save_columns(self):
        if not self._restore_name:
            return

        d = self.result_view.get_settings()
        columns = api.user_settings.get(self._settings_key, {})
        columns[self._restore_name] = d

    def restore_columns(self, cols):
        if not self._restore_name:
            return cols

        columns = api.user_settings.get(self._settings_key, {})
        if columns:
            saved = columns.get(self._restore_name, {})
        else:
            saved = self._migrate_from_pickle()

        cols_dict = {}
        for original_pos, col in enumerate(cols):
            attr = col.attribute
            props = saved.get(attr)
            # This will happen for two reasons: a) the column is referenced by
            # another one (only the column that references is saved) and
            # b) Its a brand new column (not saved in the preferences)
            if not props:
                cols_dict[attr] = (col, original_pos)
                continue

            col.visible = props[0]
            # Expanded columns should not have a width set
            if not col.expand:
                col.width = props[1]

            # We didn't store sorted and order before
            if len(props) <= 2:
                continue

            col.sorted = props[2]
            col.order = props[3]

            pos = props[4]
            # If col references another column, the referenced column
            # should appear before this col
            if col.column:
                referenced_col = cols_dict[col.column][0]
                cols_dict[col.column] = (referenced_col, pos)
                cols_dict[attr] = (col, pos + 1)
                if col.sorted:
                    referenced_col.sorted, col.sorted = True, False
            else:
                cols_dict[attr] = (col, pos)

        cols.sort(key=lambda col: cols_dict[col.attribute][1])
        return cols

    def save_filter_settings(self, domain, restore_name):
        """
        Save filters to user settings

        :param domain: settings domain, like "app-ui"
        :param restore_name: name of the setting, like "admin"
        """
        if self._loading_filters:
            return
        filter_states = self.get_filter_states()
        domain_settings = api.user_settings.get(domain, {})
        settings = domain_settings.setdefault(restore_name, {})
        settings['filter-states'] = filter_states

    def restore_filter_settings(self, domain, restore_name):
        """
        Restore filters from user settings

        :param domain: settings domain, like "app-ui"
        :param restore_name: name of the setting, like "admin"
        """
        self._loading_filters = True
        domain_settings = api.user_settings.get(domain, {})
        settings = domain_settings.setdefault(restore_name, {})
        filter_states = settings.get('filter-states')
        if filter_states is not None:
            # Disable auto search to avoid an extra query when restoring the
            # state
            self.set_auto_search(False)
            self.set_filter_states(filter_states)
            self.set_auto_search(True)
        self._loading_filters = False

    def create_branch_filter(self, label=None, column=None):
        """Returns a new branch filter.

        :param label: The label to be used for the filter
        :param column: When provided, besides creating the filter, we will also
          add it to the interface, filtering by the informed column.
        """
        items = api.get_branches_for_filter(self.store, use_id=True)
        if not label:
            label = _('Branch:')

        if column and not isinstance(column, list):
            column = [column]

        branch_filter = ComboSearchFilter(label, items)
        current = api.get_current_branch(self.store)
        branch_filter.select(current.id)
        if column:
            self.add_filter(branch_filter, columns=column,
                            position=SearchFilterPosition.TOP)

        return branch_filter

    #
    #  Callbacks
    #

    def on_result_view__item_activated(self, result_view, item):
        self.emit('result-item-activated', item)

    def on_result_view__item_popup_menu(self, result_view, results, event):
        self.emit('result-item-popup-menu', results, event)

    def on_result_view__selection_changed(self, result_view, selected):
        self.emit('result-selection-changed')

    def on_search_button__clicked(self, button):
        self.search()

    def on_search_entry__activate(self, button):
        self.search()

    def _on_menu_item__activate(self, item, attr, title, data_type,
                                valid_values, callback, use_having,
                                multiple_selection):
        self.add_filter_by_attribute(attr, title, data_type, valid_values,
                                     callback, use_having, multiple_selection)

    def _on_search_filter__remove(self, filter):
        self.remove_filter(filter)

    def _on_search_filter__changed(self, search_filter):
        # The 'changed' event is emitted when someone presses Enter on the
        # entry. Since we already do a search when the entry is activated,
        # doing again when the primary filter is changed would result in doing
        # the same query twice.
        if search_filter == self._primary_filter:
            return
        if self._auto_search:
            self.search()
