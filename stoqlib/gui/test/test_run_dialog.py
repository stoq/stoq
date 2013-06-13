# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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

import mock

from stoqlib.gui.base.dialogs import run_dialog, get_dialog
from stoqlib.gui.dialogs.paymentcategorydialog import PaymentCategoryDialog
from stoqlib.gui.events import RunDialogEvent
from stoqlib.gui.test.uitestutils import GUITest


class TestRunDialog(GUITest):

    def test_run_dialog_event(self):
        self.event_call_count = 0

        def _run_dialog_event(dialog, parent, *args, **kwargs):
            self.event_call_count += 1
            return None

        RunDialogEvent.connect(_run_dialog_event)
        fake_run = mock.Mock()

        # The real get dialog returns an instance of the given class, and then,
        # run_dialog calls the method run() on the toplevel of the instance. We
        def _get_dialog(*args, **kwargs):
            real_dialog = get_dialog(*args, **kwargs)
            toplevel = real_dialog.get_current_toplevel()
            toplevel.run = fake_run
            return real_dialog

        with mock.patch('stoqlib.gui.base.dialogs.get_dialog', new=_get_dialog):
            run_dialog(PaymentCategoryDialog, parent=None, store=self.store)

        fake_run.assert_called_once_with()
        self.assertEquals(self.event_call_count, 1)
