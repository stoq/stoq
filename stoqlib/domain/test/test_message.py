# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

#
# Copyright (C) 2018 Async Open Source <http://www.async.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
# Author(s): Stoq Team <stoq-devel@async.com.br>
#

__tests__ = 'stoqlib/domain/message.py'

from stoqlib.domain.message import Message
from stoqlib.domain.test.domaintest import DomainTest


class TestMessage(DomainTest):

    def test_find_active(self):
        user = self.create_user()
        # No messages yet.
        self.assertEqual(Message.find_active(self.store, self.current_branch,
                                             self.current_user).count(), 0)

        # One global message
        msg = Message(store=self.store, created_by=user, content='global')
        messages = set(Message.find_active(self.store, self.current_branch, self.current_user))
        self.assertEqual(messages, set([msg]))
