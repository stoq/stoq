# -*- Mode: Python; coding: utf-8 -*-
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

from stoqlib.gui.events import PrintReportEvent
from stoqlib.reporting.workorder import WorkOrderQuoteReport
from stoq.gui.test.baseguitest import BaseGUITest

from ..bikeshopreport import BikeShopWorkOrderQuoteReport
from ..bikeshopui import BikeShopUI


class TestBikeShopUi(BaseGUITest):

    @mock.patch('plugins.bikeshop.bikeshopui.print_report')
    def test_print_report_event(self, print_report):
        # We need the UI for the events setup
        ui = BikeShopUI()

        # We need to save this in a variable, even though we dont use it,
        # otherwise the callback will not be triggered, since it is a weakref
        ui  # pyflakes

        # Emitting with something different from WorkOrderQuoteReport
        rv = PrintReportEvent.emit(object)
        self.assertFalse(rv)
        self.assertEquals(print_report.call_count, 0)

        # Emitting with a WorkOrderQuoteReport
        order = self.create_workorder()
        rv = PrintReportEvent.emit(WorkOrderQuoteReport, order)
        self.assertTrue(rv)
        print_report.assert_called_once_with(BikeShopWorkOrderQuoteReport,
                                             order)
