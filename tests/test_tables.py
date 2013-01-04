# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

import glob
import unittest

from kiwi.python import namedAny

from stoqlib import domain
from stoqlib.database.orm import ORMObject
from stoqlib.database.tables import get_table_types


def _introspect_tables():
    base_dir = domain.__path__[0]
    filenames = []
    filenames.extend(glob.glob(base_dir + '/*.py'))
    filenames.extend(glob.glob(base_dir + '/payment/*.py'))
    tables = []

    for filename in filenames:
        if '__init__' in filename:
            continue
        module_name = filename[len(base_dir) + 1:-3]
        module_name = 'stoqlib.domain.' + module_name.replace('/', '.')
        module = namedAny(module_name)
        for attr in dir(module):
            value = getattr(module, attr)
            try:
                if not issubclass(value, ORMObject):
                    continue
            except TypeError:
                continue
            if value.__dict__.get('__storm_table__', 'invalid') == 'invalid':
                continue

            tables.append(value)

    return tables


class TableTypeTest(unittest.TestCase):

    def test(self):
        expected = set(get_table_types())
        introspected = set(_introspect_tables())
        if expected != introspected:
            candidate = expected.difference(introspected)
            if not candidate:
                candidate = introspected.difference(expected)
            tbls = sorted([t.__name__ for t in candidate])
            self.fail("Missing tables: %s.\nPlease add them to "
                      "stoqlib.database.tables" % (', '.join(tbls, )))


if __name__ == '__main__':
    unittest.main()
