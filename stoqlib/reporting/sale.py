# -*- coding: utf-8 -*-
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s):  Henrique Romano         <henrique@async.com.br>
##              Evandro Miquelito       <evandro@async.com.br>
##
##
""" Sales report implementation """

from kiwi.datatypes import currency

from stoqlib.database.runtime import get_connection, get_current_branch
from stoqlib.domain.commission import CommissionView
from stoqlib.domain.sale import SaleView
from stoqlib.reporting.base.default_style import TABLE_LINE_BLANK
from stoqlib.reporting.base.tables import (ObjectTableColumn as OTC,
                                           TableColumn as TC, HIGHLIGHT_NEVER)
from stoqlib.reporting.base.flowables import RIGHT
from stoqlib.lib.validators import (get_formatted_price, format_quantity,
                                    format_phone_number,
                                    get_formatted_percentage)
from stoqlib.lib.defaults import ALL_ITEMS_INDEX
from stoqlib.reporting.template import BaseStoqReport, SearchResultsReport
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

class SaleOrderReport(BaseStoqReport):
    report_name = _("Sale Order")

    def __init__(self, filename, sale_order):
        self.sale = sale_order
        BaseStoqReport.__init__(self, filename, SaleOrderReport.report_name,
                                do_footer=True, landscape=True)
        self._identify_client()
        self.add_blank_space()
        self._setup_items_table()

    def _identify_client(self):
        if self.sale.client:
            person = self.sale.client.person
            client = person.name
        else:
            person = None
            client = _(u'No client')

        if person is not None:
            phone_number = format_phone_number(person.phone_number)
        else:
            phone_number = _(u'No phone number')

        cols = [TC('', style='Normal-Bold', width=80),
                TC('', expand=True, truncate=True),
                TC('', style='Normal-Bold', width=130), TC('', expand=True)]
        data = [[_(u'Client:'), client, _(u'Phone number:'), phone_number]]
        self.add_column_table(data, cols, do_header=False,
                              highlight=HIGHLIGHT_NEVER,
                              table_line=TABLE_LINE_BLANK)

    def _get_table_columns(self):
        # XXX Bug #2430 will improve this part
        return [OTC(_("Code"), lambda obj: obj.sellable.code,
                    truncate=True, width=100),
                OTC(_("Item"),
                    lambda obj: obj.sellable.base_sellable_info.description,
                    truncate=True, expand=True),
                OTC(_("Quantity"), lambda obj: obj.get_quantity_unit_string(),
                    width=80, align=RIGHT),
                OTC(_("Price"), lambda obj: get_formatted_price(obj.price),
                    width=90, align=RIGHT),
                OTC(_("Total"),
                    lambda obj: get_formatted_price(obj.get_total()),
                    width=100, align=RIGHT)]

    def _setup_items_table(self):
        # XXX Bug #2430 will improve this part
        items_qty = self.sale.get_items_total_quantity()
        total_value = get_formatted_price(self.sale.get_sale_subtotal())
        if items_qty > 1:
            items_text = _("%s items") % format_quantity(items_qty)
        else:
            items_text = _("%s item") % format_quantity(items_qty)
        summary = ["", "", items_text, "", total_value]
        self.add_object_table(list(self.sale.get_items()),
                              self._get_table_columns(), summary_row=summary)

    #
    # BaseReportTemplate hooks
    #

    def get_title(self):
        return (_("Sale Order on %s") % self.sale.open_date.strftime("%x"))

