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

import re
import threading
import Queue

import glib
import gobject
from kiwi.python import Settable
from kiwi.utils import gsignal
from storm import Undef
from storm.database import Connection, convert_param_marks
from storm.expr import compile, And, Or, Like, Not, Alias, State, Lower
from storm.tracer import trace
import psycopg2
import psycopg2.extensions

from stoqlib.database.expr import Date, StoqNormalizeString
from stoqlib.database.interfaces import ISearchFilter
from stoqlib.database.settings import db_settings
from stoqlib.database.viewable import Viewable


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
    (EQUALS,
     DIFFERENT) = range(2)

    def __init__(self, filter, value, mode=EQUALS):
        QueryState.__init__(self, filter)
        self.mode = mode
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
    (CONTAINS_EXACTLY,
     IDENTICAL_TO,
     NOT_CONTAINS,
     CONTAINS_ALL) = range(4)

    def __init__(self, filter, text, mode=CONTAINS_ALL):
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


class MultiQueryState(QueryState):
    """Query state for objects."""

    def __init__(self, filter, values):
        super(MultiQueryState, self).__init__(filter)
        self.values = values

    def __repr__(self):
        return '<MultiQueryState values=%r>' % (self.values, )


class AsyncResultSet(object):
    """Resultset returned by :class:`AsyncQueryOperation`.

    This should perform exactly like a
    :class:`stoqlib.database.runtime.StoqlibResultSet`. Some methods
    that are not defined here will be forwarded to it.

    The original resultset can be accessed by :attr:`.resultset`
    """

    def __init__(self, resultset, result):
        """
        :param resultset: the original
            :class:stoqlib.database.runtime.StoqlibResultset`. It will
            be used mostly to help constructing the objects on iteration
        :param result: the :class:`storm.database.Result` queried by
            the query operation
        """
        self.resultset = resultset
        self._result = result

    def __iter__(self):
        for values in self._result:
            yield self.resultset._load_objects(self._result, values)

    def __len__(self):
        return self._result.rowcount

    def __getattr__(self, attr):
        return getattr(self.resultset, attr)


class AsyncQueryOperation(gobject.GObject):

    (STATUS_WAITING,
     STATUS_EXECUTING,
     STATUS_FINISHED,
     STATUS_CANCELLED) = range(4)

    gsignal('finish')

    def __init__(self, store, resultset, expr):
        """
        :param store: database store
        :param resultset: resultset that will be used to construct
           the result from.
        :param expr: query expression to execute
        """
        gobject.GObject.__init__(self)

        self.status = self.STATUS_WAITING
        self.resultset = resultset
        self.expr = expr

        self._conn = store._connection
        self._async_cursor = None
        self._async_conn = None
        self._statement = None
        self._parameters = None

    #
    #  Public API
    #

    def execute(self, async_conn):
        """Executes a query within an asyncronous psycopg2 connection
        """
        if self.status == self.STATUS_CANCELLED:
            return

        self.status = self.STATUS_EXECUTING

        # Async variant of Connection.execute() in storm/database.py
        state = State()
        statement = compile(self.expr, state)
        stmt = convert_param_marks(statement, "?", "%s")
        self._async_cursor = async_conn.cursor()
        self._async_conn = async_conn

        # This is postgres specific, see storm/databases/postgres.py
        self._statement = stmt.encode('utf-8')
        self._parameters = tuple(Connection.to_database(state.parameters))

        trace("connection_raw_execute", self._conn,
              self._async_cursor, self._statement, self._parameters)
        self._async_cursor.execute(self._statement,
                                   self._parameters)

        # This can happen if another thread cancelled this while the cursor was
        # executing. In that case, it is not interested in the retval anymore
        if self.status == self.STATUS_CANCELLED:
            return

        self.status = self.STATUS_FINISHED
        glib.idle_add(self._on_finish)

    def get_result(self):
        """Get operation result.

        Note that this can only be called when the *finish* signal
        has been emitted.

        :returns: a :class:`AsyncResultSet` containing the result
        """
        assert self.status == self.STATUS_FINISHED

        trace("connection_raw_execute_success", self._conn,
              self._async_cursor, self._statement, self._parameters)

        result = self._conn.result_factory(self._conn,
                                           self._async_cursor)
        return AsyncResultSet(self.resultset, result)

    def cancel(self):
        """Cancel the operation scheduling"""
        self.status = self.STATUS_CANCELLED

    #
    #  Private
    #

    def _on_finish(self):
        if self.status == self.STATUS_CANCELLED:
            return
        self.emit('finish')

gobject.type_register(AsyncQueryOperation)


class _OperationExecuter(threading.Thread):

    _SINGLETON = None

    def __init__(self):
        super(_OperationExecuter, self).__init__()

        self._conn = psycopg2.connect(db_settings.get_store_dsn())
        self._queue = Queue.Queue()

    @classmethod
    def get_instance(cls):
        if cls._SINGLETON is None:
            cls._SINGLETON = cls()
            cls._SINGLETON.daemon = True
            cls._SINGLETON.start()
        return cls._SINGLETON

    def run(self):
        while True:
            operation = self._queue.get()
            operation.execute(self._conn)
            self._queue.task_done()

    def schedule(self, operation):
        assert isinstance(operation, AsyncQueryOperation)
        self._queue.put(operation)


