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

import os
import socket
import sys
import warnings
import weakref

from kiwi.component import get_utility, provide_utility, implements
from kiwi.log import Logger
from psycopg2 import OperationalError
from storm.expr import SQL, Avg
from storm.info import get_obj_info
from storm.store import Store, ResultSet
from storm.tracer import trace

from stoqlib.database.exceptions import InterfaceError
from stoqlib.database.interfaces import (
    ITransaction, ICurrentBranch,
    ICurrentBranchStation, ICurrentUser)
from stoqlib.database.orm import ORMObject
from stoqlib.database.orm import sqlIdentifier, const
from stoqlib.database.settings import db_settings
from stoqlib.exceptions import DatabaseError, LoginError, StoqlibError
from stoqlib.lib.decorators import public
from stoqlib.lib.message import error, yesno
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext
log = Logger('stoqlib.runtime')

#: the default store, considered read-only in Stoq
_default_store = None

#: list of global stores used by the application,
#: should not be used by anything except autoreload_object()
_stores = weakref.WeakSet()


def autoreload_object(obj):
    """Autoreload object in any other existing store.

    This will go through every open store and see if the object is alive in the
    store. If it is, it will be marked for autoreload the next time its used.
    """
    for store in _stores:
        if Store.of(obj) is store:
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


class StoqlibStore(Store):
    """The Stoqlib Store.

    This is the Stoqlib API to access a database.
    It represents more or less a database transaction, after modifying
    an object you need to either :meth:`.commit` or :meth:`.rollback`
    the store.

    The primary way of querying object from  a store is via the :meth:`.find`
    method, but you can also use :meth:`.get` if you know the id of the object.
    find returns a ResultSet, see the Storm documentation for information
    about that.

    Objects needs to be added to a store. This can either be done via
    :meth:`.add` or passing in the store parameter to a ORMObject/Domain object.

    If you want to delete an object you use :meth:`.remove`

    You normally create a store using :func:`.new_store`, it needs to be
    :meth:`close` when you're done or a database connection will be leaked.

    See also:
    `storm manual <https://storm.canonical.com/Manual>`__
    `storm tutorial <https://storm.canonical.com/Tutorial>`__

    :attribute retval: The return value of a operation this transaction
      is covering. Usually a domain object that was modified
    :attribute needs_retval: If this is set to True, the retval variable
      needs to be set to a non-zero value to be committed, see
      stoqlib.api.trans
    """
    implements(ITransaction)
    _result_set_factory = StoqlibResultSet

    def __init__(self, database=None, cache=None):
        """
        Creates a new store

        :param database: the database to connect to or ``None``
        :param cache: storm cache to use or ``None``
        """
        self._savepoints = []
        self.retval = None
        self.needs_retval = False
        self.obsolete = False

        if database is None:
            database = get_default_store().get_database()
        Store.__init__(self, database=database, cache=cache)
        _stores.add(self)
        trace('transaction_create', self)
        self._reset_pending_objs()

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
        except OperationalError:
            raise DatabaseError("Could not obtain lock")

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

    #
    #  ITransaction implementation
    #

    def add_created_object(self, obj):
        """Record an object that was created in the store.
        This is an internal method that should only be called by Domain.

        :param obj: the object that was created, a Domain subclass
        """
        obj_set = self._created_object_sets[-1]
        obj_set.add(obj)

    def add_modified_object(self, obj):
        """Record an object that was modified in the store.
        This is an internal method that should only be called by Domain.

        :param obj: the object that was created, a Domain subclass
        """
        obj_set = self._modified_object_sets[-1]
        obj_set.add(obj)

    def add_deleted_object(self, obj):
        """Record an object that was deleted from the store.
        This is an internal method that should only be called by Domain.

        :param obj: the object that was created, a Domain subclass
        """
        obj_set = self._deleted_object_sets[-1]
        obj_set.add(obj)

    @public(since="1.5.0")
    def commit(self, close=False):
        """Commits a database.
        This needs to be done to submit the actually inserts to the database.

        :param close: If ``True``, the store will also be closed after committed.
        """
        self._check_obsolete()
        self._process_pending_objs()

        super(StoqlibStore, self).commit()
        trace('transaction_commit', self)
        if close:
            self.close()

    @public(since="1.5.0")
    def rollback(self, name=None, close=True):
        """Rollback the transaction

        :param close: If ``True``, the connection will also be closed and will not
          be available for use anymore. If False, only a rollback is done and
          it will still be possible to use it for other queries.
        """
        self._check_obsolete()

        if name:
            self.rollback_to_savepoint(name)
        else:
            super(StoqlibStore, self).rollback()
            self._reset_pending_objs()

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

    def savepoint(self, name):
        """Creates a database savepoint.
        This can be rolled back to using :meth:`.rollback_to_savepoint`.

        :param name: name of the savepoint
        """
        self._check_obsolete()

        if not sqlIdentifier(name):
            raise ValueError("Invalid savepoint name: %r" % name)
        self.execute('SAVEPOINT %s' % name)
        self._modified_object_sets.append(set())
        self._created_object_sets.append(set())
        self._deleted_object_sets.append(set())
        self._savepoints.append(name)

    def rollback_to_savepoint(self, name):
        """Rollsback the store to a previous savepoint that was saved
        using :meth:`.savepoint`

        :param name: savepoint to move back to
        """
        self._check_obsolete()

        if not sqlIdentifier(name):
            raise ValueError("Invalid savepoint name: %r" % name)
        if not name in self._savepoints:
            raise ValueError("Unknown savepoint: %r" % name)

        self.execute('ROLLBACK TO SAVEPOINT %s' % name)

        for savepoint in reversed(self._savepoints[:]):
            # Objects may have changed in this transaction.
            # Make sure to autorelad the original values after the rollback
            for obj in self._modified_object_sets.pop():
                self.autoreload(obj)
            self._created_object_sets.pop()
            self._deleted_object_sets.pop()

            if self._savepoints.pop() == name:
                break

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

    def _check_obsolete(self):
        if self.obsolete:
            raise InterfaceError("This transaction has already been closed")

    def _process_pending_objs(self):
        # Fields to update te_modified for modified objs
        user = get_current_user(self)
        station = get_current_station(self)

        station_id = station and station.id
        te_time = const.NOW()
        user_id = user and user.id

        created_objs = set()
        modified_objs = set()
        deleted_objs = set()
        processed_objs = set()

        while self._need_process_pending():
            created_objs.update(*self._created_object_sets)
            modified_objs.update(*self._modified_object_sets)
            deleted_objs.update(*self._deleted_object_sets)

            # Remove already processed objs (can happen when an obj is
            # added here again when processing the hooks bellow).
            modified_objs -= processed_objs | created_objs | deleted_objs
            created_objs -= processed_objs | deleted_objs
            deleted_objs -= processed_objs

            # Make sure while will be False on next iteration. Unless any
            # object is added when processing the hooks bellow.
            self._reset_pending_objs()

            for deleted_obj in deleted_objs:
                deleted_obj.on_delete()
                processed_objs.add(deleted_obj)

            for created_obj in created_objs:
                created_obj.on_create()
                processed_objs.add(created_obj)

            for modified_obj in modified_objs:
                te_modified = modified_obj.te_modified
                te_modified.station_id = station_id
                te_modified.te_time = te_time
                te_modified.user_id = user_id

                modified_obj.on_update()
                processed_objs.add(modified_obj)
                # Invalidate the modified objects in other possible related
                # transactions
                autoreload_object(modified_obj)

    def _need_process_pending(self):
        return (any(self._created_object_sets) or
                any(self._modified_object_sets) or
                any(self._deleted_object_sets))

    def _reset_pending_objs(self):
        self._created_object_sets = [set()]
        self._modified_object_sets = [set()]
        self._deleted_object_sets = [set()]


