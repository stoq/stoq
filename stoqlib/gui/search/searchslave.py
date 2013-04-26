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

import logging
import os

from kiwi.ui.delegates import SlaveDelegate
from kiwi.utils import gsignal

from stoqlib.api import api
from stoqlib.enums import SearchFilterPosition
from stoqlib.gui.search.searchcontainer import SearchContainer
from stoqlib.lib.osutils import get_application_dir
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

log = logging.getLogger(__name__)


# TODO:
# * Rename to SearchSlave
# * Always create a QueryExecutor in here
# * Move everything for SearchContainer and put it in here
#   * Will avoid search.search madness
#   * Will reduce connect/emit abstraction madness
#   * Will simplify callsites
# * Improve SearchResultView selection API
# * Simplify all call sites, esp application.py

class SearchSlaveDelegate(SlaveDelegate):
    gsignal("result-item-activated", object)
    gsignal("result-item-popup-menu", object, object)
    gsignal("result-selection-changed")

    def __init__(self, columns, tree=False, restore_name=None):
        """
        Create a new SearchSlaveDelegate object.
        :param results: the results list of the container
        :param search: the :class:`SearchContainer`
        :param restore_name:
        """

        self._restore_name = restore_name
        self._settings_key = 'search-columns-%s' % (
            api.get_current_user(api.get_default_store()).username, )
        self._columns = self.restore_columns(columns)

        self.search = SearchContainer(columns, tree=tree)
        SlaveDelegate.__init__(self, toplevel=self.search)
        self.results = self.search.result_view
        self.search.show()
        self.search.connect("search-completed",
                            self._on_search__search_completed)
        self.search.connect("item-activated",
                            self._on_search__item_activated)
        self.search.connect("item-popup-menu",
                            self._on_search__item_popup_menu)
        self.search.connect("selection-changed",
                            self._on_search__selection_changed)

    #
    # Public API
    #

    def add_filter(self, search_filter, position=SearchFilterPosition.BOTTOM,
                   columns=None, callback=None, use_having=False):
        """
        See :class:`SearchSlaveDelegate.add_filter`
        """
        self.search.add_filter(search_filter, position, columns=columns,
                               callback=callback, use_having=use_having)

    def set_query_executer(self, querty_executer):
        """
        See :class:`SearchSlaveDelegate.set_query_executer`
        """
        self.search.set_query_executer(querty_executer)

    def set_text_field_columns(self, columns):
        """
        See :class:`SearchSlaveDelegate.set_text_field_columns`
        """
        self.search.set_text_field_columns(columns)

    def get_primary_filter(self):
        """
        Fetches the primary filter of the SearchSlaveDelegate
        :returns: primary filter
        """
        return self.search.get_primary_filter()

    def focus_search_entry(self):
        """
        Grabs the focus of the search entry
        """
        self.search.search_entry.grab_focus()

    def refresh(self):
        """
        Triggers a search again with the currently selected inputs
        """
        self.search.search()

    def clear(self):
        """
        Clears the result list
        """
        self.search.result_view.clear()

    def disable_search_entry(self):
        """
        Disables the search entry
        """
        self.search.disable_search_entry()

    def set_summary_label(self, column, label='Total:', format='%s',
                          parent=None):
        """
        See :class:`SearchContainer.set_summary_label`
        """
        self.search.set_summary_label(column, label, format, parent)

    def enable_advanced_search(self):
        """
        See :class:`SearchContainer.enable_advanced_search`
        """
        self.search.enable_advanced_search()

    def get_search_filters(self):
        return self.search.get_search_filters()

    def save_columns(self):
        if not self._restore_name:
            return

        d = self.search.result_view.get_settings()
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

    def set_message(self, message):
        self.search.result_view.set_message(message)

    def get_column_by_attribute(self, attribute):
        """Returns a column by its model attribute."""
        for column in self._columns:
            if column.attribute == attribute:
                return column

    def select(self, item):
        self.search.result_view.select(item)

    def get_selected_item(self):
        return self.search.result_view.get_selected_item()

    #
    #  Private
    #

    def _migrate_from_pickle(self):
        username = api.get_current_user(api.get_default_store()).username
        filename = os.path.join(get_application_dir(), 'columns-%s' % username,
                                self._restore_name + '.pickle')
        log.info("Migrating columns from pickle: %s" % (filename, ))
        try:
            with open(filename) as fd:
                import cPickle
                return cPickle.load(fd)
        except Exception as e:
            log.info("Exception while migrating: %r" % (e, ))
            return {}

    #
    #  Callbacks
    #

    def _on_search__search_completed(self, search, results, states):
        if not len(results):
            self.set_message(_("Nothing found."))

    def _on_search__item_activated(self, search, item):
        self.emit('result-item-activated', item)

    def _on_search__item_popup_menu(self, search, results, event):
        self.emit('result-item-popup-menu', results, event)

    def _on_search__selection_changed(self, search):
        self.emit('result-selection-changed')

    #
    # Overridable
    #

    def get_columns(self):
        """
        This needs to be implemented in a subclass
        :returns: columns
        :rtype: list of :class:`kiwi.ui.objectlist.Column`
        """
        raise NotImplementedError
