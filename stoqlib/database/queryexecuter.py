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

from kiwi.python import Settable
from storm import Undef
from storm.expr import And, Or, Like, Not, Alias

from stoqlib.database.expr import Date
from stoqlib.database.viewable import Viewable
from stoqlib.database.interfaces import ISearchFilter


class QueryState(object):
    def __init__(self, search_filter):
        """
        Create a new QueryState object.
        :param search_filter: search filter this query state is associated with
        :type search_filter: :class:`SearchFilter`
        """
        self.filter = search_filter


class NumberQueryState(QueryState):
    """
    Create a new NumberQueryState object.
    :cvar value: number
    """
    def __init__(self, filter, value):
        QueryState.__init__(self, filter)
        self.value = value

    def __repr__(self):
        return '<NumberQueryState value=%r>' % (self.value,)


class NumberIntervalQueryState(QueryState):
    """
    Create a new NumberIntervalQueryState object.
    :cvar start: number
    :cvar end: number
    """
    def __init__(self, filter, start, end):
        QueryState.__init__(self, filter)
        self.start = start
        self.end = end

    def __repr__(self):
        return '<NumberIntervalQueryState start=%r end=%r>' % (self.start, self.end)


class StringQueryState(QueryState):
    """
    Create a new StringQueryState object.
    :cvar text: string
    """
    (CONTAINS,
     NOT_CONTAINS) = range(2)

    def __init__(self, filter, text, mode=CONTAINS):
        QueryState.__init__(self, filter)
        self.mode = mode
        self.text = text

    def __repr__(self):
        return '<StringQueryState text=%r>' % (self.text,)


class DateQueryState(QueryState):
    """
    Create a new DateQueryState object.
    :cvar date: date
    """
    def __init__(self, filter, date):
        QueryState.__init__(self, filter)
        self.date = date

    def __repr__(self):
        return '<DateQueryState date=%r>' % (self.date,)


class DateIntervalQueryState(QueryState):
    """
    Create a new DateIntervalQueryState object.
    :cvar start: start of interval
    :cvar end: end of interval
    """
    def __init__(self, filter, start, end):
        QueryState.__init__(self, filter)
        self.start = start
        self.end = end

    def __repr__(self):
        return '<DateIntervalQueryState start=%r, end=%r>' % (
            self.start, self.end)


class BoolQueryState(QueryState):
    """
    Create a new BoolQueryState object.
    :cvar value: value of the query state
    """
    def __init__(self, filter, value):
        QueryState.__init__(self, filter)
        self.value = value

    def __repr__(self):
        return '<BoolQueryState value=%r>' % (self.value)


class QueryExecuter(object):
    """
    A QueryExecuter is responsible for taking the state (as in QueryState)
    objects from search filters and construct a query.
    How the query is constructed is ORM/DB-layer dependent.

    :cvar default_search_limit: The default search limit.
    """

    def __init__(self, store=None):
        self._columns = {}
        self._limit = -1
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

    def set_limit(self, limit):
        """
        Set the maximum number of result items to return in a search query.
        :param limit:
        """
        self._limit = limit

    def get_limit(self):
        return self._limit

    def set_filter_columns(self, search_filter, columns, use_having=False):
        """Set what columns should be filtered for the search_filter

        :param columns: Should be a list of column names or properties to be
          used in the query. If they are column names (strings), we will call
          getattr on the table to get the property for the query construction.
        """
        if not ISearchFilter.providedBy(search_filter):
            pass
            #raise TypeError("search_filter must implement ISearchFilter")

        assert not search_filter in self._columns
        self._columns[search_filter] = (columns, use_having)

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
