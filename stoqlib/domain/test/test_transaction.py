# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" This module test all class in stoq/domain/system.py """

import datetime
from decimal import Decimal
from nose.exc import SkipTest

from stoqlib.database.runtime import (get_current_user,
                                      get_current_station,
                                      get_default_store,
                                      new_store)
from stoqlib.domain.person import Person
from stoqlib.domain.system import TransactionEntry
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.database.settings import db_settings

NAME = 'dummy transaction test'


def _query_server_time(store):
    # Be careful, this opens up a new connection, queries the server
    # and closes the connection. That takes ~150ms
    if db_settings.rdbms == 'postgres':
        return store.execute("SELECT NOW();").get_all()[0][0]
    else:
        raise NotImplementedError


class TestTransaction(DomainTest):
    def testTimestamp(self):
        # Inside a transaction, NOW() returns always the same value.
        # We should fix te_time setting to use datetime.now or clock_timestamp.
        # See Bug 5282
        raise SkipTest('Problems with NOW and transactions')
        # The sleeps are here because the client and server
        # might be out of sync, datetime.dateime.now() is client side
        # while te_time is set on the server side, we should ideally move
        # everything to the server side
        before = _query_server_time(self.store)

        person = Person(name='dummy', store=self.store)

        created = _query_server_time(self.store)

        self.store.commit()
        self.assertEqual(person.te_created.te_time,
                         person.te_modified.te_time)

        person.name = NAME
        self.store.commit()

        self.assertNotEqual(person.te_created.te_time,
                            person.te_modified.te_time)

        updated = _query_server_time(self.store)

        dates = [
            ('before create', before),
            ('create', person.te_created.te_time),
            ('after create', created),
            ('modifiy', person.te_modified.te_time),
            ('after modify', updated),
            ]
        for i in range(len(dates) - 1):
            before_name, before = dates[i]
            after_name, after = dates[i + 1]
            before_decimal = Decimal(before.strftime('%s.%f'))
            after_decimal = Decimal(after.strftime('%s.%f'))
            if before_decimal > after_decimal:
                raise AssertionError(
                    "'%s' (%s) was expected to be before '%s' (%s)" % (
                    before_name, before, after_name, after))

    def testCacheInvalidation(self):
        # First create a new person in an outside transaction
        outside_store = new_store()
        outside_person = Person(name='doe', store=outside_store)
        outside_store.commit()

        # Get this person in the default store
        store = get_default_store()
        db_person = store.find(Person, id=outside_person.id).one()
        self.assertEqual(db_person.name, 'doe')

        # Now, select that same person in an inside store
        inside_store = new_store()
        inside_person = inside_store.fetch(outside_person)

        # Change and commit the changes on this inside store
        inside_person.name = 'john'

        # Flush to make sure the database was updated
        inside_store.flush()

        # Before comminting the other persons should still be 'doe'
        self.assertEqual(db_person.name, 'doe')
        self.assertEqual(outside_person.name, 'doe')

        inside_store.commit()

        # We expect the changes to reflect on the connection
        self.assertEqual(db_person.name, 'john')

        # and also on the outside store
        self.assertEqual(outside_person.name, 'john')

        outside_store.close()
        inside_store.close()

    def testUser(self):
        user = get_current_user(self.store)
        person = Person(name=NAME, store=self.store)

        self.assertEqual(person.te_created.user, user)

    def testStation(self):
        station = get_current_station(self.store)
        person = Person(name=NAME, store=self.store)

        self.assertEqual(person.te_created.station, station)

    def testEmpty(self):
        entry = TransactionEntry(te_time=datetime.datetime.now(),
                                 store=self.store,
                                 type=TransactionEntry.CREATED)
        self.assertEqual(entry.user, None)
        self.assertEqual(entry.station, None)

    def tearDown(self):
        store = new_store()
        for person in Person.selectBy(name=NAME,
                                      store=store):
            Person.delete(person.id, store=store)
        store.commit()
        DomainTest.tearDown(self)
        store.close()
