# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source
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

import sys

from kiwi.component import get_utility, provide_utility, implements
from kiwi.log import Logger

from stoqlib.database.interfaces import (
    IDatabaseSettings, IConnection, ITransaction, ICurrentBranch,
    ICurrentBranchStation, ICurrentUser)
from stoqlib.database.orm import ORMObject, Transaction
from stoqlib.database.orm import sqlIdentifier, const
from stoqlib.exceptions import LoginError, StoqlibError
from stoqlib.lib.message import error, yesno
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext
log = Logger('stoqlib.runtime')

#
# Working with connections and transactions
#


class StoqlibTransaction(Transaction):
    """
    @ivar retval: The return value of a operation this transaction
      is covering. Usually a domain object that was modified
    @ivar needs_retval: If this is set to True, the retval variable
      needs to be set to a non-zero value to be committed, see
      stoqlib.api.trans
    """
    implements(ITransaction)

    def __init__(self, *args, **kwargs):
        self._savepoints = []
        self._related_transactions = set()
        self.retval = None
        self.needs_retval = False
        Transaction.__init__(self, *args, **kwargs)

        self._reset_pending_objs()

    #
    #  ITransaction implementation
    #

    def add_created_object(self, obj):
        obj_set = self._created_object_sets[-1]
        obj_set.add(obj)

    def add_modified_object(self, obj):
        obj_set = self._modified_object_sets[-1]
        obj_set.add(obj)

    def add_deleted_object(self, obj):
        obj_set = self._deleted_object_sets[-1]
        obj_set.add(obj)

    def commit(self, close=False):
        self._process_pending_objs()
        Transaction.commit(self, close=close)

    def rollback(self, name=None):
        if name:
            self.rollback_to_savepoint(name)
        else:
            # FIXME: SQLObject is busted, this is called from __del__
            if Transaction is not None:
                Transaction.rollback(self)
            self._reset_pending_objs()

    def close(self):
        self._connection.close()
        self._obsolete = True

    def get(self, obj):
        if obj is None:
            return None

        if not isinstance(obj, ORMObject):
            raise TypeError("obj must be a ORMObject, not %r" % (obj, ))

        # sqlobject invalidates the objects from the connection, but not from
        # other transactions. If the object we are getting now comes from
        # another transaction, save it so we can invalidate the objects modified
        # in this transaction when committing
        other_conn = obj.get_connection()
        if isinstance(other_conn, StoqlibTransaction):
            self._related_transactions.add(other_conn)

        table = type(obj)
        return table.get(obj.id, connection=self)

    def savepoint(self, name):
        if not sqlIdentifier(name):
            raise ValueError("Invalid savepoint name: %r" % name)
        self.query('SAVEPOINT %s' % name)
        self._modified_object_sets.append(set())
        self._created_object_sets.append(set())
        self._deleted_object_sets.append(set())
        if not name in self._savepoints:
            self._savepoints.append(name)

    def rollback_to_savepoint(self, name):
        if not sqlIdentifier(name):
            raise ValueError("Invalid savepoint name: %r" % name)
        if not name in self._savepoints:
            raise ValueError("Unknown savepoint: %r" % name)

        self.query('ROLLBACK TO SAVEPOINT %s' % name)
        self._modified_object_sets.pop()
        self._created_object_sets.pop()
        self._deleted_object_sets.pop()
        self._savepoints.remove(name)

    #
    #  Private
    #

    def _process_pending_objs(self):
        # Fields to update te_modified for modified objs
        user = get_current_user(self)
        station = get_current_station(self)
        te_fields = {'te_time': const.NOW(),
                     'user_id': user and user.id,
                     'station_id': station and station.id}

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
                modified_obj.te_modified.set(**te_fields)
                modified_obj.on_update()
                processed_objs.add(modified_obj)

                # Invalidate the modified objects in other possible related
                # transactions
                for trans in self._related_transactions:
                    klass = type(modified_obj)
                    cache = trans.cache.tryGet(modified_obj.id, klass)
                    if cache:
                        cache.expire()

    def _need_process_pending(self):
        return (any(self._created_object_sets) or
                any(self._modified_object_sets) or
                any(self._deleted_object_sets))

    def _reset_pending_objs(self):
        self._created_object_sets = [set()]
        self._modified_object_sets = [set()]
        self._deleted_object_sets = [set()]


