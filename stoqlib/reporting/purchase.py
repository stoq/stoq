# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2008 Async Open Source <http://www.async.com.br>
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
""" Purchase report implementation """

from decimal import Decimal

from kiwi.datatypes import currency

from stoqlib.reporting.base.tables import (ObjectTableColumn as OTC,
                                           TableColumn as TC,
                                           HIGHLIGHT_NEVER)
from stoqlib.reporting.base.flowables import RIGHT, LEFT
from stoqlib.reporting.base.default_style import TABLE_LINE_BLANK
from stoqlib.lib.validators import get_formatted_price, format_quantity
from stoqlib.lib.defaults import ALL_ITEMS_INDEX
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.template import SearchResultsReport, BaseStoqReport
from stoqlib.domain.purchase import PurchaseOrder, PurchaseOrderView

_ = stoqlib_gettext


class PurchaseReport(SearchResultsReport):
    report_name = _("Purchase Order Report")
    main_object_name = _("orders")
    filter_format_string = _("with status <u>%s</u>")
    # This should be properly verified on SearchResultsReport. Waiting for
    # bug 2517
    obj_type = PurchaseOrderView

    def __init__(self, filename, purchases, status, *args, **kwargs):
        self.show_status_column = status == ALL_ITEMS_INDEX
        self._purchases = purchases
        SearchResultsReport.__init__(self, filename, purchases,
                                     PurchaseReport.report_name,
                                     landscape=1, *args, **kwargs)
        self._setup_table()

    def _get_columns(self):
        # XXX Bug #2430 will improve this part
        columns = [OTC(_("Number"), lambda obj: obj.id,
                       width=60, align=RIGHT),
                   OTC(_("Date"), lambda obj: obj.get_open_date_as_string(),
                       width=70),
                   OTC(_("Supplier"), lambda obj: obj.supplier_name,
                       width=250, truncate=True),
                   OTC(_("Qty Ordered"),
                       lambda obj: format_quantity(obj.ordered_quantity),
                       width=90, align=RIGHT),
                   OTC(_("Qty Received"),
                       lambda obj: format_quantity(obj.received_quantity),
                       width=120, align=RIGHT),
                   OTC(_("Total"),
                       lambda obj: get_formatted_price(obj.total),
                       width=85, align=RIGHT)]
        if self.show_status_column:
            columns.insert(-4, OTC(_("Status"),
                                   lambda obj: obj.get_status_str(), width=80))
        return columns

    def _setup_table(self):
        totals = [(purchase.ordered_quantity, purchase.received_quantity,
                   purchase.total)
                      for purchase in self._purchases]
        ordered, received , total = zip(*totals)
        total_ordered, total_received, total = (sum(ordered, Decimal(0)),
                                                sum(received, Decimal(0)),
                                                sum(total, currency(0)))
        summary_row = ["", "", _("Totals:"), format_quantity(total_ordered),
                       format_quantity(total_received),
                       get_formatted_price(total)]
        if self.show_status_column:
            summary_row.insert(0, "")
        self.add_object_table(self._purchases, self._get_columns(),
                              summary_row=summary_row)

