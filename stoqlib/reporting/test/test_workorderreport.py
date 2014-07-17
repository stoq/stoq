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
from stoqlib.reporting.workorder import (WorkOrderQuoteReport,
                                         WorkOrderReceiptReport)


class TestWorkOrderQuoteReport(ReportTest):
    def test_report(self):
        workorder = self.create_workorder(description=u'Test equipment')
        workorder.client = self.create_client()
        workorder.identifier = 666
        workorder.estimated_start = datetime.datetime(2013, 1, 1)
        workorder.estimated_finish = datetime.datetime(2013, 1, 5)
        workorder.estimated_cost = currency(299)
        workorder.quote_responsible = self.create_employee(u'Quote responsible')
        workorder.defect_reported = (
            u"Lorem ipsum dolor sit amet, consectetur adipisicing elit, "
            u"sed do eiusmod tempor incididunt ut labore et dolore magna "
            u"aliqua. Ut enim ad minim veniam, quis nostrud exercitation "
            u"ullamco laboris nisi ut aliquip ex ea commodo consequat. "
            u"Duis aute irure dolor in reprehenderit in voluptate velit "
            u"esse cillum dolore eu fugiat nulla pariatur. Excepteur sint "
            u"occaecat cupidatat non proident, sunt in culpa qui officia "
            u"deserunt mollit anim id est laborum")
        self._diff_expected(WorkOrderQuoteReport, 'workorder-quote', workorder)

        workorder.defect_detected = u"This is the defect detected"
        self._diff_expected(WorkOrderQuoteReport,
                            'workorder-detected-quote', workorder)

    def test_report_with_sale(self):
        workorder = self.create_workorder(description=u'Test equipment')
        workorder.client = self.create_client()
        workorder.identifier = 666
        workorder.estimated_start = datetime.datetime(2013, 1, 1)
        workorder.estimated_finish = datetime.datetime(2013, 1, 5)
        workorder.estimated_cost = currency(299)
        workorder.quote_responsible = self.create_employee(u'Quote responsible')
        self.create_work_order_item(order=workorder)
        workorder.sale = self.create_sale()
        workorder.defect_reported = (
            u"Lorem ipsum dolor sit amet, consectetur adipisicing elit, "
            u"sed do eiusmod tempor incididunt ut labore et dolore magna "
            u"aliqua. Ut enim ad minim veniam, quis nostrud exercitation "
            u"ullamco laboris nisi ut aliquip ex ea commodo consequat. "
            u"Duis aute irure dolor in reprehenderit in voluptate velit "
            u"esse cillum dolore eu fugiat nulla pariatur. Excepteur sint "
            u"occaecat cupidatat non proident, sunt in culpa qui officia "
            u"deserunt mollit anim id est laborum")
        self._diff_expected(WorkOrderQuoteReport,
                            'workorder-with-sale-quote', workorder)

        workorder.defect_detected = u"This is the defect detected"
        self._diff_expected(WorkOrderQuoteReport,
                            'workorder-reported-with-sale-quote', workorder)


class TestWorkOrderReceiptReport(ReportTest):
    def test_report(self):
        workorder = self.create_workorder(description=u'Test equipment')
        workorder.client = self.create_client()
        workorder.identifier = 666
        workorder.approval_date = datetime.datetime(2013, 1, 1)
        workorder.finish_date = datetime.datetime(2013, 1, 5)
        workorder.execution_responsible = self.create_employee(u'Quote responsible')
        for description, quantity, price in [
                (u'Product A', 2, 20),
                (u'Product B', 1, 500),
                (u'Product C', 5, 10)]:
            workorder.add_sellable(self.create_sellable(description=description),
                                   quantity=quantity, price=price)

        self._diff_expected(WorkOrderReceiptReport,
                            'workorder-receipt', workorder)
