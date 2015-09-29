# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2014 Async Open Source <http://www.async.com.br>
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
import gtk

from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.base.wizards import BaseWizard, BaseWizardStep


class _FakeStep(BaseWizardStep):
    gladefile = 'HolderTemplate'


class TestBaseWizard(GUITest):
    @mock.patch('stoqlib.gui.base.wizards.yesno')
    def test_cancel_confirmation_close(self, yesno):
        step = _FakeStep(self.store, None)
        wizard = BaseWizard(self.store, step, title="Fake")

        # need_cancel_confirmation is False, cancel should close the wizard
        with mock.patch.object(wizard, 'close') as close:
            wizard.cancel()
            self.assertEquals(yesno.call_count, 0)
            self.assertEquals(close.call_count, 1)

        wizard.need_cancel_confirmation = True

        # need_cancel_confirmation is True but there're no changes. Cancel
        # should still close the dialog
        with mock.patch.object(wizard, 'close') as close:
            wizard.cancel()
            self.assertEquals(yesno.call_count, 0)
            self.assertEquals(close.call_count, 1)

        # Just to make store.get_pending_changes return something greater
        # thant the time the wizard was created
        self.create_sellable()

        yesno.return_value = True
        # need_cancel_confirmation is True and there're changes. yesno
        # should ask if we can close the wizard or not and since we are
        # answering True, it should still close
        with mock.patch.object(wizard, 'close') as close:
            wizard.cancel()
            yesno.assert_called_once_with(
                ("If you cancel this dialog all changes will be "
                 "lost. Are you sure?"),
                gtk.RESPONSE_NO, "Cancel", "Don't cancel")
            self.assertEquals(close.call_count, 1)

        yesno.reset_mock()
        yesno.return_value = False
        # need_cancel_confirmation is True and there're changes. yesno
        # should ask if we can close the wizard or not and since we are
        # answering False, it should not close
        with mock.patch.object(wizard, 'close') as close:
            wizard.cancel()
            yesno.assert_called_once_with(
                ("If you cancel this dialog all changes will be "
                 "lost. Are you sure?"),
                gtk.RESPONSE_NO, "Cancel", "Don't cancel")
            self.assertEquals(close.call_count, 0)
