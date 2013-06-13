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

import datetime

import mock
import gtk

from stoqlib.api import api
from stoqlib.domain.system import SystemTable
from stoqlib.gui.dialogs.sintegradialog import SintegraDialog
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class TestSintegraDialog(GUITest):
    @mock.patch('stoqlib.gui.dialogs.sintegradialog.localtoday')
    @mock.patch('stoqlib.gui.dialogs.sintegradialog.StoqlibSintegraGenerator')
    @mock.patch('stoqlib.gui.dialogs.sintegradialog.save')
    def test_confirm(self, save, generator, localtoday):
        save.return_value = True

        value = datetime.datetime(2012, 1, 31)
        localtoday.return_value = value

        # we need to create a system table because it is used by the sintegra
        # dialog to populate the date filter
        SystemTable(updated=datetime.datetime(2012, 1, 1),
                    patchlevel=0,
                    generation=1,
                    store=self.store)
        branch = api.get_current_branch(self.store)
        branch.manager = self.create_employee()

        dialog = SintegraDialog(self.store)
        with mock.patch.object(generator, 'write'):
            self.click(dialog.ok_button)
            self.check_dialog(dialog, 'dialog-sintegra-confirm', [dialog.retval])

            self.assertEquals(save.call_count, 1)
            args, kwargs = save.call_args
            label, toplevel, filename = args
            self.assertEquals(label, _("Save Sintegra file"))
            self.assertTrue(isinstance(toplevel, gtk.Dialog))
            self.assertEquals(filename, 'sintegra-2012-01.txt')