class SalesReport(SearchResultsReport):
    # This should be properly verified on BaseStoqReport. Waiting for
    # bug 2517
    obj_type = SaleView
    report_name = _("Sales Report")
    main_object_name = _("sales")
    filter_format_string = _("with status <u>%s</u>")

    def __init__(self, filename, sale_list, status=None, *args, **kwargs):
        self.sale_list = sale_list
        self._landscape_mode = bool(status and status == ALL_ITEMS_INDEX)
        SearchResultsReport.__init__(self, filename, sale_list,
                                     SalesReport.report_name,
                                     landscape=self._landscape_mode,
                                     *args, **kwargs)
        self._setup_sales_table()

    def _get_columns(self):
        # XXX Bug #2430 will improve this part
        person_col_width = 140
        if self._landscape_mode:
            person_col_width += 84
        columns = [OTC(_("Number"), lambda obj: obj.id, width=50,
                       align=RIGHT),
                   OTC(_("Date"), lambda obj: obj.get_open_date_as_string(),
                       width=70, align=RIGHT),
                   OTC(_("Client"),
                       data_source=lambda obj: obj.get_client_name(),
                       width=person_col_width),
                   OTC(_("Salesperson"), lambda obj: obj.salesperson_name,
                       width=person_col_width, truncate=True),
                   OTC(_("Total"), lambda obj: get_formatted_price(obj.total),
                       width=80, align=RIGHT)]
        if self._landscape_mode:
            columns.insert(-1, OTC(_("Status"),
                                   lambda obj: (obj.get_status_name()),
                                   width=80))
        return columns

    def _setup_sales_table(self):
        total = sum([sale.total
                         for sale in self.sale_list], currency(0))
        total_str = _("Total %s") % get_formatted_price(total)
        summary_row = ["", "", "", "", total_str]
        if self._landscape_mode:
            summary_row.insert(-1, "")
        self.add_object_table(self.sale_list, self._get_columns(),
                              summary_row=summary_row)


class SalesPersonReport(SearchResultsReport):
    # This should be properly verified on BaseStoqReport. Waiting for
    # bug 2517
    obj_type = CommissionView
    report_name = _("Sales")

    def __init__(self, filename, salesperson_list, salesperson_name,
                 *args, **kwargs):
        branch = get_current_branch(get_connection())
        self.salesperson_list = salesperson_list
        SalesPersonReport.main_object_name = _("sales on branch %s") % (
            branch.get_description())
        if salesperson_name is not None:
            SalesPersonReport.main_object_name = _("sales from %s "
                "on branch %s" % (salesperson_name, branch.get_description()))
        SearchResultsReport.__init__(self, filename, salesperson_list,
                                     SalesPersonReport.report_name,
                                     landscape=(salesperson_name is None),
                                     *args, **kwargs)
        self._sales_person = salesperson_name
        self._setup_sales_person_table()

    def _get_columns(self):
        columns = []
        if self._sales_person is None:
            columns.append(OTC(_("Name"), lambda obj: obj.salesperson_name,
                           expand=True, truncate=True, width=245))
        columns.extend([
            OTC(_("Code"), lambda obj: obj.code, truncate=True,
                width=60),
            OTC(_("Total Amount"), lambda obj: get_formatted_price(
                obj.get_total_amount()), truncate=True, width=105),
            OTC(_("P/A"), lambda obj: get_formatted_price(
                obj.get_payment_amount()), truncate=True, width=90),
            OTC(_("Percentage"), lambda obj: get_formatted_percentage(
                obj.commission_percentage), truncate=True,
                width=100),
            OTC(_("Value"), lambda obj: get_formatted_price(
                obj.commission_value), truncate=True, width=80),
            OTC(_("S/P"), lambda obj: format_quantity(obj.quantity_sold()),
                width=45, truncate=True)])
        return columns

    def _setup_sales_person_table(self):
        total_amount = total_payment = total_percentage = total_value = \
            total_sold = 0
        for commission_view in self.salesperson_list:
            total_amount += commission_view.get_total_amount()
            total_payment += commission_view.get_payment_amount()
            total_value += commission_view.commission_value
            total_sold += commission_view.quantity_sold()

        if total_amount > 0:
            total_percentage = total_value * 100 / total_amount
        else:
            total_percentage = 0

        summary_row = ["", _("Total:"), get_formatted_price(total_amount),
                       get_formatted_price(total_payment),
                       get_formatted_percentage(total_percentage),
                       get_formatted_price(total_value),
                       format_quantity(total_sold)]

        # salesperson_list might have multiples items that refers to the
        # same sale. This will count the right number of sales.
        sales_qty = len([s.id for s in self.salesperson_list
                                    if not s.sale_returned()])

        text = None
        if self._sales_person is not None:
            summary_row.pop(0)
            va = 0
            if total_amount:
                va = total_amount/sales_qty
            text = _("Sold value per sales %s") % (get_formatted_price(va,))
            total_sellables = sum([item.sale.get_items_total_quantity()
                for item in self.salesperson_list])

        self.add_object_table(self.salesperson_list, self._get_columns(),
                              summary_row=summary_row)

        self.add_preformatted_text(_("P/A: Payment Amount"))
        self.add_preformatted_text(_("S/P: Sellables sold per sale"))
        if text:
            self.add_preformatted_text(text)
            self.add_preformatted_text(_("Total of sales: %d" %  sales_qty))
