# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010-2014 Async Open Source <http://www.async.com.br>
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

""" A Manual stock decrease receipt implementation """

from stoqlib.api import api
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.report import HTMLReport, ObjectListReport

_ = stoqlib_gettext


class StockDecreaseReceipt(HTMLReport):
    template_filename = 'stock_decrease/stock_decrease.html'
    title = _("Manual Stock Decrease Receipt")
    complete_header = False

    def __init__(self, filename, order):
        self.order = order
        self.payments = api.sysparam.get_bool("CREATE_PAYMENTS_ON_STOCK_DECREASE")
        HTMLReport.__init__(self, filename)

    def get_subtitle(self):
        return ""


class _StockDecreaseReceipt():
    def __init__(self, filename, order, *args, **kwargs):
        self._add_signatures()

    def _add_signatures(self):
        self.add_signatures([_(u"Responsible"), _(u'Removed By')])


class StockDecreaseReport(ObjectListReport):
    title = _("Stock decrease report")
    main_object_name = (_("stock decrease"), _("stock decreases"))
