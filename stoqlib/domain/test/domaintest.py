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
                                      new_transaction)
from stoqlib.domain.exampledata import ExampleCreator

try:
    import unittest
    unittest # pyflakes
except:
    import unittest


class FakeAPITrans:
    def __init__(self):
        self.trans = None

    def __call__(self):
        return self

    def __enter__(self):
        return self.trans

    def __exit__(self, *args):
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


class FakeNamespace(object):
    def __init__(self):
        self.api = mock.Mock()
        self.api.trans = FakeAPITrans()
        self.DatabaseSettings = FakeDatabaseSettings
        self.StoqConfig = FakeStoqConfig
        self.datetime = mock.MagicMock(datetime)
        self.datetime.date.today.return_value = datetime.date(2012, 1, 1)

    def set_transaction(self, trans):
        self.api.trans.trans = trans


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
