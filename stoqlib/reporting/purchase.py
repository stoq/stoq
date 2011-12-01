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

from decimal import Decimal

from stoqlib.reporting.base.tables import (ObjectTableColumn as OTC,
                                           TableColumn as TC,
                                           HIGHLIGHT_NEVER)
from stoqlib.reporting.base.flowables import RIGHT, LEFT
from stoqlib.reporting.base.default_style import TABLE_LINE_BLANK
from stoqlib.lib.formatters import (get_formatted_price, get_formatted_cost,
                                   format_quantity)
from stoqlib.lib.defaults import ALL_ITEMS_INDEX
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.template import BaseStoqReport, ObjectListReport
from stoqlib.domain.purchase import (PurchaseOrder, PurchaseOrderView,
                                     PurchaseItemView)
from stoqlib.domain.receiving import ReceivingOrder

_ = stoqlib_gettext


class PurchaseReport(ObjectListReport):
    report_name = _("Purchase Order Report")
    main_object_name = (_("order"), _("orders"))
    filter_format_string = _("with status <u>%s</u>")
    # This should be properly verified on SearchResultsReport. Waiting for
    # bug 2517
    obj_type = PurchaseOrderView

    def __init__(self, filename, objectlist, purchases, status,
                 *args, **kwargs):
        self.show_status_column = status == ALL_ITEMS_INDEX
        self._purchases = purchases
        ObjectListReport.__init__(self, filename, objectlist, purchases,
                                  PurchaseReport.report_name,
                                  landscape=1, *args, **kwargs)
        self._setup_table()

    def _setup_table(self):
        totals = [(purchase.ordered_quantity, purchase.received_quantity,
                   purchase.total) for purchase in self._purchases]
        ordered, received, total = zip(*totals)
        self.add_summary_by_column(
            _(u'Ordered'), format_quantity(sum(ordered, Decimal(0))))
        self.add_summary_by_column(
            _(u'Received'), format_quantity(sum(received, Decimal(0))))
        self.add_summary_by_column(
            _(u'Total'), get_formatted_price(sum(total, Decimal(0))))

        summary_row = self.get_summary_row()
        if self.show_status_column:
            summary_row.insert(0, "")

        self.add_object_table(self._purchases, self.get_columns(),
                              summary_row=summary_row)


class PurchasedItemsReport(ObjectListReport):
    report_name = _("Purchases Items Report")
    obj_type = PurchaseItemView

    def __init__(self, filename, objectlist, purchases, *args, **kwargs):
        self._purchases = purchases
        ObjectListReport.__init__(self, filename, objectlist, purchases,
                                  self.report_name, landscape=True,
                                  *args, **kwargs)
        self._setup_table()

    def _setup_table(self):
        totals = [(purchase.purchased, purchase.received, purchase.stocked)
                  for purchase in self._purchases]
        purchased, received, stocked = zip(*totals)
        self.add_summary_by_column(_(u'Purchased'),
                                   format_quantity(sum(purchased, Decimal(0))))
        self.add_summary_by_column(_(u'Received'),
                                   format_quantity(sum(received, Decimal(0))))
        self.add_summary_by_column(_(u'In Stock'),
                                   format_quantity(sum(stocked, Decimal(0))))

        self.add_object_table(self._purchases, self.get_columns(),
                              summary_row=self.get_summary_row())


