# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2007 Async Open Source <http://www.async.com.br>
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
""" Sale return implementation """

from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.reporting.report import HTMLReport


class SaleReturnReport(HTMLReport):
    """Return sales report. Show client information, returned sale and returned
       items informations
    """
    template_filename = 'return_sale/return_sale.html'
    title = _('Sale Return')
    complete_header = False
    client = None
    returned_sale = None
    returned_items = None

    def __init__(self, filename, store, client, returned_sale, returned_sale_items):
        self.client = client
        self.returned_sale = returned_sale
        self.returned_items = returned_sale_items
        HTMLReport.__init__(self, filename)

    def get_subtitle(self):
        return _(u'Sale %s') % self.returned_sale.identifier
