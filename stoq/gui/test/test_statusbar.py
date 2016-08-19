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

import gtk
from kiwi.python import Settable
import mock

from stoq.gui.shell.statusbar import StatusButton, StatusDialog
from stoq.gui.test.baseguitest import BaseGUITest
from stoq.lib.status import (ResourceStatus, ResourceStatusManager,
                             ResourceStatusAction)
from stoqlib.gui.stockicons import (STOQ_STATUS_NA,
                                    STOQ_STATUS_OK,
                                    STOQ_STATUS_WARNING,
                                    STOQ_STATUS_ERROR)


class TestStatusDialog(BaseGUITest):

    def test_create(self):
        dialog = StatusDialog()
        self.check_dialog(dialog, 'dialog-status')

    def test_handle_action(self):
        dialog = StatusDialog()
        manager = ResourceStatusManager.get_instance()

        action = ResourceStatusAction(object(), 'foo', 'bar', lambda: None,
                                      threaded=False)
        with mock.patch.object(manager, 'handle_action') as handle_action:
            dialog._handle_action(action)
            self.assertCalledOnceWith(handle_action, action)

    @mock.patch('stoq.gui.shell.statusbar.ProgressDialog')
    def test_handle_action_threaded(self, ProgressDialog):
        ProgressDialog.return_value = mock.Mock()

        dialog = StatusDialog()
        manager = ResourceStatusManager.get_instance()

        action = ResourceStatusAction(Settable(label='baz'), 'foo', 'bar',
                                      lambda: None, threaded=True)
        with mock.patch.object(manager, 'handle_action') as handle_action:
            t = mock.Mock()
            t.is_alive.return_value = False

            handle_action.return_value = t
            dialog._handle_action(action)

            self.assertCalledOnceWith(handle_action, action)
            self.assertCalledOnceWith(
                ProgressDialog,
                'Executing "bar". This might take a while...', pulse=True)


class TestStatusButton(BaseGUITest):

    def test_pixbuf(self):
        btn = StatusButton()

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
            pixbuf = btn.render_icon(stock, gtk.ICON_SIZE_MENU)
            with contextlib.nested(
                    mock.patch.object(btn, 'render_icon'),
                    mock.patch.object(btn._image, 'set_from_pixbuf')) as (ri, sfp):
                ri.return_value = pixbuf

                manager.emit('status-changed', status)

                self.assertCalledOnceWith(ri, stock, gtk.ICON_SIZE_MENU)
                self.assertCalledOnceWith(sfp, pixbuf)
