# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2009 Async Open Source <http://www.async.com.br>
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
""" Purchase report implementation """

from stoqlib.reporting.base.tables import (ObjectTableColumn as OTC,
                                           TableColumn as TC,
                                           HIGHLIGHT_NEVER)
from stoqlib.reporting.base.flowables import RIGHT, LEFT
from stoqlib.reporting.base.defaultstyle import TABLE_LINE_BLANK
from stoqlib.lib.formatters import get_formatted_price, format_quantity
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.report import ObjectListReport, HTMLReport
from stoqlib.reporting.template import BaseStoqReport
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.receiving import ReceivingOrder

_ = stoqlib_gettext


class PurchaseReport(ObjectListReport):
    title = _("Purchase Order Report")
    main_object_name = (_("order"), _("orders"))
    filter_format_string = _("with status <u>%s</u>")
    summary = ['total', 'ordered_quantity', 'received_quantity']


class PurchasedItemsReport(ObjectListReport):
    title = _("Purchases Items Report")
    main_object_name = (_("items"), _("items"))
    summary = ['purchased', 'received', 'stocked']


class PurchaseOrderReport(HTMLReport):
    template_filename = 'purchase/purchase.html'
    title = _("Purchase Order")
    complete_header = False

    def __init__(self, filename, order):
        self.order = order
        self.receiving_orders = list(order.get_receiving_orders())
        HTMLReport.__init__(self, filename)

    def get_agreed_freight(self):
        freight_names = PurchaseOrder.freight_types
        freight_value = get_formatted_price(self.order.expected_freight)
        return _(u"%s (%s)") % (freight_names[self.order.freight_type],
                                freight_value)

    def get_received_freight(self):
        if not self.receiving_orders:
            return None

        freight_names = PurchaseOrder.freight_types
        freight_type_map = {
            ReceivingOrder.FREIGHT_FOB_PAYMENT: PurchaseOrder.FREIGHT_FOB,
            ReceivingOrder.FREIGHT_FOB_INSTALLMENTS: PurchaseOrder.FREIGHT_FOB,
            ReceivingOrder.FREIGHT_CIF_UNKNOWN: PurchaseOrder.FREIGHT_CIF,
            ReceivingOrder.FREIGHT_CIF_INVOICE: PurchaseOrder.FREIGHT_CIF
            }
        freight_types = []

        freight = 0
        for order in self.receiving_orders:
            freight += order.freight_total

            # If first time used, append to the list of used types
            if freight_type_map[order.freight_type] not in freight_types:
                freight_types.append(freight_type_map[order.freight_type])

        freight_value = get_formatted_price(freight)
        if len(freight_types) == 1:
            received_freight = _(u"%s (%s)") % (freight_names[freight_types[0]],
                                                freight_value)
        else:
            received_freight = _(u'Mixed (%s)') % freight_value
        return received_freight

    def get_subtitle(self):
        order_number = self.order.get_order_number_str()
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
        self._add_notes()
        self._add_signature_field()

    def _get_items_columns(self):
        return [
            OTC(_("Category"), lambda obj: "%s" %
                obj.sellable.get_category_description(), width=110),
            OTC(_("Item"), lambda obj: "%s" % obj.sellable.get_description(),
                expand=True, truncate=True),
            # FIXME: This column should be virtual, waiting for bug #2764
            OTC("Unit", lambda obj: obj.sellable.get_unit_description(),
                virtual=False, width=50, align=LEFT),
            OTC(_("Cost"), lambda obj: "", width=70, align=RIGHT),
            OTC(_("Quantity"), lambda obj: format_quantity(obj.quantity),
                width=70, align=RIGHT),
            OTC(_("Total"), lambda obj: "", width=90, align=RIGHT)]

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

    def _add_notes(self):
        if self._quote.notes:
            self.add_paragraph(_(u'Purchase Notes'), style='Normal-Bold')
            self.add_preformatted_text(self._quote.notes,
                                       style='Normal-Notes')

    def get_title(self):
        order_number = self._quote.get_order_number_str()
        return "%s #%s" % (self.report_name, order_number)
