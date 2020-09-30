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

import contextlib

from gi.repository import Gtk
from stoqlib.lib.objutils import Settable
import mock

from stoq.gui.shell.statusbar import StatusButton, StatusPopover, ResourceStatusBox
from stoq.gui.test.baseguitest import BaseGUITest
from stoq.lib.status import ResourceStatus, ResourceStatusManager, ResourceStatusAction
from stoq.lib.gui.stockicons import (STOQ_STATUS_NA, STOQ_STATUS_OK,
                                     STOQ_STATUS_WARNING, STOQ_STATUS_ERROR)


class TestStatusPopover(BaseGUITest):

    def test_create(self):
        popover = StatusPopover()
        popover  # pyflakes
        # This is giving different results on jenkins and locally
        # self.check_dialog(popover, 'dialog-status')


class TestStatusBox(BaseGUITest):

    def test_resource_boxes(self):
        action = ResourceStatusAction(object(), 'foo', 'bar', lambda: None,
                                      threaded=False)
        resource = mock.MagicMock(status=0, name='mock', label='Mock', reason='Reason',
                                  reason_long=None)
        resource.get_actions.return_value = [action]
        manager = ResourceStatusManager.get_instance()

        # Compact
        box = ResourceStatusBox(resource, manager, compact=True)
        box.update_ui()
        self.check_widget(box, 'status-box-resource-compact')

        # Normal
        box = ResourceStatusBox(resource, manager, compact=False)
        box.update_ui()
        self.check_widget(box, 'status-box-resource-not-compact')

        # Long reason
        resource.long_reason = 'Long reason'
        box = ResourceStatusBox(resource, manager, compact=False)
        box.update_ui()
        self.check_widget(box, 'status-box-resource-long-reason')

        # Running
        manager.running_action = action
        box = ResourceStatusBox(resource, manager)
        box.update_ui()
        self.check_widget(box, 'status-box-resource-running')
        manager.running_action = None

        # admin user
        action.admin_only = True
        box = ResourceStatusBox(resource, manager)
        box._is_admin = False
        box.update_ui()
        self.check_widget(box, 'status-box-resource-admin')

    def test_handle_action(self):
        resource = mock.MagicMock(status=0, name='mock', label='Mock', reason='Reason',
                                  reason_long='Long reason')
        manager = ResourceStatusManager.get_instance()
        box = ResourceStatusBox(resource, manager)

        action = ResourceStatusAction(object(), 'foo', 'bar', lambda: None,
                                      threaded=False)
        btn = box.add_action(action)
        with mock.patch.object(manager, 'handle_action') as handle_action:
            self.click(btn)
            self.assertCalledOnceWith(handle_action, action)

    @mock.patch('stoq.gui.shell.statusbar.ProgressDialog')
    def test_handle_action_threaded(self, ProgressDialog):
        ProgressDialog.return_value = mock.Mock()

        resource = mock.MagicMock(status=0, name='mock', label='Mock', reason='Reason',
                                  reason_long='Long reason')
        manager = ResourceStatusManager.get_instance()
        box = ResourceStatusBox(resource, manager)

        action = ResourceStatusAction(Settable(label='baz'), 'foo', 'bar',
                                      lambda: None, threaded=True)
        btn = box.add_action(action)
        with mock.patch.object(manager, 'handle_action') as handle_action:
            t = mock.Mock()
            t.is_alive.side_effect = [True, False]

            handle_action.return_value = t
            self.click(btn)

            self.assertCalledOnceWith(handle_action, action)
            self.assertCalledOnceWith(
                ProgressDialog,
                'Executing "bar". This might take a while...', pulse=True)


class TestStatusButton(BaseGUITest):

    def test_pixbuf(self):
        btn = StatusButton()

        icon_map = {
            ResourceStatus.STATUS_NA: 'stoq-status-na',
            ResourceStatus.STATUS_OK: 'stoq-status-ok',
            ResourceStatus.STATUS_WARNING: 'stoq-status-warning',
            ResourceStatus.STATUS_ERROR: 'stoq-status-error',
        }

        manager = ResourceStatusManager.get_instance()
        for status, stock in [
                (ResourceStatus.STATUS_NA,
                 STOQ_STATUS_NA),
                (ResourceStatus.STATUS_OK,
                 STOQ_STATUS_OK),
                (ResourceStatus.STATUS_WARNING,
                 STOQ_STATUS_WARNING),
                (ResourceStatus.STATUS_ERROR,
                 STOQ_STATUS_ERROR)]:
            with contextlib.nested(
                    mock.patch.object(btn._image, 'set_from_icon_name')) as (sfp,):
                manager.emit('status-changed', status)
                self.assertCalledOnceWith(sfp, icon_map[status], Gtk.IconSize.MENU)
