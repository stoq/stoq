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

import mock
import datetime

from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
from stoqlib.gui.dialogs.renegotiationdetails import RenegotiationDetailsDialog
from stoqlib.gui.test.uitestutils import GUITest


class TestRenegotiationDetailsDialog(GUITest):
    @mock.patch('stoqlib.gui.dialogs.renegotiationdetails.run_dialog')
    def test_show(self, run_dialog):
        renegotiation = self.create_payment_renegotiation()
        group = self.create_payment_group()
        parent_renegotiation = self.create_payment_renegotiation(group=group)

        renegotiation.identifier = 333
        group.renegotiation = renegotiation
        parent_renegotiation.open_date = datetime.date.today()
        parent_renegotiation.identifier = 444

        dialog = RenegotiationDetailsDialog(self.store, renegotiation)
        self.check_dialog(dialog, 'dialog-renegotiation-details-show')

        self.click(dialog.details_button)

        self.assertEquals(run_dialog.call_count, 1)
        args, kwargs = run_dialog.call_args
        details_dialog, dialog, trans, client = args
        self.assertEquals(details_dialog, ClientDetailsDialog)
        self.assertTrue(isinstance(dialog, RenegotiationDetailsDialog))
        self.assertEquals(client, renegotiation.client)
