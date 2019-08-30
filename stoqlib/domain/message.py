# -* coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2018 Async Open Source <http://www.async.com.br>
## All rights reserved
##
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
"""Messaging domain
"""

from storm.expr import And, Coalesce, Join, LeftJoin
from storm.references import Reference

from stoqlib.database.properties import UnicodeCol, IdCol, DateTimeCol
from stoqlib.database.viewable import Viewable
from stoqlib.domain.base import Domain
from stoqlib.domain.person import Person, LoginUser, Branch
from stoqlib.lib.dateutils import localnow
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class Message(Domain):
    """A message that will be displayed at the launcher screen.
    """
    __storm_table__ = 'message'

    #: The content of the message
    content = UnicodeCol(default=u'')

    #: When this message was created
    created_at = DateTimeCol(default_factory=localnow)

    #: Until when this message will be shown
    expire_at = DateTimeCol()

    created_by_id = IdCol(default=None)
    #: The user that created this message
    created_by = Reference(created_by_id, 'LoginUser.id')

    branch_id = IdCol()
    #: the branch this message will be displayed at
    branch = Reference(branch_id, 'Branch.id')

    profile_id = IdCol()
    #: the user this message will be displayed to
    profile = Reference(profile_id, 'UserProfile.id')

    user_id = IdCol()
    #: the user profile this message will be displayed to
    user = Reference(user_id, 'LoginUser.id')

    @classmethod
    def find_active(cls, store, branch: Branch, user: LoginUser):
        profile = user.profile
        now = localnow()
        query = And(
            # All fields are optional, so default to the current user (or now) if they are missing
            Coalesce(cls.expire_at, now) >= now,
            Coalesce(cls.branch_id, branch.id) == branch.id,
            Coalesce(cls.user_id, user.id) == user.id,
            Coalesce(cls.profile_id, profile.id) == profile.id,
        )
        return store.find(cls, query)


class MessageView(Viewable):
    message = Message

    id = Message.id
    content = Message.content
    created_at = Message.created_at
    expire_at = Message.expire_at
    creator_name = Person.name

    tables = [
        Message,
        Join(LoginUser, LoginUser.id == Message.created_by_id),
        Join(Person, Person.id == LoginUser.person_id),
        LeftJoin(Branch, Branch.id == Message.branch_id),
    ]
