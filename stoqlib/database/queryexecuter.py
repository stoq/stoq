# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2013 Async Open Source <http://www.async.com.br>
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

"""
Kiwi integration for Stoq/Storm
"""

from kiwi.db.query import NumberQueryState, StringQueryState, \
    DateQueryState, DateIntervalQueryState, QueryExecuter, \
    NumberIntervalQueryState, BoolQueryState
from kiwi.interfaces import ISearchFilter
from kiwi.python import Settable
from storm import Undef
from storm.expr import And, Or, Like, Not, Alias

from stoqlib.database.expr import Date
from stoqlib.database.viewable import Viewable


class StoqlibQueryExecuter(QueryExecuter):
    """Execute queries from a storm database"""

    def __init__(self, store=None):
        QueryExecuter.__init__(self)
        self.store = store
        self.table = None
        self._query_callbacks = []
        self._filter_query_callbacks = {}
        self._query = self._default_query
        self.post_result = None

    def search(self, states):
        """
        Execute a search.
        :param states:
        """
        if self.table is None:
            raise ValueError("table cannot be None")
        table = self.table
        queries = []
        having = []
        for state in states:
            search_filter = state.filter
            assert state.filter

            # Column query
            if search_filter in self._columns:
                columns, use_having = self._columns[search_filter]
                query = self._construct_state_query(table, state, columns)
                if query and use_having:
                    having.append(query)
                elif query:
                    queries.append(query)
            # Custom per filter/state query.
            elif search_filter in self._filter_query_callbacks:
                for callback, use_having in self._filter_query_callbacks[search_filter]:
                    query = callback(state)
                    if query and use_having:
                        having.append(query)
                    elif query:
                        queries.append(query)
            else:
                if (self._query == self._default_query and
                    not self._query_callbacks):
                    raise ValueError(
                        "You need to add a search column or a query callback "
                        "for filter %s" % (search_filter))

        for callback in self._query_callbacks:
            query = callback(states)
            if query:
                queries.append(query)

        result = self._query(self.store)
        if queries:
            result = result.find(And(*queries))
        if having:
            result = result.having(And(*having))

        return result

    def set_table(self, table):
        """
        Sets the Storm table/object for this executer
        :param table: a Storm table class
        """
        self.table = table

    def add_query_callback(self, callback):
        """
        Adds a generic query callback

        :param callback: a callable
        """
        if not callable(callback):
            raise TypeError
        self._query_callbacks.append(callback)

    def add_filter_query_callback(self, search_filter, callback,
                                  use_having=False):
        """
        Adds a query callback for the filter search_filter

        :param search_filter: a search filter
        :param callback: a callable
        """
        if not ISearchFilter.providedBy(search_filter):
            raise TypeError
        if not callable(callback):
            raise TypeError
        l = self._filter_query_callbacks.setdefault(search_filter, [])
        l.append((callback, use_having))

    def set_query(self, callback):
        """
        Overrides the default query mechanism.
        :param callback: a callable which till take two arguments:
          (query, store)
        """
        if callback is None:
            callback = self._default_query
        elif not callable(callback):
            raise TypeError

        self._query = callback

    def get_post_result(self, result):
        descs, query = self.table.post_search_callback(result)
        # This should not be present in the query, since post_search_callback
        # should only use aggregate functions.
        query.order_by = Undef
        query.group_by = Undef
        store = self.store
        values = store.execute(query).get_one()
        assert len(descs) == len(values), (descs, values)
        data = {}
        for desc, value in zip(descs, list(values)):
            data[desc] = value
        return Settable(**data)

    def get_ordered_result(self, result, attribute):
        if issubclass(self.table, Viewable):
            # sorting viewables is not supported with strings, since that
            # viewables can query more than one table at once, and each
            # table may have columns with the same name.
            if isinstance(attribute, str):
                attribute = getattr(self.table, attribute)

        return result.order_by(attribute)

    def _default_query(self, store):
        return store.find(self.table)

    def _construct_state_query(self, table, state, columns):
        queries = []
        for column in columns:
            query = None
            if isinstance(column, str):
                table_field = getattr(table, column)
            else:
                table_field = column

            if isinstance(table_field, Alias):
                table_field = table_field.expr

            if isinstance(state, NumberQueryState):
                query = self._parse_number_state(state, table_field)
            elif isinstance(state, NumberIntervalQueryState):
                query = self._parse_number_interval_state(state, table_field)
            elif isinstance(state, StringQueryState):
                query = self._parse_string_state(state, table_field)
            elif isinstance(state, DateQueryState):
                query = self._parse_date_state(state, table_field)
            elif isinstance(state, DateIntervalQueryState):
                query = self._parse_date_interval_state(state, table_field)
            elif isinstance(state, BoolQueryState):
                query = self._parse_bool_state(state, table_field)
            else:
                raise NotImplementedError(state.__class__.__name__)
            if query:
                queries.append(query)
        if queries:
            return Or(*queries)

    def _parse_number_state(self, state, table_field):
        if state.value is not None:
            return table_field == state.value

    def _parse_number_interval_state(self, state, table_field):
        queries = []
        if state.start:
            queries.append(table_field >= state.start)
        if state.end:
            queries.append(table_field <= state.end)
        if queries:
            return And(*queries)

    def _parse_string_state(self, state, table_field):
        if not state.text:
            return
        text = u'%%%s%%' % state.text.lower()
        retval = Like(table_field, text, case_sensitive=False)
        if state.mode == StringQueryState.NOT_CONTAINS:
            retval = Not(retval)

        return retval

    def _parse_date_state(self, state, table_field):
        if state.date:
            return Date(table_field) == Date(state.date)

    def _parse_date_interval_state(self, state, table_field):
        queries = []
        if state.start:
            queries.append(Date(table_field) >= Date(state.start))
        if state.end:
            queries.append(Date(table_field) <= Date(state.end))
        if queries:
            return And(*queries)

    def _parse_bool_state(self, state, table_field):
        return table_field == state.value