class QueryExecuter(object):
    """
    A QueryExecuter is responsible for taking the state (as in QueryState)
    objects from search filters and construct a query.
    The query is constructed using storm.

    :cvar default_search_limit: The default search limit.
    """

    def __init__(self, store=None):
        self._columns = {}
        self._limit = -1
        self.store = store
        self.search_spec = None
        self._query_callbacks = []
        self._filter_query_callbacks = {}
        self._query = self._default_query
        self.post_result = None
        self._operation_executer = _OperationExecuter.get_instance()

    # Public API

    def search(self, states=None, resultset=None, limit=None):
        """
        Execute a search.

        :param resultset: resultset to use, if ``None`` we will
          just execute a normal store.find() on the search_spec set in
          .set_search_spec()
        :param states:
        :param limit: use this limit instead of the one defined by set_limit()
        """
        if resultset is None:
            resultset = self._query(self.store)
        resultset = self._parse_states(resultset, states)
        limit = limit or self._limit
        if limit > 0:
            resultset.config(limit=limit)
        return resultset

    def search_async(self, states=None, resultset=None, limit=None):
        """
        Execute a search asynchronously.
        This uses a separate psycopg2 connection which is lazily
        created just before executing the first async query.
        This method returns an operation for which a signal **finish** is
        emitted when the query has finished executing. In that callback,
        :meth:`.AsyncQueryOperation.finish` should be called, eg:

        >>> from stoqlib.api import api
        >>> from stoqlib.domain.person import Person

        >>> default_store = api.get_default_store()
        >>> resultset = default_store.find(Person)

        >>> qe = QueryExecuter(store=default_store)
        >>> operation = qe.search_async(resultset=resultset)

        >>> def finished(operation, loop):
        ...     operation.get_result()
        ...     # use result
        ...     loop.quit()

        Create a loop for testing

        >>> loop = glib.MainLoop()
        >>> sig_id = operation.connect('finish', finished, loop)
        >>> loop.run()

        :param states:
        :param resultset: a resultset or ``None``
        :returns: a query operation
        """
        if resultset is None:
            resultset = self._query(self.store)
        resultset = self._parse_states(resultset, states)
        limit = limit or self._limit
        if limit > 0:
            resultset.config(limit=limit)
        operation = AsyncQueryOperation(self.store,
                                        resultset,
                                        resultset._get_select())
        self._operation_executer.schedule(operation)
        return operation

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
          getattr on the search_spec to get the property for the query construction.
        """
        if not ISearchFilter.providedBy(search_filter):
            pass
            #raise TypeError("search_filter must implement ISearchFilter")

        assert not search_filter in self._columns
        self._columns[search_filter] = (columns, use_having)

    def set_search_spec(self, search_spec):
        """
        Sets the Storm search_spec for this executer

        :param search_spec: a Storm search_spec
        """
        self.search_spec = search_spec

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

        :param callback: a callable which till take two arguments (query, store)
        """
        if callback is None:
            callback = self._default_query
        elif not callable(callback):
            raise TypeError

        self._query = callback

    def get_post_result(self, result):
        descs, query = self.search_spec.post_search_callback(result)
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
        if issubclass(self.search_spec, Viewable):
            # sorting viewables is not supported with strings, since that
            # viewables can query more than one search_spec at once, and each
            # search_spec may have columns with the same name.
            if isinstance(attribute, str):
                attribute = getattr(self.search_spec, attribute)

        return result.order_by(attribute)

    # Private API

    def _default_query(self, store):
        return store.find(self.search_spec)

    def parse_states(self, states):
        """Parses the state given and return a tuple where the first element is
        the queries that should be used, and the second is a 'having' that
        should be used with the query.
        """
        if states is None:
            return None, None

        search_spec = self.search_spec
        if search_spec is None:
            raise ValueError("search_spec cannot be None")

        queries = []
        having = []
        for state in states:
            search_filter = state.filter
            assert state.filter

            # Column query
            if search_filter in self._columns:
                columns, use_having = self._columns[search_filter]
                query = self._construct_state_query(search_spec, state, columns)
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

        return queries, having

    def _parse_states(self, resultset, states):
        queries, having = self.parse_states(states)
        if queries:
            resultset = resultset.find(And(*queries))
        if having:
            resultset = resultset.having(And(*having))

        return resultset

    def _construct_state_query(self, search_spec, state, columns):
        queries = []
        for column in columns:
            query = None
            if isinstance(column, str):
                table_field = getattr(search_spec, column)
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
            elif isinstance(state, MultiQueryState):
                query = self._parse_multi_query_state(state, table_field)
            else:
                raise NotImplementedError(state.__class__.__name__)
            if query:
                queries.append(query)
        if queries:
            return Or(*queries)

    def _parse_number_state(self, state, table_field):
        if state.value is None:
            return

        if state.mode == NumberQueryState.EQUALS:
            return table_field == state.value
        elif state.mode == NumberQueryState.DIFFERENT:
            return table_field != state.value
        else:
            raise AssertionError

    def _parse_number_interval_state(self, state, table_field):
        queries = []
        if state.start:
            queries.append(table_field >= state.start)
        if state.end:
            queries.append(table_field <= state.end)
        if queries:
            return And(*queries)

    def _parse_string_state(self, state, table_field):
        if not state.text.strip():
            return

        def _like(value):
            return Like(StoqNormalizeString(table_field),
                        StoqNormalizeString(u'%%%s%%' % value.lower()),
                        case_sensitive=False)

        if state.mode == StringQueryState.CONTAINS_ALL:
            queries = [_like(word) for word in re.split('[ \n\r]', state.text) if word]
            retval = And(*queries)
        elif state.mode == StringQueryState.IDENTICAL_TO:
            retval = Lower(table_field) == state.text.lower()
        elif state.mode == StringQueryState.CONTAINS_EXACTLY:
            retval = (_like(state.text.lower()))
        elif state.mode == StringQueryState.NOT_CONTAINS:
            queries = [Not(_like(word)) for word in state.text.split(' ') if word]
            retval = And(*queries)
        else:  # pragma nocoverage
            raise AssertionError

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

    def _parse_multi_query_state(self, state, table_field):
        return table_field.is_in(state.values)