class PurchaseOrderReport(BaseStoqReport):
    report_name = _("Purchase Order")

    def __init__(self, filename, order):
        self._order = order
        BaseStoqReport.__init__(self, filename, PurchaseOrderReport.report_name,
                                landscape=True)
        self._setup_order_details_table()
        self.add_blank_space(10)
        self._setup_payment_group_data()
        self.add_blank_space(10)
        self._setup_items_table()

    def _get_items_table_columns(self):
        return [
            OTC(_("Item"),
                lambda obj: ("%s - %s" % (obj.sellable.id,
                                          obj.sellable.get_description())),
                expand=True, truncate=True),
            # FIXME: This column should be virtual, waiting for bug #2764
            OTC("Unit", lambda obj: obj.sellable.get_unit_description(),
                virtual=False, width=50, align=LEFT),
            OTC(_("Cost"), lambda obj: get_formatted_price(obj.cost),
                width=70, align=RIGHT),
            OTC(_("Quantity"), lambda obj: format_quantity(obj.quantity),
                width=70, align=RIGHT),
            OTC(_("Total"),
                lambda obj: get_formatted_price(obj.get_total()), width=90,
                align=RIGHT),
            OTC(_("Qty Received"), lambda obj: format_quantity(
                obj.quantity_received), width=90, align=RIGHT),
            OTC(_("Total"),
                lambda obj: get_formatted_price(obj.get_received_total()),
                width=90, align=RIGHT),
            ]
    def _add_items_table(self, items):
        total_quantity = Decimal(0)
        total_qty_received = Decimal(0)
        total_received = Decimal(0)
        total_value = Decimal(0)
        for item in items:
            total_quantity += item.quantity
            total_qty_received += item.quantity_received
            total_value += item.quantity * item.cost
            total_received += item.quantity_received * item.cost
        extra_row = ["", "", _("Totals:"), format_quantity(total_quantity),
                     get_formatted_price(total_value),
                     format_quantity(total_qty_received),
                     get_formatted_price(total_received)]
        self.add_object_table(items, self._get_items_table_columns(),
                              summary_row=extra_row)

    def _add_ordered_items_table(self, items):
        self.add_paragraph(_("Purchase Ordered Items"), style="Title")
        self._add_items_table(items)

    def _get_freight_line(self):
        freight_line = []
        transporter = self._order.get_transporter_name() or _("Not Specified")
        freight_line.extend([_("Transporter:"), transporter, _("Freight:")])
        if self._order.freight_type == PurchaseOrder.FREIGHT_FOB:
            freight_line.append("FOB (%.2f %%)" % self._order.freight)
        else:
            # transporter may be None
            freight_percentage = 0
            if self._order.transporter:
                freight_percentage = self._order.transporter.freight_percentage
            freight_line.append("CIF (%.2f %%)" % (freight_percentage,))
        return freight_line

    def _setup_payment_group_data(self):
        payments = self._order.payments
        installments_number = payments.count()
        if installments_number > 1:
            msg = (_("Payments: %d installments")
                   % (installments_number,))
        else:
            msg = _("Payments: 1 installment")
        self.add_paragraph(msg, style="Title")
        self._add_payment_table(payments)

    def _add_payment_table(self, payments):
        payment_columns = [OTC(_("#"), lambda obj: obj.id, width=40,
                               align=RIGHT),
                           OTC(_("Method"), lambda obj:
                               obj.method.get_description(), width=70),
                           OTC(_("Description"), lambda obj: obj.description,
                               expand=True),
                           OTC(_("Due date"), lambda obj:
                               obj.due_date.strftime("%x"), width=140),
                           OTC(_("Value"), lambda obj:
                               get_formatted_price(obj.value), width=100,
                               align=RIGHT)]

        self.add_object_table(list(payments), payment_columns)

    def _setup_order_details_table(self):
        cols = [TC("", width=100), TC("", width=285, expand=True,
                                      truncate=True),
                TC("", width=50), TC("", width=285, expand=True,
                                     truncate=True)]
        data = [[_("Open Date:"), self._order.get_open_date_as_string(),
                 _("Status:"), self._order.get_status_str()],
                [_("Supplier:"), self._order.get_supplier_name(),
                 _("Branch:"), self._order.get_branch_name()],
                ]
        data.append(self._get_freight_line())
        self.add_column_table(data, cols, do_header=False,
                              highlight=HIGHLIGHT_NEVER, margins=2,
                              table_line=TABLE_LINE_BLANK, width=730)
        if self._order.expected_receival_date:
            expected_date = self._order.expected_receival_date.strftime("%x")
        else:
            expected_date = _("Not Specified")
        self.add_paragraph(_("Expected Receival Date: %s") % expected_date)

    def _setup_items_table(self):
        items = self._order.get_items()
        # XXX: Stoqlib Reporting try to apply len() on the table data, but
        # Purchase's get_items returns a SelectResult instance (ORMObject)
        # that not supports the len operator.
        self._add_ordered_items_table(list(self._order.get_items()))

    #
    # BaseStoqReport hooks
    #

    def get_title(self):
        order_number = self._order.get_order_number_str()
        return _("Purchase Order #%s") % order_number


class PurchaseQuoteReport(BaseStoqReport):
    """A quote report to be sent to suppliers
    """
    report_name = _(u'Quote Request')

    def __init__(self, filename, quote, *args, **kwargs):
        self._quote = quote
        BaseStoqReport.__init__(self, filename, self.report_name,
                                landscape=True, *args, **kwargs)
        self._setup_quote_details()
        self._setup_payments()
        self._setup_items_table()
        self._add_signature_field()

    def _get_items_columns(self):
        return [
            OTC(_("Item"), lambda obj: "%s" % obj.sellable.get_description(),
                expand=True, truncate=True),
            # FIXME: This column should be virtual, waiting for bug #2764
            OTC("Unit", lambda obj: obj.sellable.get_unit_description(),
                virtual=False, width=50, align=LEFT),
            OTC(_("Cost"), lambda obj: "", width=70, align=RIGHT),
            OTC(_("Quantity"), lambda obj: format_quantity(obj.quantity),
                width=70, align=RIGHT),
            OTC(_("Total"), lambda obj: "", width=90, align=RIGHT),]

    def _get_freight_line(self):
        return [_(u"Transporter:"), u"",
                _(u"Freight:"), u""]

    def _setup_quote_details(self):
        cols = [TC("", width=100),
                TC("", width=285, expand=True, truncate=True),
                TC("", width=50),
                TC("", width=285, expand=True, truncate=True)]
        data = [[_(u"Open Date:"), self._quote.get_open_date_as_string(),
                 # To be filled
                 _(u"Deadline:"), ""],
                [_(u"Supplier:"), self._quote.get_supplier_name(),
                 _(u"Branch:"), self._quote.get_branch_name()]]

        data.append(self._get_freight_line())
        self.add_column_table(data, cols, do_header=False,
                              highlight=HIGHLIGHT_NEVER, margins=2,
                              table_line=TABLE_LINE_BLANK, width=730)
        self.add_blank_space(5)

    def _setup_payments(self):
        self.add_paragraph(_(u"Payment Settings"), style="Title")
        self.add_blank_space(5)
        cols = [TC("", width=150, expand=True), TC("", width=150, expand=True),
                TC("", width=150, expand=True), TC("", width=150, expand=True)]
        data = [[_(u"Payment Method:"), "", _(u"Installments:"), ""],
                [_(u"Intervals:"), "", _(u"Obs:"), ""]]
        self.add_column_table(data, cols, do_header=False,
                              highlight=HIGHLIGHT_NEVER, margins=2,
                              table_line=TABLE_LINE_BLANK, width=730)
        self.add_blank_space(5)

    def _setup_items_table(self):
        self.add_paragraph(_(u"Quoting Items"), style="Title")
        items = self._quote.get_items()
        self.add_object_table(list(items), self._get_items_columns())
        self.add_blank_space(5)

    def _add_signature_field(self):
        # The supplier name here ?
        self.add_signatures([_(u"Responsible")])

    #
    # BaseStoqReport
    #

    def get_title(self):
        return self.report_name
