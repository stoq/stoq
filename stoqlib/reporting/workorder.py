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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

"""Work order reports implementation"""

from stoqlib.reporting.report import ObjectListReport, HTMLReport
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class WorkOrdersReport(ObjectListReport):
    title = _("Work orders report")
    main_object_name = (_("work order"), _("work orders"))
    filter_format_string = _("with status <u>%s</u>")
    summary = ['total']


class _BaseWorkOrderReport(HTMLReport):
    title = _("Work order")
    complete_header = True

    def __init__(self, filename, workorder):
        self.workorder = workorder
        self.subtitle = (_("Order number: %s") %
                         self.workorder.identifier)

        super(_BaseWorkOrderReport, self).__init__(filename)


class WorkOrderQuoteReport(_BaseWorkOrderReport):
    template_filename = "workorder/quote.html"


class WorkOrderReceiptReport(_BaseWorkOrderReport):
    template_filename = "workorder/receipt.html"


if __name__ == '__main__':  # pragma nocover
    from stoqlib.api import api
    from stoqlib.domain.workorder import WorkOrder
    import sys
    creator = api.prepare_test()
    wo = creator.store.find(WorkOrder, identifier=int(sys.argv[-1])).one()
    r = WorkOrderQuoteReport('test.pdf', wo)
    r.save_html('test.html')
    r.save()
