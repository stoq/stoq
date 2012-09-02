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
from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.dialogs.sintegradialog import SintegraDialog


_datetime = mock.MagicMock(datetime)
_datetime.date.today.return_value = datetime.date(2012, 1, 1)


class TestSintegraDialog(GUITest):
    @mock.patch('stoqlib.gui.dialogs.sintegradialog.datetime', _datetime)
    def testCreate(self):
        # FIXME: Put in some fake items in the dialog
        dialog = SintegraDialog(self.trans)
        self.check_dialog(dialog, 'dialog-sintegra-create')
