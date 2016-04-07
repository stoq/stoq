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
""" Runtime routines for applications"""

from collections import namedtuple
import logging
import sys
import warnings
import weakref
import os

from kiwi.component import get_utility, provide_utility
from storm import Undef
from storm.expr import SQL, Avg
from storm.info import get_obj_info
from storm.store import Store, ResultSet
from storm.tracer import trace

from stoqlib.database.exceptions import InterfaceError, OperationalError
from stoqlib.database.interfaces import (
    ICurrentBranch,
    ICurrentBranchStation, ICurrentUser)
from stoqlib.database.expr import is_sql_identifier
from stoqlib.database.orm import ORMObject
from stoqlib.database.properties import Identifier
from stoqlib.database.settings import db_settings
from stoqlib.database.viewable import Viewable
from stoqlib.exceptions import DatabaseError, LoginError
from stoqlib.lib.decorators import public
from stoqlib.lib.interfaces import IAppInfo
from stoqlib.lib.message import error, yesno
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.net.socketutils import get_hostname

_ = stoqlib_gettext
log = logging.getLogger(__name__)

#: the default store, considered read-only in Stoq
_default_store = None

#: list of global stores used by the application,
#: should not be used by anything except autoreload_object()
_stores = weakref.WeakSet()


def autoreload_object(obj, obj_store=False):
    """Autoreload object in any other existing store.

    This will go through every open store and see if the object is alive in the
    store. If it is, it will be marked for autoreload the next time its used.

    :param obj_store: if we should also autoreload the current store
        of the object
    """
    for store in _stores:
        if not obj_store and Store.of(obj) is store:
            continue

        alive = store._alive.get((obj.__class__, (obj.id,)))
        if alive:
            # Just to make sure its not modified before reloading it, otherwise,
            # we would lose the changes
            assert not store._is_dirty(get_obj_info(obj))
            store.autoreload(alive)


class StoqlibResultSet(ResultSet):
    # FIXME: Remove. See bug 4985
    def __nonzero__(self):
        warnings.warn("use self.is_empty()", DeprecationWarning, stacklevel=2)
        return not self.is_empty()

    def avg(self, attribute):
        # ResultSet.avg() is not used because storm returns it as a float
        return self._aggregate(Avg, attribute)

    def set_viewable(self, viewable):
        """Configures this result set to load the results as instances of the
        given viewable.

        :param viewable: A :class:`Viewable  <stoqlib.database.viewable.Viewable>`
        """
        self._viewable = viewable

        # ResultSet needs this to create the query correctly
        self._tables = viewable.tables
        if viewable.group_by:
            self.group_by(*viewable.group_by)

    def _load_viewable(self, values):
        """Converts the result of this result set into an instance of the
        configured viewable.
        """
        instance = self._viewable()
        # This will be removed later
        instance._store = self._store
        identifiers = []
        for attr, value in zip(self._viewable.cls_attributes, values):
            if type(value) is Identifier:
                identifiers.append(value)
            setattr(instance, attr, value)
        branch = getattr(instance, 'branch', None)
        if branch:
            for i in identifiers:
                i.prefix = branch.acronym or ''
        return instance

    def _load_objects(self, result, values):
        # Overwrite the default _load_objects so we can convert the results to
        # viewable instances (if necessary)
        values = super(StoqlibResultSet, self)._load_objects(result, values)

        if hasattr(self, '_viewable'):
            values = self._load_viewable(values)

        return values

    def find(self, *args, **kwargs):
        # We only need this workaround if we are querying a viewable and the
        # viewable has a group_by
        workaround_needed = hasattr(self, '_viewable') and self._group_by is not Undef
        if workaround_needed:
            # Storm is not letting us call store.find(Viewable, args1).find(args2),
            # but it should be possible, since that the same as writing
            # store.find(Viewable, And(args1, args2))
            group_by = self._group_by[:]
            self._group_by = Undef
            resultset = super(StoqlibResultSet, self).find(*args, **kwargs)
            resultset._group_by = group_by
            self._group_by = group_by
            return resultset

        return super(StoqlibResultSet, self).find(*args, **kwargs)

    def _load_fast_object(self, named_tuples, values):
        objects = []
        values_start = values_end = 0
        for nt in named_tuples:
            if nt is None:
                # This means its an single expression
                values_end += 1
                objects.append(values[values_start])
            else:
                values_end += len(nt._fields)
                objects.append(nt(*values[values_start:values_end]))
            values_start = values_end

        if self._find_spec.is_tuple:
            return tuple(objects)
        else:
            return objects[0]

    def fast_iter(self):
        # First build all named tuples
        named_tuples = []
        for is_expr, info in self._find_spec._cls_spec_info:
            if is_expr:
                named_tuples.append(None)
            else:
                named_tuples.append(namedtuple(info.cls.__name__,
                                               [i.name for i in info.columns]))

        is_viewable = hasattr(self, '_viewable')
        # Then interate over the results bypassing storm object creation
        for values in self._store._connection.execute(self._get_select()):
            value = self._load_fast_object(named_tuples, values)
            if is_viewable:
                value = self._load_viewable(value)
            yield value


