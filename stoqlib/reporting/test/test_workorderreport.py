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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

import datetime

from kiwi.currency import currency

from stoqlib.reporting.test.reporttest import ReportTest
from stoqlib.reporting.workorder import WorkOrderQuoteReport


class TestWorkOrderQuoteReport(ReportTest):
    def testReport(self):
        workorder = self.create_workorder(u'Test equipment')
        workorder.client = self.create_client()
        workorder.identifier = 666
        workorder.estimated_start = datetime.datetime(2013, 1, 1)
        workorder.estimated_finish = datetime.datetime(2013, 1, 5)
        workorder.estimated_cost = currency(299)
        workorder.quote_responsible = self.create_user(u'Quote responsible')
        workorder.defect_detected = (
            u"Lorem ipsum dolor sit amet, consectetur adipisicing elit, "
            u"sed do eiusmod tempor incididunt ut labore et dolore magna "
            u"aliqua. Ut enim ad minim veniam, quis nostrud exercitation "
            u"ullamco laboris nisi ut aliquip ex ea commodo consequat. "
            u"Duis aute irure dolor in reprehenderit in voluptate velit "
            u"esse cillum dolore eu fugiat nulla pariatur. Excepteur sint "
            u"occaecat cupidatat non proident, sunt in culpa qui officia "
            u"deserunt mollit anim id est laborum")

        self._diff_expected(WorkOrderQuoteReport, 'workorder-quote', workorder)
