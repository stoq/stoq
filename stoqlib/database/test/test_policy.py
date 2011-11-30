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
""" This module test all class in stoq/database/policy.py """

import unittest

from stoqlib.enums import SyncPolicy
from stoqlib.database.policy import (get_policy_by_name,
                                     SynchronizationPolicy)


class TestStation(unittest.TestCase):

    def test_getPolicyByName(self):
        policy = get_policy_by_name('shop')
        self.failUnless(issubclass(policy, SynchronizationPolicy))
        self.failUnless(type(policy.tables), list)
        self.failUnless(len(policy.tables) > 0)
        self.assertEqual(type(policy.tables[0][0]), str)
        self.failUnless(isinstance(policy.tables[0][1], SyncPolicy))
        self.assertEqual(policy.name, 'shop')

    def test_getPolicyByNameError(self):
        self.assertRaises(LookupError, get_policy_by_name, 'invalid-policy')