class PurchaseOrderReport(BaseStoqReport):
    report_name = _("Purchase Order")

    def __init__(self, filename, order):
        self._order = order
        self._receiving_orders = order.get_receiving_orders()
        BaseStoqReport.__init__(self, filename, PurchaseOrderReport.report_name,
                                landscape=True)
        self._setup_order_details_table()
        self.add_blank_space(10)
        self._setup_payment_group_data()
        self.add_blank_space(10)
        self._setup_items_table()
        self._add_notes()

    def _get_items_table_columns(self, include_received):
        """
        @param include_received: If the received quantity and total columns
        should be displayed
        """
        cols = [
            OTC(_("Category"), lambda obj: "%s" %
                obj.sellable.get_category_description(), width=90),
            OTC(_("Item"),
                lambda obj: ("%s - %s" % (obj.sellable.code,
                                          obj.sellable.get_description())),
                expand=True, truncate=True),
            # FIXME: This column should be virtual, waiting for bug #2764
            OTC("Unit", lambda obj: obj.sellable.get_unit_description(),
                virtual=False, width=50, align=LEFT),
            OTC(_("Cost"), lambda obj: get_formatted_cost(obj.cost),
                width=70, align=RIGHT),
            OTC(_("Qty"), lambda obj: format_quantity(obj.quantity),
                width=70, align=RIGHT),
            OTC(_("Total"),
                lambda obj: get_formatted_price(obj.get_total()), width=90,
                align=RIGHT),
            ]

        if include_received:
            cols.extend([
                OTC(_("Qty Received"), lambda obj: format_quantity(
                    obj.quantity_received), width=90, align=RIGHT),
                OTC(_("Total"),
                    lambda obj: get_formatted_price(obj.get_received_total()),
                    width=90, align=RIGHT),
                ])

        return cols

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

        extra_row = ["", "", "", _("Totals:"), format_quantity(total_quantity),
                     get_formatted_price(total_value)]
        if total_qty_received:
            extra_row.extend([format_quantity(total_qty_received),
                              get_formatted_price(total_received)])

        columns = self._get_items_table_columns(total_qty_received)
        self.add_object_table(items, columns,
                              summary_row=extra_row)

    def _add_ordered_items_table(self, items):
        self.add_paragraph(_("Purchase Ordered Items"), style="Title")
        self._add_items_table(items)

    def _get_transporter_freight_lines(self):
        lines = []

        freight_type_map = {
            ReceivingOrder.FREIGHT_FOB_PAYMENT: PurchaseOrder.FREIGHT_FOB,
            ReceivingOrder.FREIGHT_FOB_INSTALLMENTS: PurchaseOrder.FREIGHT_FOB,
            ReceivingOrder.FREIGHT_CIF_UNKNOWN: PurchaseOrder.FREIGHT_CIF,
            ReceivingOrder.FREIGHT_CIF_INVOICE: PurchaseOrder.FREIGHT_CIF
            }
        freight_names = PurchaseOrder.freight_types
        freight_types = []

        # First line.
        transporter = self._order.get_transporter_name() or _(u"Not Specified")
        freight = get_formatted_price(self._order.expected_freight)
        agreed_freight = _(u"%s (%s)") % (
            freight_names[self._order.freight_type], freight)

        lines.append([_(u"Transporter:"), transporter,
                      _(u"Agreed Freight:"), agreed_freight])

        # Second line
        if self._order.expected_receival_date:
            expected_date = self._order.expected_receival_date.strftime("%x")
        else:
            expected_date = _("Not Specified")
        second_line = [_(u"Expected Receival Date:"), expected_date]

        if self._receiving_orders.count():
            # If order was received, show it's freight
            freight = 0
            for order in self._receiving_orders:
                freight += order.freight_total
                # If first time used, append to the list of used types
                if freight_type_map[order.freight_type] not in freight_types:
                    freight_types.append(freight_type_map[order.freight_type])

            freight = get_formatted_price(freight)
            if len(freight_types) == 1:
                received_freight = _(u"%s (%s)") % (
                    freight_names[freight_types[0]], freight)
            else:
                self.received_freight_type = _(u'Mixed (%s)') % freight

            second_line.extend([_("Received Freight:"), received_freight])
        else:
            second_line.extend([u'', u''])
        lines.append(second_line)

        return lines

    def _setup_payment_group_data(self):
        payments = self._order.payments
        installments_number = payments.count()
        if installments_number > 1:
            msg = (_("Payments: %d installments")
                   % (installments_number, ))
        elif installments_number == 1:
            msg = _("Payments: 1 installment")
        else:
            msg = _(u'There are no payments defined for this order.')
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
        if payments:
            self.add_object_table(list(payments), payment_columns)

    def _setup_order_details_table(self):
        cols = [TC("", width=100), TC("", width=250, expand=True,
                                      truncate=True),
                TC("", width=120), TC("", width=250, expand=True,
                                     truncate=True)]
        data = [[_("Open Date:"), self._order.get_open_date_as_string(),
                 _("Status:"), self._order.get_status_str()],
                [_("Supplier:"), self._order.get_supplier_name(),
                 _("Branch:"), self._order.get_branch_name()],
                ]

        data.extend(self._get_transporter_freight_lines())

        self.add_column_table(data, cols, do_header=False,
                              highlight=HIGHLIGHT_NEVER, margins=2,
                              table_line=TABLE_LINE_BLANK, width=730)

    def _setup_items_table(self):
        # XXX: Stoqlib Reporting try to apply len() on the table data, but
        # Purchase's get_items returns a SelectResult instance (ORMObject)
        # that not supports the len operator.
        self._add_ordered_items_table(list(self._order.get_items()))

    def _add_notes(self):
        if self._order.notes:
            self.add_paragraph(_(u'Purchase Notes'), style='Normal-Bold')
            self.add_preformatted_text(self._order.notes,
                                       style='Normal-Notes')

        receiving_details = u'\n'.join([r.notes for r
                                        in self._receiving_orders])
        if receiving_details:
            self.add_blank_space(10)
            self.add_paragraph(_(u'Receiving Details'), style='Normal-Bold')
            self.add_preformatted_text(receiving_details,
                                       style='Normal-Notes')

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
