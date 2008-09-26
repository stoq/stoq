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
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##                  Johan Dahlin                <jdahlin@async.com.br>
##
""" Runtime routines for applications"""

import sys

from kiwi.component import get_utility, provide_utility, implements
from kiwi.log import Logger

from stoqlib.database.interfaces import (
    IDatabaseSettings, IConnection, ITransaction, ICurrentBranch,
    ICurrentBranchStation, ICurrentUser)
from stoqlib.database.orm import ORMObject, Transaction
from stoqlib.database.orm import sqlIdentifier, const, Update, IN
from stoqlib.exceptions import StoqlibError
from stoqlib.lib.message import error, yesno, info
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext
log = Logger('stoqlib.runtime')

#
# Working with connections and transactions
#

class StoqlibTransaction(Transaction):
    implements(ITransaction)

    def __init__(self, *args, **kwargs):
        self._modified_object_sets = [dict()]
        self._savepoints = []
        Transaction.__init__(self, *args, **kwargs)

    def _reset_modified(self):
        self._modified_object_sets = [dict()]

    def _update_transaction_entry(self):
        fields = dict(te_time=const.NOW())
        user = get_current_user(self)
        if user:
            fields['user_id'] = user.id

        station = get_current_station(self)
        if station is not None:
            fields['station_id'] = station.id

        for objdicts in self._modified_object_sets:
            for table, modified_te_objs in objdicts.iteritems():
                modified_obj_ids = [m.id for m in modified_te_objs]
                sql = Update('transaction_entry', fields,
                             where=IN(const.id, modified_obj_ids))
                self.query(self.sqlrepr(sql))

                # We changed the object behind ORMObjects back, sync them
                for modified_te in modified_te_objs:
                    modified_te.sync()

    def add_modified_object(self, obj):
        if obj.te_modified is not None:
            objdict = self._modified_object_sets[-1]
            objset = objdict.setdefault(type(obj), set())
            objset.add(obj.te_modified)

    def commit(self, close=False):
        self._update_transaction_entry()
        Transaction.commit(self, close=close)
        self._reset_modified()

    def rollback(self, name=None):
        if name:
            self.rollback_to_savepoint(name)
        else:
            # FIXME: SQLObject is busted, this is called from __del__
            if Transaction is not None:
                Transaction.rollback(self)
            self._reset_modified()

    def close(self):
        self._connection.close()
        self._obsolete = True

    def get(self, obj):
        if obj is None:
            return None

        if not isinstance(obj, ORMObject):
            raise TypeError("obj must be a ORMObject, not %r" % (obj,))

        table = type(obj)
        return table.get(obj.id, connection=self)

    def savepoint(self, name):
        if not sqlIdentifier(name):
            raise ValueError("Invalid savepoint name: %r" % name)
        self.query('SAVEPOINT %s' % name)
        self._modified_object_sets.append(dict())
        if not name in self._savepoints:
            self._savepoints.append(name)

    def rollback_to_savepoint(self, name):
        if not sqlIdentifier(name):
            raise ValueError("Invalid savepoint name: %r" % name)
        if not name in self._savepoints:
            raise ValueError("Unknown savepoint: %r" % name)

        self.query('ROLLBACK TO SAVEPOINT %s' % name)
        self._modified_object_sets.pop()
        self._savepoints.remove(name)

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
def _register_branch(station_name):
    import gtk
    settings = get_utility(IDatabaseSettings)
    if yesno(_("The computer <u>%s</u> is not registered to the Stoq "
               "server at %s.\n\n"
               "Do you want to register it "
               "(requires administrator access) ?") %
             (station_name, settings.address),
             gtk.RESPONSE_NO, _(u"Quit"), _(u"Register Computer")):
        raise SystemExit

    from stoqlib.gui.login import LoginHelper
    h = LoginHelper(username="admin")
    user = h.validate_user()
    if not user:
        error(_("Must login as 'admin'"))

    from stoqlib.domain.interfaces import IBranch
    from stoqlib.domain.person import Person
    from stoqlib.domain.station import BranchStation

    trans = new_transaction()
    branches = Person.iselect(IBranch, connection=trans)
    if not branches:
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
        error(_("ERROR: %s" % e))

    trans.commit(close=True)

def set_current_branch_station(conn, station_name):
    """Registers the current station and the branch of the station
    as the current branch for the system
    @param conn: a database connection
    @param station_name: name of the station to register
    """
    from stoqlib.domain.station import BranchStation
    station = BranchStation.selectOneBy(name=station_name, connection=conn)
    if station is None:
        _register_branch(station_name)
        info(_("%s was registered in Stoq.\n\nPlease restart." % (station_name,)))
        raise SystemExit

    if not station.is_active:
        error(_("The computer <u>%s</u> is not active in Stoq") %
              station_name,
              _("To solve this, open the administrator application "
                "and re-activate this computer."))

    provide_utility(ICurrentBranchStation, station)
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

