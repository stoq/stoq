# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Base module to be used by all domain test modules"""

import datetime

import mock

from stoqlib.lib.kiwilibrary import library
library  # pyflakes

from stoqlib.database.runtime import (get_current_branch,
                                      new_transaction,
                                      StoqlibTransaction)
from stoqlib.domain.exampledata import ExampleCreator

try:
    import unittest
    unittest # pyflakes
except:
    import unittest


class FakeAPITrans:
    def __init__(self, trans=None):
        self.trans = trans

    def __call__(self):
        return self

    def __enter__(self):
        return self.trans

    def __exit__(self, *args):
        if self.trans is not None:
            self.trans.committed = True


class FakeStoqConfig:
    def __init__(self, settings):
        self.settings = settings
        self.options = None
        self.flushed = False

    def items(self, name):
        return []

    def get_settings(self):
        return self.settings

    def set_from_options(self, options):
        self.options = options

    def get_password(self):
        return 'password'

    def load_settings(self, settings):
        pass

    def get(self, section, value):
        if (section, value) == ('Database', 'enable_production'):
            return ''

    def flush(self):
        self.flushed = True


class FakeDatabaseSettings:
    def __init__(self, trans):
        self.trans = trans
        self.address = 'invalid'
        self.check = False
        self.password = ''

    def check_database_address(self):
        return self.check

    def has_database(self):
        return False

    def get_command_line_arguments(self):
        return []

    def get_default_connection(self):
        class FakeConn:
            def dbVersion(self):
                return (8, 4)
        return FakeConn()


class FakeStore:
    def __init__(self, trans):
        self.trans = trans

    def block_implicit_flushes(self):
        pass

    def unblock_implicit_flushes(self):
        pass

    def get(self, cls, obj_id):
        return self.trans.store.get(cls, obj_id)

    def add(self, obj):
        pass


class ReadOnlyTransaction(StoqlibTransaction):
    """Wraps a normal transaction but doesn't actually
    modify it, commit/rollback/close etc are no-ops"""

    # FIXME: This is probably better done as a subclass of StoqlibTransaction
    #        but mocking new_transaction and trans becomes a bit
    #        harder/different to do then.
    def __init__(self, trans):
        self.trans = trans
        self.store = FakeStore(trans)
        self._created_object_sets = [set()]
        self._modified_object_sets = [set()]

    def get(self, obj):
        return self.trans.get(obj)

    def rollback(self):
        pass

    def commit(self):
        pass

    def close(self):
        pass

    def __eq__(self, other):
        return self.trans == getattr(other, 'trans', None)


class FakeNamespace(object):
    """Commonly used mock objects goes in here"""
    def __init__(self):
        self.api = mock.Mock()
        self.api.trans = FakeAPITrans()
        self.DatabaseSettings = FakeDatabaseSettings
        self.StoqConfig = FakeStoqConfig
        self.datetime = mock.MagicMock(datetime)
        self.datetime.date.today.return_value = datetime.date(2012, 1, 1)

    def set_transaction(self, trans):
        # Since we are per default a class attribute we need to call this
        # when we get a transaction
        rd_trans = ReadOnlyTransaction(trans)
        self.api.trans.trans = rd_trans
        self.api.new_transaction.return_value = ReadOnlyTransaction(trans)
        self.api.trans.return_value = rd_trans
        if trans is not None:
            trans.readonly = rd_trans

    def set_retval(self, retval):
        self.api.trans.trans.retval = retval


class DomainTest(unittest.TestCase, ExampleCreator):

    fake = FakeNamespace()

    def __init__(self, test):
        unittest.TestCase.__init__(self, test)
        ExampleCreator.__init__(self)

    def setUp(self):
        self.trans = new_transaction()
        self.fake.set_transaction(self.trans)
        self.set_transaction(self.trans)

    def tearDown(self):
        self.fake.set_transaction(None)
        self.trans.rollback()
        self.clear()

    def collect_sale_models(self, sale):
        models = [sale,
                  sale.group]
        models.extend(sale.payments)
        branch = get_current_branch(self.trans)
        for item in sorted(sale.get_items(),
                           cmp=lambda a, b: cmp(a.sellable.description,
                                                b.sellable.description)):
            models.append(item.sellable)
            stock_item = item.sellable.product_storable.get_stock_item(branch)
            models.append(stock_item)
            models.append(item)
        p = list(sale.payments)[0]
        p.description = p.description.rsplit(' ', 1)[0]
        return models
