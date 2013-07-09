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

from stoqlib.database.runtime import get_current_station
from stoqlib.gui.editors.invoiceeditor import InvoicePrinterEditor
from stoqlib.gui.test.uitestutils import GUITest


class TestInvoicePrinterEditor(GUITest):
    @mock.patch('stoqlib.gui.editors.invoiceeditor.BranchStation.get_active_stations')
    def test_create(self, select):
        # Station names change depending on the computer running the test. Make
        # sure only one station is in the list, and that the name is always de
        # same
        station = get_current_station(self.store)
        station.name = u'Test station'
        select.return_value = [station]
        editor = InvoicePrinterEditor(self.store)
        self.check_editor(editor, 'editor-invoiceprinter-create')
