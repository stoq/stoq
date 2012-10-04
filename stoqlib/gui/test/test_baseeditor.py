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

from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.uitestutils import GUITest


class _TestEditorSlave(BaseEditorSlave):
    model_type = object
    on_confirm_count = 0
    on_cancel_count = 0

    def on_confirm(self):
        self.on_confirm_count += 1

    def on_cancel(self):
        self.on_cancel_count += 1

    def attach_slave(self, holder, slave):
        # mimic attach slave behaviour
        self.slaves[holder] = slave


class TestBaseEditorSlave(GUITest):
    """Tests for :class:`stoqlib.editors.baseeditor.BaseEditorSlave`"""

    @property
    def slaves(self):
        return [self.slave_a, self.slave_b, self.slave_c, self.slave_d]

    def setUp(self):
        super(TestBaseEditorSlave, self).setUp()

        self.slave_a = _TestEditorSlave(self.trans, object())
        self.slave_b = _TestEditorSlave(self.trans, object())
        self.slave_c = _TestEditorSlave(self.trans, object())
        self.slave_d = _TestEditorSlave(self.trans, object())

        # This will generate the following:
        # [A [B [C, D]]]
        self.slave_b.attach_slave('C', self.slave_c)
        self.slave_b.attach_slave('D', self.slave_d)
        self.slave_a.attach_slave('B', self.slave_b)

    def test_confirm(self):
        # none of the slaves should have on_confirm, on_cancel called yet
        for slave in self.slaves:
            self.assertEqual(slave.on_confirm_count, 0)
            self.assertEqual(slave.on_cancel_count, 0)

        self.slave_a.confirm()
        # now on_confirm should be called once
        for slave in self.slaves:
            self.assertEqual(slave.on_confirm_count, 1)
            self.assertEqual(slave.on_cancel_count, 0)

    def test_cancel(self):
        # none of the slaves should have on_confirm, on_cancel called yet
        for slave in self.slaves:
            self.assertEqual(slave.on_confirm_count, 0)
            self.assertEqual(slave.on_cancel_count, 0)

        self.slave_a.cancel()
        # now on_cancel should be called once
        for slave in self.slaves:
            self.assertEqual(slave.on_confirm_count, 0)
            self.assertEqual(slave.on_cancel_count, 1)

    def test_validate_confirm(self):
        # test each time making one slave return False on validate_confirm.
        for slave in self.slaves:
            _old_validate_confirm = slave.validate_confirm
            slave.validate_confirm = lambda: False
            self.slave_a.confirm()
            slave.validate_confirm = _old_validate_confirm
            # on_confirm should not get called on any slave here
            for slave in self.slaves:
                self.assertEqual(slave.on_confirm_count, 0)
                self.assertEqual(slave.on_cancel_count, 0)
