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

from stoqlib.lib.formatters import get_formatted_price
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.report import ObjectListReport, HTMLReport
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
        return _("Purchase Order #%s") % self.order.identifier


class PurchaseQuoteReport(HTMLReport):
    """A quote report to be sent to suppliers
    """
    title = _(u'Quote Request')
    template_filename = 'quote/quote.html'
    complete_header = False

    def __init__(self, filename, order):
        self.order = order
        HTMLReport.__init__(self, filename)

    def get_subtitle(self):
        return _("Number #%s") % self.order.identifier
