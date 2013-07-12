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

# pylint: enable=E1101

from storm.references import Reference
from storm.store import AutoReload

from stoqlib.database.orm import ORMObject
from stoqlib.database.properties import DateTimeCol, IntCol, UnicodeCol, IdCol
from stoqlib.domain.person import Branch

Branch  # pylint: disable=W0104


class BranchSynchronization(ORMObject):
    """Created once per branch. Contains a string which is a reference to a policy
    defined in stoqlib.database.policy and a timestamp which is updated each
    time a synchronization is done.
    """

    __storm_table__ = 'branch_synchronization'

    id = IntCol(primary=True, default=AutoReload)

    #: last time updated
    sync_time = DateTimeCol(allow_none=False)

    branch_id = IdCol()

    #: a |branch|
    branch = Reference(branch_id, 'Branch.id')

    #: policy used to update the branch
    policy = UnicodeCol(allow_none=False)
