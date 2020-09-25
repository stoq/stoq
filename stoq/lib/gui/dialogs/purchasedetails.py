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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Purchase details dialogs """

import datetime
from decimal import Decimal

from gi.repository import Gtk, Gdk, Pango
from kiwi.currency import currency
from kiwi.ui.objectlist import Column, SummaryLabel, ColoredColumn

from stoqlib.api import api
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import PaymentChangeHistoryView
from stoqlib.domain.purchase import PurchaseOrder, PurchaseItemView
from stoqlib.domain.receiving import ReceivingInvoice
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.formatters import get_formatted_cost
from stoq.lib.gui.base.dialogs import run_dialog
from stoq.lib.gui.dialogs.labeldialog import SkipLabelsEditor
from stoq.lib.gui.dialogs.spreadsheetexporterdialog import SpreadSheetExporter
from stoq.lib.gui.editors.baseeditor import BaseEditor
from stoq.lib.gui.search.searchcolumns import IdentifierColumn, QuantityColumn
from stoq.lib.gui.utils.printing import print_labels, print_report
from stoqlib.reporting.purchase import (PurchaseOrderReport,
                                        PurchaseQuoteReport,
                                        PurchaseOrderItemReport)

_ = stoqlib_gettext


def payment_value_colorize(payment):
    if payment.status == Payment.STATUS_CANCELLED:
        return Gdk.color_parse('gray')
    if payment.is_inpayment():
        return Gdk.color_parse('blue')

    return Gdk.color_parse('red')


class _TemporaryReceivingDetails:
    """A workaround class, used to summarize a list of receiving order"""

    total_discounts = currency(0)
    total_surcharges = currency(0)
    receiving_subtotal = currency(0)
    receiving_total = currency(0)
    receiving_quantity = Decimal(0)
    received_freight = currency(0)
    received_freight_type = u''

    def __init__(self, purchase, receivings):
        freight_type_map = {
            ReceivingInvoice.FREIGHT_FOB_PAYMENT: PurchaseOrder.FREIGHT_FOB,
            ReceivingInvoice.FREIGHT_FOB_INSTALLMENTS: PurchaseOrder.FREIGHT_FOB,
            ReceivingInvoice.FREIGHT_CIF_UNKNOWN: PurchaseOrder.FREIGHT_CIF,
            ReceivingInvoice.FREIGHT_CIF_INVOICE: PurchaseOrder.FREIGHT_CIF
        }
        freight_names = PurchaseOrder.freight_types
        freight_types = set()

        if receivings.count():
            discount = surcharge = freight = subtotal = total = quantity = 0
            for receiving in receivings:
                discount += receiving.total_discounts
                surcharge += receiving.total_surcharges
                if receiving.receiving_invoice:
                    freight += receiving.receiving_invoice.freight_total
                subtotal += receiving.product_total_with_ipi
                total += receiving.total
                quantity += receiving.total_quantity

                freight_types.add(freight_type_map.get(receiving.freight_type,
                                                       purchase.freight_type))

            self.total_discounts = currency(discount)
            self.total_surcharges = currency(surcharge)
            self.received_freight = currency(freight)
            self.receiving_subtotal = currency(subtotal)
            self.receiving_total = currency(total)
            self.receiving_quantity = quantity

            if len(freight_types) == 1:
                self.received_freight_type = freight_names[freight_types.pop()]
            else:
                self.received_freight_type = _(u'Mixed Freights')


class PurchaseDetailsDialog(BaseEditor):
    gladefile = "PurchaseDetailsDialog"
    model_type = PurchaseOrder
    title = _("Purchase Details")
    size = (750, 460)
    hide_footer = True
    proxy_widgets = ('branch',
                     'identifier',
                     'supplier',
                     'open_date',
                     'status',
                     'transporter_name',
                     'responsible_name',
                     'salesperson_name',
                     'expected_receival_date',
                     'expected_freight',
                     'freight_type',
                     'notes')
    payment_proxy = ('total_paid',
                     'total_interest',
                     'total_discount',
                     'total_penalty',
                     'total_value')
    receiving_proxy = ('received_freight_type',
                       'received_freight',
                       'total_discounts',
                       'total_surcharges',
                       'receiving_subtotal',
                       'receiving_total',
                       'receiving_quantity')

    def _setup_summary_labels(self):
        order_summary_label = SummaryLabel(
            klist=self.ordered_items,
            column='total',
            label='<b>%s</b>' % api.escape(_(u"Total")),
            value_format='<b>%s</b>')
        order_summary_label.show()
        self.ordered_vbox.pack_start(order_summary_label, False, True, 0)

    def _setup_widgets(self):
        self.ordered_items.set_columns(self._get_ordered_columns())
        self.received_items.set_columns(self._get_received_columns())
        self.payments_info_list.set_columns(self._get_payments_info_columns())

        purchase_items = PurchaseItemView.find_by_purchase(self.store, self.model)

        self.ordered_items.add_list(purchase_items)
        self.received_items.add_list(purchase_items)

        self.payments_list.set_columns(self._get_payments_columns())
        if self.model.group:
            self.payments_list.add_list(self.model.group.payments)
            changes = PaymentChangeHistoryView.find_by_group(self.store,
                                                             self.model.group)
            self.payments_info_list.add_list(changes)

        if self._receiving_orders.is_empty():
            for widget in (self.received_freight_type_label,
                           self.received_freight_type,
                           self.received_freight_label,
                           self.received_freight):
                widget.hide()

        self.export_csv.set_visible(
            self.model.status == PurchaseOrder.ORDER_QUOTING)
        self.export_received.set_visible(bool(self.model.get_receiving_orders().any()))

        self._setup_summary_labels()

        label = self.print_labels.get_children()[0]
        label = label.get_children()[0].get_children()[1]
        label.set_label(_(u'Print labels'))

    def _get_ordered_columns(self):
        return [Column('description', title=_('Description'), data_type=str,
                       expand=True, searchable=True, sorted=True,
                       ellipsize=Pango.EllipsizeMode.END),
                QuantityColumn('quantity', title=_('Qty')),
                Column('cost', title=_('Cost'), data_type=currency,
                       format_func=get_formatted_cost),
                Column('total', title=_('Total'), data_type=currency)]

    def _get_received_columns(self):
        return [Column('description', title=_('Description'), data_type=str,
                       expand=True, searchable=True, sorted=True,
                       ellipsize=Pango.EllipsizeMode.END),
                QuantityColumn('quantity_received', title=_('Qty Received')),
                Column('cost', title=_('Cost'), data_type=currency,
                       format_func=get_formatted_cost),
                Column('total_received', title=_('Total'), data_type=currency),
                QuantityColumn('current_stock', title=_('Current Stock')),
                ]

    def _get_payments_columns(self):
        return [IdentifierColumn('identifier', title=_('Payment #')),
                Column('description', _("Description"), data_type=str,
                       expand=True, ellipsize=Pango.EllipsizeMode.END),
                Column('due_date', _("Due date"), sorted=True,
                       data_type=datetime.date, justify=Gtk.Justification.RIGHT),
                Column('paid_date', _("Paid date"), data_type=datetime.date),
                Column('status_str', _("Status"), data_type=str),
                ColoredColumn('value', _("Value"), data_type=currency,
                              justify=Gtk.Justification.RIGHT, use_data_model=True,
                              data_func=payment_value_colorize),
                ColoredColumn('paid_value', _("Paid value"), data_type=currency,
                              justify=Gtk.Justification.RIGHT, use_data_model=True,
                              data_func=payment_value_colorize)]

    def _get_payments_info_columns(self):
        return [Column('change_date', _(u"When"), data_type=datetime.date,
                       sorted=True),
                Column('description', _(u"Payment"), data_type=str, expand=True,
                       ellipsize=Pango.EllipsizeMode.END),
                Column('changed_field', _(u"Changed"), data_type=str,
                       justify=Gtk.Justification.RIGHT),
                Column('from_value', _(u"From"), data_type=str,
                       justify=Gtk.Justification.RIGHT),
                Column('to_value', _(u"To"), data_type=str,
                       justify=Gtk.Justification.RIGHT),
                Column('reason', _(u"Reason"), data_type=str,
                       ellipsize=Pango.EllipsizeMode.END)]

    def _export_csv(self, object_list, name, filename_prefix):
        sse = SpreadSheetExporter()
        sse.export(object_list=object_list,
                   name=name,
                   filename_prefix=filename_prefix)

    def _print_report(self):
        if self.model.status == PurchaseOrder.ORDER_QUOTING:
            report = PurchaseQuoteReport
        else:
            report = PurchaseOrderReport

        print_report(report, self.model)

    #
    # BaseEditor hooks
    #

    def setup_proxies(self):
        self._receiving_orders = self.model.get_receiving_orders()

        self._setup_widgets()

        self.add_proxy(self.model, PurchaseDetailsDialog.proxy_widgets)
        if self.model.group:
            self.add_proxy(self.model.group, PurchaseDetailsDialog.payment_proxy)
        self.add_proxy(_TemporaryReceivingDetails(self.model, self._receiving_orders),
                       PurchaseDetailsDialog.receiving_proxy)

    def on_export_csv__clicked(self, button):
        self._export_csv(self.ordered_items, _('Purchase items'), _('purchase-items'))

    def on_export_received__clicked(self, button):
        self._export_csv(self.received_items, _('Received items'), _('received-items'))

    def on_print_button__clicked(self, button):
        self._print_report()

    def on_print_labels__clicked(self, button):
        label_data = run_dialog(SkipLabelsEditor, self, self.store)
        if label_data:
            print_labels(label_data, self.store, self.model)

    def on_print_items_button__clicked(self, button):
        print_report(PurchaseOrderItemReport, self.model)
