# -*- Mode: Python; coding: utf-8 -*-
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

from kiwi.component import get_utility, provide_utility
from zope.interface import implementer

from stoqlib.lib.decorators import public
from stoqlib.lib.interfaces import IPermissionManager


@public(since="1.5.0")
@implementer(IPermissionManager)
class PermissionManager(object):

    # ACCESS AND SEARCH are synonyms.
    PERM_ACCESS = PERM_SEARCH = 1
    PERM_CREATE = 2
    PERM_EDIT = 4
    PERM_DETAILS = 8
    PERM_DELETE = 16

    # Aliases
    PERM_ALL = (PERM_DETAILS | PERM_EDIT | PERM_CREATE | PERM_SEARCH | PERM_DELETE)
    PERM_HIDDEN = 0
    PERM_NO_DETAILS = PERM_SEARCH
    PERM_ONLY_DETAILS = PERM_SEARCH | PERM_DETAILS

    def __init__(self):
        self._default_domain_permission = self.PERM_ALL
        self._perms = {}

    def set(self, key, permission):
        self._perms[key] = permission

    def get(self, key):
        return self._perms.get(key, self._default_domain_permission)

    def can_search(self, key):
        return self.get(key) & self.PERM_SEARCH

    def can_edit(self, key):
        return self.get(key) & self.PERM_EDIT

    def can_create(self, key):
        return self.get(key) & self.PERM_CREATE

    def can_see_details(self, key):
        return self.get(key) & self.PERM_DETAILS

    def can_delete(self, key):
        return self.get(key) & self.PERM_DELETE

    @classmethod
    def get_permission_manager(cls):
        """Returns the payment operation manager"""
        pm = get_utility(IPermissionManager, None)

        if not pm:
            pm = PermissionManager()
            provide_utility(IPermissionManager, pm)
        return pm
