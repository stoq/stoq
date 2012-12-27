# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

from stoqlib.domain.person import UserBranchAccess
from stoqlib.domain.test.domaintest import DomainTest


class TestUserBranchAccess(DomainTest):
    def test_has_access(self):
        user = self.create_user()
        branch = self.create_branch()

        self.assertFalse(UserBranchAccess.has_access(self.store, None, None))
        self.assertFalse(UserBranchAccess.has_access(self.store, user, None))
        self.assertFalse(UserBranchAccess.has_access(self.store, None, branch))
        self.assertFalse(UserBranchAccess.has_access(self.store, user, branch))

        user.add_access_to(branch)
        self.assertTrue(UserBranchAccess.has_access(self.store, user, branch))
