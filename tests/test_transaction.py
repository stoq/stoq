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
import unittest

from stoqlib.database import finish_transaction
from stoqlib.domain.person import Person
from stoqlib.lib.runtime import (new_transaction, get_current_user,
                                 get_current_station)

import tests.base
tests.base #pyflakes

class TestStation(unittest.TestCase):
    def setUp(self):
        self.conn = new_transaction()

    def tearDown(self):
        finish_transaction(self.conn)

    def test_timestamp(self):
        before = datetime.datetime.now()
        time.sleep(1)
        person = Person(name="dummy", connection=self.conn)
        created = datetime.datetime.now()

        self.assertEqual(person.te_created.timestamp,
                         person.te_modified.timestamp)

        self.conn.commit()
        person.name = 'updated'
        self.conn.commit()

        self.assertNotEqual(person.te_created.timestamp,
                            person.te_modified.timestamp)

        updated = datetime.datetime.now()

        dates = [(before, 'before create'),
                 (person.te_created.timestamp, 'create'),
                 (created, 'after create'),
                 (person.te_modified.timestamp, 'modifiy' ),
                 (updated, 'after modify')]
        for i in range(len(dates)-1):
            before, before_name = dates[i]
            after, after_name = dates[i+1]
            if before >= after:
                raise AssertionError(
                    "'%s' (%s) was expected to be before '%s' (%s)" % (
                    before_name, before, after_name, after))

    def test_user(self):
        user = get_current_user(self.conn)
        person = Person(name="dummy", connection=self.conn)

        self.assertEqual(person.te_created.user, user)

    def test_station(self):
        station = get_current_station(self.conn)
        person = Person(name="dummy", connection=self.conn)

        self.assertEqual(person.te_created.station, station)
