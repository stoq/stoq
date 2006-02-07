# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):    Henrique Romano            <henrique@async.com.br>
##
""" Sales report implementation """

import gettext
from datetime import datetime

from stoqlib.reporting.tables import ObjectTableColumn as OTC
from stoqlib.reporting.flowables import RIGHT

from stoq.report.template import BaseStoqReport
from stoqlib.lib.validators import (get_formatted_price, format_quantity,
                                 format_phone_number)
from stoqlib.lib.parameters import sysparam
from stoqlib.domain.sellable import AbstractSellableItem

_ = gettext.gettext

class SaleOrderReport(BaseStoqReport):
    report_name = "Sale Order"

    def __init__(self, filename, sale_order):
        self.order = sale_order
        BaseStoqReport.__init__(self, filename, SaleOrderReport.report_name,
                                do_footer=True)
        self._identify_client()
        self.add_blank_space()
        self._setup_items_table()

    def _identify_client(self):
        if not self.order.client:
            return
        person = self.order.client.get_adapted()
        text = "<b>%s:</b> %s" % (_("Client"), person.name)
        if person.phone_number:
            phone_str = ("<b>%s:</b> %s" %
                         (_("Phone"), format_phone_number(person.phone_number)))
            text += " %s" % phone_str
        self.add_paragraph(text)

    def _get_table_columns(self):
        # XXX Bug #2430 will improve this part
        return [OTC(_("Code"), lambda obj: obj.sellable.code, width=50),
                OTC(_("Item"),
                    lambda obj: obj.sellable.base_sellable_info.description,
                    width=180),
                OTC(_("Quantity"), lambda obj: format_quantity(obj.quantity),
                    width=50, align=RIGHT),
                OTC(_("Price"), lambda obj: get_formatted_price(obj.price),
                    width=100, align=RIGHT),
                OTC(_("Total"),
                    lambda obj: get_formatted_price(obj.get_total()),
                    width=100, align=RIGHT)]

    def _setup_items_table(self):
        # XXX Bug #2430 will improve this part
        items_qty = self.order.get_items_total_quantity()
        total_value = get_formatted_price(self.order.get_items_total_value())
        if items_qty > 1.0:
            items_text = _("%s items") % format_quantity(items_qty)
        else:
            items_text = ("%s item") % format_quantity(items_qty)
        summary = ["", "", items_text, "", total_value]
        self.add_object_table(list(self.order.get_items()),
                              self._get_table_columns(), summary_row=summary)

    #
    # BaseReportTemplate hooks
    #

    def get_title(self):
        return (_("Sale Order on %s with due date of %d days")
                % (self.order.open_date.strftime("%x"),
                   sysparam(self.conn).MAX_SALE_ORDER_VALIDITY))
