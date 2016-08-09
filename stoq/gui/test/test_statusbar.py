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

from stoq.gui.shell.statusbar import StatusButton, StatusDialog
from stoq.gui.test.baseguitest import BaseGUITest
from stoq.lib.status import ResourceStatus, ResourceStatusManager


class TestStatusButton(BaseGUITest):

    def test_label(self):
        btn = StatusButton()
        self.assertEqual(btn.get_label(), "Checking status...")

        manager = ResourceStatusManager.get_instance()
        for status, text in [
                (ResourceStatus.STATUS_OK,
                 u"Everything is running fine"),
                (ResourceStatus.STATUS_WARNING,
                 u"Some services are in a warn\u2026"),
                (ResourceStatus.STATUS_ERROR,
                 u"Some services are in an err\u2026")]:
            manager.emit('status-changed', status)
            self.assertEqual(btn.get_label(), text)


class TestStatusDialog(BaseGUITest):

    def test_create(self):
        dialog = StatusDialog()
        self.check_dialog(dialog, 'dialog-status')
