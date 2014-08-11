# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2014 Async Open Source <http://www.async.com.br>
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

import logging


from stoqlib.gui.events import PrintReportEvent
from stoqlib.gui.utils.printing import print_report
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.workorder import WorkOrderQuoteReport

from .bikeshopreport import BikeShopWorkOrderQuoteReport


_ = stoqlib_gettext
log = logging.getLogger(__name__)


class BikeShopUI(object):

    def __init__(self):
        PrintReportEvent.connect(self._on_PrintReportEvent)

    #
    # Events
    #

    def _on_PrintReportEvent(self, report_class, *args, **kwargs):
        if report_class is WorkOrderQuoteReport:
            print_report(BikeShopWorkOrderQuoteReport, *args)
            return True
