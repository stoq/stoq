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
## Author(s):   Johan Dahlin      <jdahlin@async.com.br>
##
""" This module test all class in stoq/domain/transaction.py """

import datetime
import time

from stoqlib.database.runtime import (get_current_user,
                                      get_current_station,
                                      new_transaction)
from stoqlib.domain.person import Person
from stoqlib.domain.transaction import TransactionEntry

from stoqlib.domain.test.domaintest import DomainTest

NAME = 'dummy transaction test'

class TestTransaction(DomainTest):
    def testTimestamp(self):
        # The sleeps are here because the client and server
        # might be out of sync, datetime.dateime.now() is client side
        # while te_time is set on the server side, we should ideally move
        # everything to the server side
        before = datetime.datetime.now()
        time.sleep(.1)

        person = Person(name='dummy', connection=self.trans)
        time.sleep(.1)

        created = datetime.datetime.now()
        time.sleep(.1)

        self.trans.commit()
        self.assertEqual(person.te_created.te_time,
                         person.te_modified.te_time)

        person.name = NAME
        self.trans.commit()

        self.assertNotEqual(person.te_created.te_time,
                            person.te_modified.te_time)

        time.sleep(.1)
        updated = datetime.datetime.now()

        dates = [(before, 'before create'),
                 (person.te_created.te_time, 'create'),
                 (created, 'after create'),
                 (person.te_modified.te_time, 'modifiy' ),
                 (updated, 'after modify')]
        for i in range(len(dates)-1):
            before, before_name = dates[i]
            after, after_name = dates[i+1]
            if before >= after:
                raise AssertionError(
                    "'%s' (%s) was expected to be before '%s' (%s)" % (
                    before_name, before, after_name, after))

    def testUser(self):
        user = get_current_user(self.trans)
        person = Person(name=NAME, connection=self.trans)

        self.assertEqual(person.te_created.user, user)

    def testStation(self):
        station = get_current_station(self.trans)
        person = Person(name=NAME, connection=self.trans)

        self.assertEqual(person.te_created.station, station)

    def testEmpty(self):
        entry = TransactionEntry(te_time=datetime.datetime.now(),
                                 connection=self.trans,
                                 type=TransactionEntry.CREATED)
        self.assertEqual(entry.user, None)
        self.assertEqual(entry.station, None)

    def tearDown(self):
        trans = new_transaction()
        for person in Person.selectBy(name=NAME,
                                      connection=trans):
            Person.delete(person.id, connection=trans)
        trans.commit()
        DomainTest.tearDown(self)
