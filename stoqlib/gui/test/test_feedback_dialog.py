# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

import mock

from stoqlib.gui.dialogs.feedbackdialog import FeedbackDialog
from stoqlib.gui.test.uitestutils import GUITest


class TestFeedabackDialog(GUITest):
    @mock.patch('stoqlib.gui.dialogs.feedbackdialog.WebService.feedback')
    def test_confirm(self, feedback):
        dialog = FeedbackDialog()

        dialog.email.update('foo@bar.com')
        dialog.feedback.update('feedback')

        self.click(dialog.main_dialog.ok_button)
        self.check_dialog(dialog, 'dialog-feedback-confirm')

        feedback.assert_called_once_with(None, 'foo@bar.com', 'feedback')
