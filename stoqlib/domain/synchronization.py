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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" BranchSynchronization domain class """

from stoqlib.database.orm import DateTimeCol, ForeignKey, StringCol
from stoqlib.database.orm import ORMObject
from stoqlib.domain.person import PersonAdaptToBranch

PersonAdaptToBranch # pyflakes


class BranchSynchronization(ORMObject):
    """Created once per branch. Contains a string which is a reference to a policy
    defined in stoqlib.database.policy and a timestamp which is updated each
    time a synchronization is done.

    @cvar timestamp: last time updated
    @cvar branch: a branch
    @cvar policy: policy used to update the branch
    """
    sync_time = DateTimeCol(notNone=True)
    branch = ForeignKey('PersonAdaptToBranch', unique=True)
    policy = StringCol(notNone=True)
