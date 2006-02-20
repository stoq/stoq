# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
##  Author(s):  Henrique Romano         <henrique@async.com.br>
##
##
""" Sales report implementation """

import gettext

from kiwi.datatypes import currency

from stoqlib.reporting.base.tables import ObjectTableColumn as OTC
from stoqlib.reporting.base.flowables import RIGHT
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.validators import (get_formatted_price, format_quantity,
                                    format_phone_number)
from stoqlib.reporting.template import BaseStoqReport
from stoqlib.domain.sale import Sale

_ = gettext.gettext

class SaleOrderReport(BaseStoqReport):
    report_name = _("Sale Order")

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
                    truncate=True, width=160),
                OTC(_("Quantity"), lambda obj: format_quantity(obj.quantity),
                    width=70, align=RIGHT),
                OTC(_("Price"), lambda obj: get_formatted_price(obj.price),
                    width=100, align=RIGHT),
                OTC(_("Total"),
                    lambda obj: get_formatted_price(obj.get_total()),
                    width=100, align=RIGHT)]

    def _setup_items_table(self):
        # XXX Bug #2430 will improve this part
        items_qty = self.order.get_items_total_quantity()
        total_value = get_formatted_price(self.order.get_items_total_value())
        if items_qty > 1:
            items_text = _("%s items") % format_quantity(items_qty)
        else:
            items_text = _("%s item") % format_quantity(items_qty)
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

class SalesReport(BaseStoqReport):
    report_name = _("Sales Report")

    def __init__(self, filename, sale_list, start_date=None, end_date=None,
                 status=None, extra_filters=None, blocked_results_qty=None):
        self.sale_list = sale_list
        self.start_date = start_date
        self.extra_filters = extra_filters
        self.end_date = end_date
        self.status = status
        self._blocked_results_qty = blocked_results_qty
        if status is None or status not in Sale.statuses:
            self._landscape_mode = True
        else:
            self._landscape_mode = False
        BaseStoqReport.__init__(self, filename, SalesReport.report_name,
                                do_foote=True, landscape=self._landscape_mode)
        self._setup_sales_table()

    def _get_columns(self):
        # XXX Bug #2430 will improve this part
        person_col_width = 140
        if self._landscape_mode:
            person_col_width += 84
        columns = [OTC(_("Number"), lambda obj: obj.order_number, width=50,
                       align=RIGHT),
                   OTC(_("Date"), lambda obj: obj.open_date.strftime("%x"),
                       width=70, align=RIGHT),
                   OTC(_("Client"),
                       data_source=lambda obj: (obj.client.get_name()),
                       width=person_col_width),
                   OTC(_("Salesperson"),
                       lambda obj: (obj.salesperson.get_adapted().name),
                       width=person_col_width, truncate=True),
                   OTC(_("Total"),
                       lambda obj: (obj.get_total_amount_as_string()),
                       width=80, align=RIGHT)]
        if self._landscape_mode:
            columns.insert(-1, OTC(_("Status"),
                                   lambda obj: (obj.get_status_name()),
                                   width=80))
        return columns

    def _setup_sales_table(self):
        total = sum([sale.get_total_sale_amount()
                         for sale in self.sale_list], currency(0))
        total_str = "Total %s" % get_formatted_price(total)
        summary_row = ["", "", "", "", total_str]
        if self._landscape_mode:
            summary_row.insert(-1, "")
        self.add_object_table(self.sale_list, self._get_columns(),
                              summary_row=summary_row)

    #
    # BaseReportTemplate hooks
    #

    def get_title(self):
        title = _("Sales Report")
        if self._blocked_results_qty is not None:
            title += " - %s " % _("Listing")
            if self._blocked_results_qty > 0:
                rows_qty = len(self.sale_list)
                title += (_("%d of a total of %d sales")
                          % (rows_qty, rows_qty + self._blocked_results_qty))
            else:
                title += _("all sales")
        notes = ""
        if self.status is not None:
            try:
                status_name = Sale.statuses[self.status].lower()
                notes += _("with status %s ") % ("<u>%s</u>" % status_name)
            except KeyError:
                pass
        if self.extra_filters:
            notes += " %s " % _("matching \"%s\"") % self.extra_filters
        if self.start_date:
            if self.end_date:
                notes += (_("between %s and %s")
                          % (self.start_date.strftime("%x"),
                             self.end_date.strftime("%x")))
            else:
                notes += _("and since %s") % self.start_date.strftime("%x")
        elif self.end_date:
            notes += (_("and until %s") % self.end_date.strftime("%x"))
        if notes:
            notes = "%s %s" % (_("Sales"), notes)
        return (title, notes)