class StoqlibStore(Store):
    """The Stoqlib Store.

    This is the Stoqlib API to access a database.
    It represents more or less a database transaction, after modifying
    an object you need to either :meth:`.commit` or :meth:`.rollback`
    the store.

    The primary way of querying object from  a store is via the :meth:`.find`
    method, but you can also use :meth:`.Store.get` if you know the id
    of the object. find returns a ResultSet, see the Storm documentation for
    information about that.

    Objects needs to be added to a store. This can either be done via
    :meth:`StoqlibStore.add` or passing in the store parameter to a
    ORMObject/Domain object.

    If you want to delete an object you use :meth:`StoqlibStore.remove`

    You normally create a store using :func:`.new_store`, it needs to be
    :meth:`close` when you're done or a database connection will be leaked.

    See also:
    `storm manual <https://storm.canonical.com/Manual>`__
    `storm tutorial <https://storm.canonical.com/Tutorial>`__

    :attribute retval: The return value of a operation this transaction
      is covering. Usually a domain object that was modified. By default
      it's ``True``, but can be set to ``False`` to do a rollback instead
      of a commit on :meth:`stoqlib.api.StoqApi.trans`
    """

    _result_set_factory = StoqlibResultSet

    def __init__(self, database=None, cache=None):
        """
        Creates a new store

        :param database: the database to connect to or ``None``
        :param cache: storm cache to use or ``None``
        """
        self._committing = False
        self._savepoints = []
        self._pending_count = [0]
        self.retval = True
        self.obsolete = False

        if database is None:
            database = get_default_store().get_database()
        Store.__init__(self, database=database, cache=cache)
        _stores.add(self)
        trace('transaction_create', self)
        self._setup_application_name()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.committed = self.confirm(commit=self.retval)
            self.close()

    def _set_dirty(self, obj_info):
        # Store calls _set_dirty when any object inside it gets modified.
        # We use this to count if any change happened inside the actual savepoint
        self._pending_count[-1] += 1
        super(StoqlibStore, self)._set_dirty(obj_info)

    def find(self, cls_spec, *args, **kwargs):
        # Overwrite the default find method so we can support querying our own
        # viewables. If the cls_spec is a Viewable, we first get the real
        # cls_spec from the viewable and after the query is executed, the
        # results will be converted in instances of the viewable

        viewable = None
        if not isinstance(cls_spec, tuple):
            try:
                is_viewable = issubclass(cls_spec, Viewable)
            except TypeError:
                is_viewable = False

            if is_viewable:
                args = list(args)
                viewable = cls_spec
                # Get the actual class spec for the viewable
                cls_spec = viewable.cls_spec

                if viewable.clause:
                    args.append(viewable.clause)

        # kwargs are based on the properties of the viewable. We need to convert
        # it to the properties of the real tables.
        if viewable and kwargs:
            for key in kwargs.copy():
                args.append(getattr(viewable, key) == kwargs.pop(key))

        resultset = super(StoqlibStore, self).find(cls_spec, *args, **kwargs)

        if viewable:
            resultset.set_viewable(viewable)

        return resultset

    def get_lock_database_query(self):
        """
        Fetch a database query that needs to be executed to lock the database,
        suitable for applying migration patches.

        :returns: a database query in string form
        """
        res = self.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        tables = ', '.join([i[0] for i in res.get_all()])
        res.close()
        if not tables:
            return ''
        return 'LOCK TABLE %s IN ACCESS EXCLUSIVE MODE NOWAIT;' % tables

    def lock_database(self):
        """Tries to lock the database.

        Raises an DatabaseError if the locking has failed (ie, other clients are
        using the database).
        """
        try:
            # Locking requires a transaction to work, but this conection does
            # not begin one explicitly
            self.execute('BEGIN TRANSACTION')
            self.execute(self.get_lock_database_query())
        except OperationalError as e:
            raise DatabaseError("ERROR: Could not obtain lock: %s" % (e, ))

    def unlock_database(self):
        """Unlock a previously locked database."""
        self.execute('ROLLBACK')

    def table_exists(self, table_name):
        """Check if a table exists

        :param table_name: name of the table to check for
        :returns: ``True`` if the table exists
        """
        res = self.execute(
            SQL("SELECT COUNT(relname) FROM pg_class WHERE relname = ?",
                # FIXME: Figure out why this is not comming as unicode
                (unicode(table_name), )))
        return res.get_one()[0]

    def list_references(self, column):
        """Returns a list of columns that reference the givem column

        This will return a list of tuples (source table, source column,
        dest table, dest column, update, delete)

        where:

        - source table and column: The column that reference the given column
        - dest table and column: The referenced column (the same as the given
          column argument)
        - update : The ON UPDATE action for the reference. 'a' for 'NO ACTION', 'c'
          for CASCADE
        - delete: The same as update.
        """
        table_name = unicode(column.cls.__storm_table__)
        column_name = unicode(column.name)
        query = """
            SELECT DISTINCT
                src_pg_class.relname AS srctable,
                src_pg_attribute.attname AS srccol,
                ref_pg_class.relname AS reftable,
                ref_pg_attribute.attname AS refcol,
                pg_constraint.confupdtype,
                pg_constraint.confdeltype
            FROM pg_constraint
            JOIN pg_class AS src_pg_class
                ON src_pg_class.oid = pg_constraint.conrelid
            JOIN pg_class AS ref_pg_class
                ON ref_pg_class.oid = pg_constraint.confrelid
            JOIN pg_attribute AS src_pg_attribute
                ON src_pg_class.oid = src_pg_attribute.attrelid
            JOIN pg_attribute AS ref_pg_attribute
                ON ref_pg_class.oid = ref_pg_attribute.attrelid, generate_series(0,10) pos(n)
            WHERE
                contype = 'f'
                AND ref_pg_class.relname = ?
                AND ref_pg_attribute.attname = ?
                AND src_pg_attribute.attnum = pg_constraint.conkey[n]
                AND ref_pg_attribute.attnum = pg_constraint.confkey[n]
                AND NOT src_pg_attribute.attisdropped
                AND NOT ref_pg_attribute.attisdropped
            ORDER BY src_pg_class.relname, src_pg_attribute.attname
            """
        return self.execute(query, (table_name, column_name)).get_all()

    def quote_query(self, query, args=()):
        """Prepare a query for executing it.
        This is suitable for serializing a query to disk so we can pass
        it in to a database command line tool. It basically just escaped
        the arguments and generates a query that can be executed

        :param query: the database query, a string
        :param args: args that are to be escaped.
        :returns: database statement
        """
        cursor = self._connection.build_raw_cursor()
        # mogrify is only available in psycopg2
        stmt = cursor.mogrify(query, args)
        cursor.close()
        return stmt

    def maybe_remove(self, obj):
        """Maybe remove an object from the database

        This will depend on the parameter SYNCHRONIZED_MODE. When working with
        synchronized databases, we should be very carefull when removing
        objects, since they will not be removed from the remote database (at
        least until we fix bug 5581)
        """
        from stoqlib.lib.parameters import sysparam
        if not sysparam.get_bool('SYNCHRONIZED_MODE'):
            self.remove(obj)

    def get_pending_count(self):
        """Get the quantity of pending changes

        Every time :meth:`.add_created_object`, :meth:`.add_deleted_object`
        or :meth:`.add_modified_object` gets called, this will increase by 1.

        Note that this is in sync with savepoints so, if before doing a
        savepoint there was 10 pending changes, then 2 more are done, when
        rolling back to it it will be 10 again. The same applies to a full
        rollback where this will go to 0.
        """
        return sum(self._pending_count)

    @public(since="1.5.0")
    def commit(self, close=False):
        """Commits a database.
        This needs to be done to submit the actually inserts to the database.

        :param close: If ``True``, the store will also be closed after committed.
        """
        self._check_obsolete()
        self._committing = True

        # the cache will be cleared when commiting, so store them here
        # and autoreload them after commit
        touched_objs = []
        for obj_info in self._cache.get_cached():
            obj = obj_info.get_obj()
            if obj is not None:
                touched_objs.append(obj)

        super(StoqlibStore, self).commit()
        trace('transaction_commit', self)

        self._pending_count = [0]
        self._savepoints = []

        # Reload objects on all other opened stores
        for obj in touched_objs:
            autoreload_object(obj)

        if close:
            self.close()

        self._committing = False

    def flush(self):
        """Flush the transaction to the database

        This will transform all modifications done on domain objs in
        an sql command and execute them on the database. Note that this
        will execute the sql on the transaction, but only will be
        commited when :meth:`.commit` is called.
        """
        super(StoqlibStore, self).flush()

        # We only call 'before-commited' when flush is being called by commit
        if not self._committing:
            return

        for obj_info in self._cache.get_cached():
            obj_info.event.emit("before-commited")

        # If objs got dirty when calling the hooks, flush again
        if self._dirty:
            self.flush()

    @public(since="1.5.0")
    def rollback(self, name=None, close=True):
        """Rollback the transaction

        :param name: If supplied limit changes to the last savepoint
        :param close: If ``True``, the connection will also be closed and will not
          be available for use anymore. If False, only a rollback is done and
          it will still be possible to use it for other queries.
        """
        self._check_obsolete()

        if name:
            self.rollback_to_savepoint(name)
        else:
            super(StoqlibStore, self).rollback()
            # If we rollback completely, we need to clear all savepoints
            self._savepoints = []
            self._pending_count = [0]

        # Rolling back resets the application name.
        self._setup_application_name()

        # sqlobject closes the connection after a rollback
        if close:
            self.close()

    @public(since="1.5.0")
    def close(self):
        """Close the store.

        Closes the socket that represents that database connection, this needs to
        be called when you finished using the store.
        """
        trace('transaction_close', self)
        self._check_obsolete()

        super(StoqlibStore, self).close()
        self.obsolete = True

    @public(since="1.5.0")
    def fetch(self, obj):
        """Fetches an existing object in the context of this store.

        This is useful to 'move' an object from one store to another.

        :param obj: object to fetch
        :returns: the object in the context of this store
        """
        self._check_obsolete()

        if obj is None:
            return None

        if not isinstance(obj, ORMObject):
            raise TypeError("obj must be a ORMObject, not %r" % (obj, ))

        return self.get(type(obj), obj.id)

    def remove(self, obj):
        """Remove an objet from the store

        The associated row will be deleted from the database.
        """
        # Overwrite store.remove so we can emit our own event for when the
        # object is goin to be deleted (but before anything is actually modified)
        obj_info = get_obj_info(obj)
        obj_info.event.emit("before-removed")
        super(StoqlibStore, self).remove(obj)

    def savepoint(self, name):
        """Creates a database savepoint.
        This can be rolled back to using :meth:`.rollback_to_savepoint`.

        :param name: name of the savepoint
        """
        self._check_obsolete()

        if not is_sql_identifier(name):
            raise ValueError("Invalid savepoint name: %r" % name)
        self.execute('SAVEPOINT %s' % name)
        self._savepoints.append(name)
        self._pending_count.append(0)

    def rollback_to_savepoint(self, name):
        """Rollsback the store to a previous savepoint that was saved
        using :meth:`.savepoint`

        :param name: savepoint to move back to
        """
        self._check_obsolete()

        if not is_sql_identifier(name):
            raise ValueError("Invalid savepoint name: %r" % name)
        if not name in self._savepoints:
            raise ValueError("Unknown savepoint: %r" % name)

        self.execute('ROLLBACK TO SAVEPOINT %s' % name)
        for savepoint in reversed(self._savepoints[:]):
            self._savepoints.remove(savepoint)
            self._pending_count.pop()
            if savepoint == name:
                break

        # Objects may have changed in this transaction.
        # Make sure to autorelad the original values after the rollback
        for obj_info in self._cache.get_cached():
            self.autoreload(obj_info.get_obj())

    def savepoint_exists(self, name):
        """Checks if the given savepoint's name exists

        :param name: the name of the savepoint
        :returns: ``True`` if the savepoint exists on this store,
            ``False`` otherwise.
        """
        return name in self._savepoints

    def confirm(self, commit):
        """Encapsulated method for committing/aborting changes in models.

        :param commit: True for commit, False for rollback
        :returns: True if it was committed, False otherwise
        """

        # Allow False/None
        if commit:
            self.commit()
        else:
            self.rollback(close=False)

        return commit

    #
    #  Private
    #

    def _setup_application_name(self):
        """Sets a friendly name for postgres connection

        This name will appear when selecting from pg_stat_activity, for instance,
        and will allow to better debug the queries (specially when there is a deadlock)
        """
        try:
            appinfo = get_utility(IAppInfo)
        except Exception:
            appname = 'stoq'
        else:
            appname = appinfo.get('name') or 'stoq'

        self.execute("SET application_name = '%s - %s - %s'" % (
            (appname.lower(), get_hostname(), os.getpid())))

    def _check_obsolete(self):
        if self.obsolete:
            raise InterfaceError("This transaction has already been closed")