def get_connection():
    """This function returns a connection to the current database.
    Notice that connections are considered read-only inside Stoqlib
    applications. Only transactions can modify objects and should be
    created using new_transaction().
    This function depends on the IDatabaseSettings utility which must be
    provided before it can be used.

    @returns: a database connection
    """
    conn = get_utility(IConnection, None)
    if conn is None:
        try:
            settings = get_utility(IDatabaseSettings)
        except NotImplementedError:
            raise StoqlibError(
                'You need to provide a IDatabaseSettings utility before '
                'calling get_connection')
        conn = settings.get_connection()
        assert conn is not None

        # Stoq applications always use transactions explicitly
        conn.autoCommit = False

        provide_utility(IConnection, conn)
    return conn


def new_transaction():
    """
    Create a new transaction.
    @returns: a transaction
    """
    log.debug('Creating a new transaction in %s()'
              % sys._getframe(1).f_code.co_name)
    _transaction = StoqlibTransaction(get_connection())
    assert _transaction is not None
    return _transaction


def rollback_and_begin(trans):
    """
    Abort changes in models and begins the transaction.
    @param trans: a transaction
    """
    trans.rollback()
    trans.begin()


def finish_transaction(trans, commit):
    """Encapsulated method for committing/aborting changes in models.
    @param trans: a transaction
    @param commit: True for commit, False for rollback_and_begin
    """

    # Allow False/None
    if commit:
        trans.commit()
    else:
        rollback_and_begin(trans)

    return commit


#
# User methods
#
def _register_branch(conn, station_name):
    import gtk
    from stoqlib.lib.parameters import sysparam

    trans = new_transaction()
    if not sysparam(trans).DEMO_MODE:
        settings = get_utility(IDatabaseSettings)
        if yesno(_("The computer <u>%s</u> is not registered to the Stoq "
                   "server at %s.\n\n"
                   "Do you want to register it "
                   "(requires administrator access) ?") %
                 (station_name, settings.address),
                 gtk.RESPONSE_NO, _("Quit"), _("Register computer")):
            trans.close()
            raise SystemExit

        from stoqlib.gui.login import LoginHelper
        h = LoginHelper(username="admin")
        try:
            user = h.validate_user()
        except LoginError, e:
            trans.close()
            error(e)

        if not user:
            trans.close()
            error(_("Must login as 'admin'"))

    from stoqlib.domain.interfaces import IBranch
    from stoqlib.domain.person import Person
    from stoqlib.domain.station import BranchStation

    branches = Person.iselect(IBranch, connection=trans)
    if not branches:
        trans.close()
        error(_("Schema error, no branches found"))

    # TODO
    # Always select the first branch as the main branch, until we
    # support multiple branches properly. And then, provide a way to the
    # user choose which one will be the main branch.
    branch = branches[0]

    try:
        station = BranchStation.create(trans,
                                       branch=branch,
                                       name=station_name)
    except StoqlibError, e:
        error(_("ERROR: %s") % e)

    station_id = station.id
    trans.commit(close=True)

    return BranchStation.get(station_id, connection=conn)


def set_current_branch_station(conn, station_name):
    """Registers the current station and the branch of the station
    as the current branch for the system
    @param conn: a database connection
    @param station_name: name of the station to register
    """
    from stoqlib.domain.station import BranchStation
    station = BranchStation.selectOneBy(name=station_name, connection=conn)
    if station is None:
        station = _register_branch(conn, station_name)

    if not station.is_active:
        error(_("The computer <u>%s</u> is not active in Stoq") %
              station_name,
              _("To solve this, open the administrator application "
                "and re-activate this computer."))

    provide_utility(ICurrentBranchStation, station)

    if station.branch:
        provide_utility(ICurrentBranch, station.branch)


def get_current_user(conn):
    """Fetch the user which is currently logged into the system or None
    None means that there are no utilities available which in turn
    should only happens during startup, for example when creating
    a new database or running the migration script,
    at that point no users are logged in

    @returns: currently logged in user or None
    @rtype: an object implementing IUser
    """
    user = get_utility(ICurrentUser, None)
    if user is not None:
        return user.get(user.id, connection=conn)


def get_current_branch(conn):
    """Fetches the current branch company.

    @returns: the current branch
    @rtype: an object implementing IBranch
    """

    branch = get_utility(ICurrentBranch, None)
    if branch is not None:
        return branch.get(branch.id, connection=conn)


def get_current_station(conn):
    """Fetches the current station (computer) which we are running on
    @param: current station
    @rtype: BranchStation
    """
    station = get_utility(ICurrentBranchStation, None)
    if station is not None:
        return station.get(station.id, connection=conn)
