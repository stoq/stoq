# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2013 Async Open Source <http://www.async.com.br>
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

import contextlib
import datetime
import os

import mock
import unittest

from stoqlib.lib.kiwilibrary import library
library  # pylint: disable=W0104

import stoqlib
from stoqlib.database.runtime import (get_current_branch,
                                      new_store,
                                      StoqlibStore)
from stoqlib.database.testsuite import StoqlibTestsuiteTracer
from stoqlib.domain.base import Domain
from stoqlib.domain.exampledata import ExampleCreator
from stoqlib.lib.dateutils import localdate, localdatetime


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

    def load_settings(self, settings):
        pass

    def get(self, section, value):
        if (section, value) == (u'Database', u'enable_production'):
            return u''

    def flush(self):
        self.flushed = True


class FakeStore(object):
    def close(self):
        pass


class FakeDatabaseSettings:
    def __init__(self, store):
        self.store = store
        self.address = u'invalid'
        self.dbname = u'stoq'
        self.check = False
        self.password = u'password'
        self.username = u'username'
        self.port = 12345

    def check_database_address(self):
        return self.check

    def has_database(self):
        return False

    def get_command_line_arguments(self):
        return ['-d', self.dbname,
                '-p', unicode(self.port),
                '-u', self.username,
                '-w', self.password]

    def get_default_connection(self):
        return FakeStore()

    def create_super_store(self):
        return FakeStore()


class ReadOnlyStore(StoqlibStore):
    """Wraps a normal store but doesn't actually
    modify it, commit/rollback/close etc are no-ops"""

    def __init__(self, database, real_store):
        # Intentionally *not* calling StoqlibStore.__init__ since this
        # creates an additional database connection
        self.real_store = real_store
        self.retval = False

    # Store

    def add(self, obj):
        pass

    def flush(self):
        pass

    def get(self, cls, key_id):
        return self.real_store.get(cls, key_id)

    # Stoqlib Store

    def fetch(self, obj):
        return obj

    def rollback(self, close=True):
        pass

    def commit(self):
        pass

    def close(self):
        pass

    def __eq__(self, other):
        return self.real_store == getattr(other, 'real_store', None)


class FakeNamespace(object):
    """Commonly used mock objects goes in here"""
    def __init__(self):
        self.api = mock.Mock()
        self.api.get_current_branch = get_current_branch
        self.DatabaseSettings = FakeDatabaseSettings
        self.StoqConfig = FakeStoqConfig
        self.datetime = mock.MagicMock(datetime)
        self.datetime.datetime.today.return_value = localdatetime(2012, 1, 1)
        self.datetime.datetime.now.return_value = localdatetime(2012, 1, 1)
        self.datetime.date.today.return_value = localdate(2012, 1, 1).date()

    def set_store(self, store):
        # Since we are per default a class attribute we need to call this
        # when we get a store
        database = mock.Mock()
        rd_store = ReadOnlyStore(database, store)
        self.api.store = rd_store
        self.api.new_store.return_value = ReadOnlyStore(database, store)
        if store is not None:
            store.readonly = rd_store

    def set_retval(self, retval):
        self.api.store.retval = retval


class DomainTest(unittest.TestCase, ExampleCreator):

    fake = FakeNamespace()

    def __init__(self, test):
        unittest.TestCase.__init__(self, test)
        ExampleCreator.__init__(self)

    @classmethod
    def setUpClass(cls):
        cls.store = new_store()
        cls.fake.set_store(cls.store)

    @classmethod
    def tearDownClass(cls):
        cls.store.close()
        cls.fake.set_store(None)

    def setUp(self):
        self.set_store(self.store)

    def tearDown(self):
        self.store.rollback(close=False)
        self.clear()

    def get_oficial_plugins_names(self):
        """Get official plugins names

        Since pluginmanager is prepared to work with plugins defined on
        the same directory as stoq repository, this is a helper for getting
        only the ones defined on stoq repository's themselves.
        """
        base_dir = os.path.dirname(os.path.dirname(stoqlib.__file__))
        plugins_dir = os.path.join(base_dir, 'plugins')
        return set(unicode(d) for d in os.listdir(plugins_dir) if
                   not d.startswith('__init__'))

    @contextlib.contextmanager
    def count_tracer(self):
        """Count the number of statements that are executed during
        a specific context, this is useful for local performance testing
        where the number of statements shouldn't increase for a specific
        operation.

        For this to behave consistently when running one test or many tests,
        it will clear common caches before starting, so the number in here
        will be higher than in the actual application.
        """
        self.store.flush()
        self.store.invalidate()

        tracer = StoqlibTestsuiteTracer()
        tracer.install()
        yield tracer
        tracer.remove()

    @contextlib.contextmanager
    def sysparam(self, **kwargs):
        """
        Updates a set of system parameters within a context.
        The values will be reverted when leaving the scope.
        kwargs contains a dictionary of parameter name->value
        """
        from stoqlib.lib.parameters import sysparam
        old_values = {}
        for param, value in kwargs.items():
            if type(value) is bool:
                old_values[param] = sysparam.get_bool(param)
                sysparam.set_bool(self.store, param, value)
            elif type(value) is int:
                old_values[param] = sysparam.get_int(param)
                sysparam.set_int(self.store, param, value)
            elif isinstance(value, Domain) or value is None:
                old_values[param] = sysparam.get_object(self.store, param)
                sysparam.set_object(self.store, param, value)
            elif isinstance(value, basestring):
                old_values[param] = sysparam.get_string(param)
                sysparam.set_string(self.store, param, value)
            else:
                raise NotImplementedError(type(value))
        try:
            yield
        finally:
            for param, value in old_values.items():
                if type(value) is bool:
                    sysparam.set_bool(self.store, param, value)
                elif type(value) is int:
                    sysparam.set_int(self.store, param, value)
                elif isinstance(value, Domain) or value is None:
                    sysparam.set_object(self.store, param, value)
                elif isinstance(value, basestring):
                    sysparam.set_string(self.store, param, value)
                else:
                    raise NotImplementedError(type(value))

    def collect_sale_models(self, sale):
        models = [sale,
                  sale.group]
        models.extend(sale.payments)
        branch = get_current_branch(self.store)
        for item in sorted(sale.get_items(),
                           cmp=lambda a, b: cmp(a.sellable.description,
                                                b.sellable.description)):
            models.append(item.sellable)
            stock_item = item.sellable.product_storable.get_stock_item(
                branch, batch=item.batch)
            models.append(stock_item)
            models.append(item)
        payments = list(sale.payments)
        if len(payments):
            p = payments[0]
            p.description = p.description.rsplit(u' ', 1)[0]
        return models