def get_default_store():
    """This function returns the default/primary store.
    Notice that this store is considered read-only inside Stoqlib
    applications. Only transactions can modify objects and should be
    created using new_store().
    This store should not be closed, it will only close when we the
    application is shutdown.

    :returns: default store
    """
    if _default_store is None:
        set_default_store(db_settings.create_store())
        # We intentionally leave this open, it's the default
        # store and should only be closed when we close the
        # application
    return _default_store


def set_default_store(store):
    """This sets a new default store and closes the
    existing one if any.

    This is only called during Startup and should not be used elsewhere
    :param store: the new store to set
    """

    global _default_store
    if store is None and _default_store is not None:
        _default_store.close()
    _default_store = store


def new_store():
    """
    Create a new transaction.
    :returns: a transaction
    """
    log.debug('Creating a new transaction in %s()'
              % sys._getframe(1).f_code.co_name)

    return StoqlibStore()


#
# User methods
#
def _register_branch_station(caller_store, station_name):
    import gtk
    from stoqlib.lib.parameters import sysparam

    if not sysparam.get_bool('DEMO_MODE'):
        fmt = _(u"The computer '%s' is not registered to the Stoq "
                u"server at %s.\n\n"
                u"Do you want to register it "
                u"(requires administrator access) ?")
        if not yesno(fmt % (station_name,
                            db_settings.address),
                     gtk.RESPONSE_YES, _(u"Register computer"), _(u"Quit")):
            raise SystemExit

        from stoqlib.gui.utils.login import LoginHelper
        h = LoginHelper(username="admin")
        try:
            user = h.validate_user()
        except LoginError as e:
            error(str(e))

        if not user:
            error(_("Must login as 'admin'"))

    from stoqlib.domain.station import BranchStation
    with new_store() as store:
        branch = sysparam.get_object(store, 'MAIN_COMPANY')
        station = BranchStation.create(store, branch=branch, name=station_name)
    return caller_store.fetch(station)


