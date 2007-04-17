# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito  <evandro@async.com.br>
##
##
""" Purchase details dialogs """

import datetime

import gtk
from kiwi.datatypes import currency
from kiwi.ui.widgets.list import Column, SummaryLabel, ColoredColumn

from stoqlib.lib.defaults import payment_value_colorize
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.base.dialogs import print_report
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.interfaces import IPaymentGroup
from stoqlib.reporting.purchase import PurchaseOrderReport

_ = stoqlib_gettext

class PurchaseDetailsDialog(BaseEditor):
    gladefile = "PurchaseDetailsDialog"
    model_type = PurchaseOrder
    title = _("Purchase Details")
    size = (750, 460)
    hide_footer = True
    proxy_widgets = ('branch',
                     'order_number',
                     'supplier',
                     'open_date',
                     'status',
                     'purchase_total',
                     'purchase_subtotal',
                     'surcharge_value',
                     'transporter',
                     'salesperson',
                     'receival_date',
                     'freight_type',
                     'freight',
                     'notes',
                     'discount_lbl')
    payment_proxy = ('payment_method',
                     'installments_number')

    def _setup_summary_labels(self):
        value_format = '<b>%s</b>'

        payment_summary_label = SummaryLabel(klist=self.payments_list,
                                             column='base_value',
                                             label='<b>%s</b>' % _(u"Total:"),
                                             value_format=value_format)
        payment_summary_label.show()
        self.payments_vbox.pack_start(payment_summary_label, False)

        received_label = '<b>%s</b>' % _('Total Received:')
        received_summary_label = SummaryLabel(klist=self.received_items,
                                              column='received_total',
                                              label=received_label,
                                              value_format=value_format)
        received_summary_label.show()
        self.received_vbox.pack_start(received_summary_label, False)

    def _setup_widgets(self):
        self.ordered_items.set_columns(self._get_ordered_columns())
        self.received_items.set_columns(self._get_received_columns())

        self.ordered_items.add_list(self.model.get_items())
        self.received_items.add_list(self.model.get_partially_received_items())

        self.payments_list.set_columns(self._get_payments_columns())
        group = IPaymentGroup(self.model)
        self.payments_list.add_list(group.get_items())

        self._setup_summary_labels()

    def _get_ordered_columns(self):
        return [Column('sellable.base_sellable_info.description',
                       title=_('Description'),
                       data_type=str, expand=True, searchable=True),
                Column('quantity_as_string', title=_('Quantity'),
                       data_type=str, width=90, editable=True,
                       justify=gtk.JUSTIFY_RIGHT),
                Column('cost', title=_('Cost'), data_type=currency,
                       width=90),
                Column('total', title=_('Total'), data_type=currency,
                       width=100)]

    def _get_received_columns(self):
        return [Column('sellable.base_sellable_info.description',
                       title=_('Description'),
                       data_type=str, expand=True, searchable=True),
                Column('quantity_received_as_string',
                       title=_('Quantity Received'),
                       data_type=str, width=150, editable=True,
                       justify=gtk.JUSTIFY_RIGHT),
                Column('cost', title=_('Cost'), data_type=currency,
                       editable=True, width=90),
                Column('received_total', title=_('Total'),
                       data_type=currency, width=100)]

    def _get_payments_columns(self):
        return [Column('id', "#", data_type=int, width=50,
                       format='%04d', justify=gtk.JUSTIFY_RIGHT),
                Column('method.description', _("Type"),
                       data_type=str, width=60),
                Column('description', _("Description"), data_type=str,
                       width=150, expand=True),
                Column('due_date', _("Due Date"), sorted=True,
                       data_type=datetime.date, width=90,
                       justify=gtk.JUSTIFY_RIGHT),
                Column('paid_date', _("Paid Date"),
                      data_type=datetime.date, width=90),
                Column('status_str', _("Status"), data_type=str, width=80),
                ColoredColumn('base_value', _("Value"), data_type=currency,
                              width=90, color='red',
                              justify=gtk.JUSTIFY_RIGHT,
                              data_func=payment_value_colorize), 
                ColoredColumn('paid_value', _("Paid Value"), data_type=currency,
                              width=92, color='red',
                              justify=gtk.JUSTIFY_RIGHT,
                              data_func=payment_value_colorize)]

    #
    # BaseEditor hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model, PurchaseDetailsDialog.proxy_widgets)
        payment_group = IPaymentGroup(self.model, None)
        if payment_group:
            self.add_proxy(payment_group, PurchaseDetailsDialog.payment_proxy)


    #
    # Kiwi callbacks
    #

    def on_print_button__clicked(self, button):
        print_report(PurchaseOrderReport, self.model)
