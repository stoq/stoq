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

from decimal import Decimal

from storm.expr import Select

from stoqlib.database.expr import StatementTimestamp
from stoqlib.database.runtime import get_default_store, new_store
from stoqlib.domain.person import Person
from stoqlib.domain.system import TransactionEntry
from stoqlib.domain.test.domaintest import DomainTest


def _query_server_time(store):
    # Be careful, this opens up a new connection, queries the server
    # and closes the connection. That takes ~150ms
    date = store.execute(Select([StatementTimestamp()])).get_one()[0]
    # Storm removes tzinfo on it's datetime columns. Do the same here
    # or the comparison on testTimestamp will fail.
    return date.replace(tzinfo=None)


class TestTransaction(DomainTest):
    def test_timestamp(self):
        # Create person
        before = _query_server_time(self.store)
        person = Person(name=u'dummy', store=self.store)
        created = _query_server_time(self.store)

        self.store.commit()

        # Now modify the person
        first_te = person.te.te_time
        person.name = u'dummy transaction test'
        self.store.commit()

        # te_time should have changed
        self.assertNotEqual(first_te, person.te.te_time)

        updated = _query_server_time(self.store)

        dates = [
            (u'before create', before),
            (u'create', first_te),
            (u'after create', created),
            (u'modifiy', person.te.te_time),
            (u'after modify', updated),
        ]
        for i in range(len(dates) - 1):
            before_name, before = dates[i]
            after_name, after = dates[i + 1]
            before_decimal = Decimal(before.strftime(u'%s.%f'))
            after_decimal = Decimal(after.strftime(u'%s.%f'))
            if before_decimal > after_decimal:
                fmt = u"'%s' (%s) was expected to be before '%s' (%s)"
                raise AssertionError(
                    fmt % (before_name, before,
                           after_name, after))

    def test_remove(self):
        # Total of transaction entries in the begining of the test
        start_te = self.store.find(TransactionEntry).count()

        person = Person(name=u'dummy', store=self.store)
        person_te_id = person.te.id

        # Afte creating a person, there should be one transaction entry more
        total_te = self.store.find(TransactionEntry).count()
        self.assertEqual(total_te, start_te + 1)

        person_te = self.store.find(TransactionEntry, id=person_te_id).one()
        self.assertEquals(person.te.id, person_te.id)

        # Now remove this person, and the transaction entry should be gone
        self.store.remove(person)

        # Total of transaction entries is back to the original
        total_te = self.store.find(TransactionEntry).count()
        self.assertEqual(total_te, start_te)

        # The transaction entry created for the person should be removed from
        # the database
        person_te = self.store.find(TransactionEntry, id=person_te_id).one()
        self.assertEquals(person_te, None)

    def test_cache_invalidation(self):
        # First create a new person in an outside transaction
        outside_store = new_store()
        outside_person = Person(name=u'doe', store=outside_store)
        outside_store.commit()

        # Get this person in the default store
        default_store = get_default_store()
        default_person = default_store.find(Person, id=outside_person.id).one()
        self.assertEqual(default_person.name, u'doe')

        # Now, select that same person in an inside store
        inside_store = new_store()

        inside_person = inside_store.fetch(outside_person)

        # Change and commit the changes on this inside store
        inside_person.name = u'john'

        # Flush to make sure the database was updated
        inside_store.flush()

        # Before comminting the other persons should still be 'doe'
        self.assertEqual(default_person.name, u'doe')
        self.assertEqual(outside_person.name, u'doe')

        inside_store.commit()

        # We expect the changes to reflect on the connection
        self.assertEqual(default_person.name, u'john')

        # and also on the outside store
        self.assertEqual(outside_person.name, u'john')

        outside_store.close()
        inside_store.close()

    def tearDown(self):
        # Make sure to remove all committed persons from the database
        with new_store() as store:
            test_names = [u'dummy transaction test', u'dummy', u'doe', u'john']
            store.find(Person, Person.name.is_in(test_names)).remove()

        DomainTest.tearDown(self)
