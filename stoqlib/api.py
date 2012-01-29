# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source
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
##

"""Stoqlib API

Singleton object which makes it easier to common stoqlib APIs without
having to import their symbols.
"""
from contextlib import contextmanager

from kiwi.component import get_utility
from twisted.internet.defer import inlineCallbacks, returnValue

from stoqlib.database.interfaces import IDatabaseSettings
from stoqlib.database.runtime import (get_connection, new_transaction,
                                      rollback_and_begin, finish_transaction)
from stoqlib.database.runtime import (get_current_branch,
                                      get_current_station, get_current_user)
from stoqlib.lib.settings import get_settings
from stoqlib.lib.interfaces import IStoqConfig
from stoqlib.lib.parameters import sysparam, is_developer_mode
from stoqlib.l10n.l10n import get_l10n_field


class StoqAPI(object):
    def get_connection(self):
        return get_connection()

    def new_transaction(self):
        return new_transaction()

    def finish_transaction(self, trans, model):
        return finish_transaction(trans, model)

    def rollback_and_begin(self, trans):
        rollback_and_begin(trans)

    def get_current_branch(self, conn):
        return get_current_branch(conn)

    def get_current_station(self, conn):
        return get_current_station(conn)

    def get_current_user(self, conn):
        return get_current_user(conn)

    @contextmanager
    def trans(self):
        """Creates a new transaction and commits/closes it when done.

        It should be used as:

          with api.trans() as trans:
              ...

        When the execution of the with statement has finished this
        will commit the object, close the transaction.
        trans.retval will be used to determine if the transaction
        should be committed or rolled back (via finish_transaction)
        """
        trans = self.new_transaction()
        yield trans

        # Editors/Wizards requires the trans.retval variable to
        # be set or it won't be committed.
        if trans.needs_retval:
            retval = bool(trans.retval)
            if self.finish_transaction(trans, retval):
                trans.committed = True
            else:
                trans.committed = False
        # Normal transaction, just commit it
        else:
            trans.commit()
            trans.committed = True
        trans.close()

    @property
    def config(self):
        return get_utility(IStoqConfig)

    @property
    def db_settings(self):
        return get_utility(IDatabaseSettings)

    @property
    def user_settings(self):
        return get_settings()

    def sysparam(self, conn):
        return sysparam(conn)

    def is_developer_mode(self):
        return is_developer_mode()

    @property
    def async(self):
        """Async API for dialog, it's built on-top of
        twisted and is meant to be used in the following way:

        @api.async
        def _run_a_dialog(self):
            model = yield run_dialog(SomeDialog, parent, conn)

        If the function returns a value, you need to use api.asyncReturn, eg:

            api.asyncReturn(model)
        """

        return inlineCallbacks

    def asyncReturn(self, value=None):
        return returnValue(value)

    def get_l10n_field(self, conn, field_name):
        return get_l10n_field(conn, field_name)

api = StoqAPI()
