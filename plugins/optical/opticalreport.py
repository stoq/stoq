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

from stoqlib.domain.payment.payment import Payment
from stoqlib.reporting.report import HTMLReport
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class OpticalWorkOrderReceiptReport(HTMLReport):
    title = _("Work order")
    template_filename = "optical/optical.html"
    complete_header = True

    def __init__(self, filename, workorders):
        self.workorders = workorders
        self.workorder_items = []

        # The workorders are always from the same sale.
        self.sale = workorders[0].sale
        if self.sale:
            self.subtitle = _("Sale number: %s") % self.sale.identifier
        else:
            assert len(workorders) == 1
            self.subtitle = _("Work order: %s") % self.workorders[0].identifier

        self.method_summary = {}
        if self.sale:
            payments = self.sale.payments
            for payment in payments.find(Payment.status == Payment.STATUS_PAID):
                self.method_summary.setdefault(payment.method, 0)
                self.method_summary[payment.method] += payment.value
            for order in workorders:
                self.workorder_items.extend(order.get_items())

        super(OpticalWorkOrderReceiptReport, self).__init__(filename)

    def get_optical_data(self, workorder):
        from optical.opticaldomain import OpticalWorkOrder
        store = self.workorders[0].store
        return store.find(OpticalWorkOrder, work_order=workorder).one()


def test():  # pragma nocover
    from stoqlib.domain.workorder import WorkOrder
    from stoqlib.api import api
    creator = api.prepare_test()
    orders = creator.store.find(WorkOrder)
    r = OpticalWorkOrderReceiptReport('teste.pdf', orders)
    #r.save_html('teste.html')
    r.save()

if __name__ == '__main__':  # pragma nocover
    test()