def get_default_store():
    """This function returns the default/primary store.
    Notice that this store is considered read-only inside Stoqlib
    applications. Only transactions can modify objects and should be
    created using new_store().
    This store should not be closed, it will only close when we the
    application is shutdown.

    :returns: default store
    """
    global _default_store
    if _default_store is None:
        _default_store = db_settings.create_store()
        assert _default_store is not None
        # We intentionally leave this open, it's the default
        # store and should only be closed when we close the
        # application
    return _default_store


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
def _register_branch(store, station_name):
    import gtk
    from stoqlib.lib.parameters import sysparam

    store = new_store()
    if not sysparam(store).DEMO_MODE:
        if yesno(_("The computer '%s' is not registered to the Stoq "
                   "server at %s.\n\n"
                   "Do you want to register it "
                   "(requires administrator access) ?") %
                 (station_name, db_settings.address),
                 gtk.RESPONSE_NO, _("Quit"), _("Register computer")):
            store.close()
            raise SystemExit

        from stoqlib.gui.login import LoginHelper
        h = LoginHelper(username="admin")
        try:
            user = h.validate_user()
        except LoginError, e:
            store.close()
            error(str(e))

        if not user:
            store.close()
            error(_("Must login as 'admin'"))

    from stoqlib.domain.person import Branch
    from stoqlib.domain.station import BranchStation

    branches = Branch.select(store=store)
    if not branches:
        store.close()
        error(_("Schema error, no branches found"))

    # TODO
    # Always select the first branch as the main branch, until we
    # support multiple branches properly. And then, provide a way to the
    # user choose which one will be the main branch.
    branch = branches[0]

    try:
        station = BranchStation.create(store,
                                       branch=branch,
                                       name=station_name)
    except StoqlibError, e:
        error(_("ERROR: %s") % e)

    station_id = station.id
    store.commit(close=True)

    return store.find(BranchStation, id=station_id).one()


def set_current_branch_station(store, station_name):
    """Registers the current station and the branch of the station
    as the current branch for the system
    :param store: a store
    :param station_name: name of the station to register
    """

    # This might be called early, so make sure SQLObject
    # knows about Branch which might not have
    # been imported yet
    from stoqlib.domain.person import Branch
    Branch  # pyflakes

    if station_name is None:
        # For LTSP systems we cannot use the hostname as stoq is run
        # on a shared serve system. Instead the ip of the client system
        # is available in the LTSP_CLIENT environment variable
        station_name = os.environ.get('LTSP_CLIENT_HOSTNAME', None)
        if station_name is None:
            station_name = socket.gethostname()

    from stoqlib.domain.station import BranchStation
    station = store.find(BranchStation, name=station_name).one()
    if station is None:
        station = _register_branch(store, station_name)

    if not station.is_active:
        error(_("The computer <u>%s</u> is not active in Stoq") %
              station_name,
              _("To solve this, open the administrator application "
                "and re-activate this computer."))

    provide_utility(ICurrentBranchStation, station, replace=True)

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
