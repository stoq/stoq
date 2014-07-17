# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import datetime

from stoqlib.reporting.test.reporttest import ReportTest
from stoqlib.lib.dateutils import localdate

from ..opticalreport import OpticalWorkOrderReceiptReport
from .test_optical_domain import OpticalDomainTest


class OpticalReportTest(ReportTest, OpticalDomainTest):

    def test_optical_report_with_sale(self):
        sellable = self.create_sellable()
        client = self.create_client(u'Juca')
        sale = self.create_sale(client=client)
        sale.identifier = 23456
        sale.open_date = localdate(2012, 1, 1)
        sale.salesperson = self.create_sales_person()
        sale_item = sale.add_sellable(sellable)

        payment = self.add_payments(sale)[0]
        payment.set_pending()
        payment.pay()

        workorders = []
        opt_wo = self.create_optical_work_order()
        opt_wo.patient = u'A'
        wo_item = self.create_work_order_item(order=opt_wo.work_order)
        wo_item.sale_item = sale_item

        wo = opt_wo.work_order
        wo.equipament = u'Equipamento 1'
        wo.identifier = 12345
        wo.client = client
        wo.sale = sale
        wo.branch = sale.branch
        wo.open_date = datetime.date(2012, 1, 1)
        wo.estimated_finish = datetime.date(2013, 1, 1)
        workorders.append(wo)

        opt_wo = self.create_optical_work_order()
        opt_wo.patient = u'B'
        wo = opt_wo.work_order
        wo.equipament = u'Equipamento 2'
        wo.identifier = 113
        wo.client = client
        wo.sale = sale
        wo.branch = sale.branch
        wo.open_date = datetime.date(2012, 1, 1)
        wo.estimated_finish = datetime.date(2013, 1, 9)
        workorders.append(wo)

        self._diff_expected(OpticalWorkOrderReceiptReport,
                            'optical-work-order-receipt-report',
                            workorders)

    def test_optical_report_without_sale(self):
        branch = self.create_branch()
        client = self.create_client(u'Juca')

        opt_wo = self.create_optical_work_order()
        wo = opt_wo.work_order
        wo.equipament = u'Equipamento 1'
        wo.identifier = 12345
        wo.open_date = datetime.date(2012, 1, 1)
        wo.client = client
        wo.branch = branch

        self._diff_expected(OpticalWorkOrderReceiptReport,
                            'optical-work-order-without-sale-receipt-report',
                            [opt_wo.work_order])
