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

"""Tests for module L{stoqlib.database.runtime}"""

from stoqlib.database.orm import UnicodeCol
from stoqlib.domain.base import Domain
from stoqlib.domain.test.domaintest import DomainTest


class WillBeCommitted(Domain):

    SQL_DROP = """DROP TABLE IF EXISTS will_be_committed;"""
    SQL_CREATE = """CREATE TABLE will_be_committed (
        id serial NOT NULL PRIMARY KEY,
        test_var text,
        te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
        te_modified_id bigint UNIQUE REFERENCES transaction_entry(id)
        );"""

    test_var = UnicodeCol()

    def __init__(self, *args, **kwargs):
        super(WillBeCommitted, self).__init__(*args, **kwargs)
        self.reset()

    def reset(self):
        self.was_created = False
        self.was_updated = False
        self.was_deleted = False

        self.update_test_var_on_update = False
        self.on_update_called_count = 0

    def on_create(self):
        self.was_created = True

    def on_delete(self):
        self.was_deleted = True

    def on_update(self):
        self.was_updated = True

        if self.update_test_var_on_update:
            if self.on_update_called_count < 2:
                self.test_var = "%s+" % self.test_var

        self.on_update_called_count += 1


class StoqlibTransactionTest(DomainTest):

    def setUp(self):
        super(StoqlibTransactionTest, self).setUp()

        self.trans.query(''.join((WillBeCommitted.SQL_DROP,
                                  WillBeCommitted.SQL_CREATE)))
        self.trans.commit()

    def test_transaction_commit_hook(self):
        # Dummy will only be asserted for creation on the first commit.
        # After that it should pass all assert for nothing made.
        dummy_obj = WillBeCommitted(connection=self.trans,
                                    test_var='XXX')

        obj = WillBeCommitted(connection=self.trans,
                              test_var='AAA')
        # Test obj being created on database
        self.trans.commit()
        self._assert_created(obj)
        self._assert_created(dummy_obj)
        obj.reset()
        dummy_obj.reset()

        # Test obj being updated on the same object it was created
        obj.test_var = 'BBB'
        self.trans.commit()
        self._assert_updated(obj)
        self._assert_nothing_made(dummy_obj)
        obj.reset()

        # Test obj being modified inside on_update
        obj.test_var = 'CCC'
        obj.update_test_var_on_update = True
        self.trans.commit()
        self._assert_updated(obj)
        self._assert_nothing_made(dummy_obj)
        obj.reset()

        obj = WillBeCommitted.selectOneBy(connection=self.trans,
                                          id=obj.id)
        dummy_obj = WillBeCommitted.selectOneBy(connection=self.trans,
                                                id=dummy_obj.id)
        # Test obj being commited without any modification
        self.trans.commit()
        self._assert_nothing_made(obj)
        self._assert_nothing_made(dummy_obj)
        obj.reset()

        # Test obj being commited after modification.
        obj.test_var = 'DDD'
        self.trans.commit()
        self._assert_updated(obj)
        self._assert_nothing_made(dummy_obj)
        obj.reset()

        obj = WillBeCommitted(connection=self.trans,
                              test_var='EEE')
        self.trans.commit()
        obj.reset()
        # Test obj being deleted without any modification
        WillBeCommitted.delete(obj.id, self.trans)
        self.trans.commit()
        self._assert_deleted(obj)
        self._assert_nothing_made(dummy_obj)
        obj.reset()

        obj = WillBeCommitted(connection=self.trans,
                              test_var='EEE')
        self.trans.commit()
        obj.reset()
        # Test obj being deleted after modification
        obj.test_var = 'FFF'
        WillBeCommitted.delete(obj.id, self.trans)
        self.trans.commit()
        self._assert_deleted(obj)
        self._assert_nothing_made(dummy_obj)
        obj.reset()

        # Test obj being deleted after creation
        obj = WillBeCommitted(connection=self.trans,
                              test_var='EEE')
        WillBeCommitted.delete(obj.id, self.trans)
        self.trans.commit()
        self._assert_deleted(obj)
        self._assert_nothing_made(dummy_obj)
        obj.reset()

    #
    #  Private
    #

    def _assert_created(self, obj):
        self.assertTrue(obj.was_created)
        self.assertFalse(obj.was_updated)
        self.assertFalse(obj.was_deleted)
        self.assertEqual(obj.on_update_called_count, 0)

    def _assert_deleted(self, obj):
        self.assertFalse(obj.was_created)
        self.assertTrue(obj.was_deleted)
        self.assertFalse(obj.was_updated)
        self.assertEqual(obj.on_update_called_count, 0)

    def _assert_updated(self, obj):
        self.assertFalse(obj.was_created)
        self.assertFalse(obj.was_deleted)
        self.assertTrue(obj.was_updated)
        self.assertEqual(obj.on_update_called_count, 1)

    def _assert_nothing_made(self, obj):
        self.assertFalse(obj.was_updated)
        self.assertFalse(obj.was_deleted)
        self.assertFalse(obj.was_created)
        self.assertEqual(obj.on_update_called_count, 0)