def set_current_branch_station(store, station_name):
    """Registers the current station and the branch of the station
    as the current branch for the system
    :param store: a store
    :param station_name: name of the station to register
    """
    # This is called from stoq-daemon, which doesn't know about Branch yet
    from stoqlib.lib.parameters import sysparam
    from stoqlib.domain.person import Branch
    Branch  # pylint: disable=W0104

    if station_name is None:
        station_name = get_hostname()

    station_name = unicode(station_name)
    from stoqlib.domain.station import BranchStation
    station = store.find(BranchStation, name=station_name).one()
    if station is None:
        station = _register_branch_station(store, station_name)

    if not station.is_active:
        error(_("The computer <u>%s</u> is not active in Stoq") %
              station_name,
              _("To solve this, open the administrator application "
                "and re-activate this computer."))

    provide_utility(ICurrentBranchStation, station, replace=True)

    main_company = sysparam.get_object(store, 'MAIN_COMPANY')
    if not station.branch and main_company:
        with new_store() as commit_store:
            commit_station = commit_store.fetch(station)
            commit_station.branch = commit_store.fetch(main_company)

    # The station may still not be associated with a branch when creating an
    # empty database
    if station.branch:
        provide_utility(ICurrentBranch, station.branch, replace=True)


@public(since="1.5.0")
def get_current_user(store):
    """Fetch the user which is currently logged into the system or None
    None means that there are no utilities available which in turn
    should only happens during startup, for example when creating
    a new database or running the migration script,
    at that point no users are logged in

    :param store: a store
    :returns: currently logged in user or None
    :rtype: a LoginUser or ``None``
    """
    user = get_utility(ICurrentUser, None)
    if user is not None:
        return store.fetch(user)


@public(since="1.5.0")
def get_current_branch(store):
    """Fetches the current branch company.

    :param store: a store
    :returns: the current branch
    :rtype: a branch or ``None``
    """

    branch = get_utility(ICurrentBranch, None)
    if branch is not None:
        return store.fetch(branch)


@public(since="1.5.0")
def get_current_station(store):
    """Fetches the current station (computer) which we are running on

    :param store: a store
    :param: current station
    :rtype: BranchStation or ``None``
    """
    station = get_utility(ICurrentBranchStation, None)
    if station is not None:
        return store.fetch(station)
