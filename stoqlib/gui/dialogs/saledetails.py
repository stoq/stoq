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
## Author(s):   Bruno Rafael Garcia             <brg@async.com.br>
##              Evandro Vale Miquelito          <evandro@async.com.br>
##
##
""" Classes for sale details """


import datetime

from kiwi.datatypes import currency
from kiwi.ui.widgets.list import Column, SummaryLabel

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.editors import BaseEditor
from stoqlib.domain.interfaces import IPaymentGroup
from stoqlib.domain.sale import SaleView, Sale

_ = stoqlib_gettext


class SaleDetailsDialog(BaseEditor):
    gladefile = "SaleDetailsDialog"
    model_type = SaleView
    title = _("Sale Details")
    size = (650, 460)
    hide_footer = True
    proxy_widgets = ('status_lbl',
                     'client_lbl',
                     'salesperson_lbl',
                     'open_date_lbl',
                     'total_lbl',
                     'subtotal_lbl',
                     'surcharge_lbl',
                     'discount_lbl')

    def _setup_widgets(self):
        # TODO Waiting for bug 2360
        self.details_button.set_sensitive(False)

        self.items_list.set_columns(self._get_items_columns())
        self.payments_list.set_columns(self._get_payments_columns())

        sale = Sale.get(self.model.id, connection=self.conn)
        self.items_list.add_list(sale.get_items())
        group = IPaymentGroup(sale, connection=self.conn)
        self.payments_list.add_list(group.get_items())

        value_format = '<b>%s</b>'
        payments_summary_label = SummaryLabel(klist=self.payments_list,
                                              column='value',
                                              label='<b>Total:</b>',
                                              value_format=value_format)
        payments_summary_label.show()
        self.payments_vbox.pack_start(payments_summary_label, False)

    def _get_payments_columns(self):
        return [Column('payment_number', "#", data_type=int, width=50),
                Column('method.description', _("Method of Payment"),
                       expand=True, data_type=str, width=200),
                Column('due_date', _("Due Date"), sorted=True,
                       data_type=datetime.date, width=120),
                Column('status_str', _("Status"), data_type=str, width=100),
                Column('value', _("Value"), data_type=currency, width=100)]

    def _get_items_columns(self):
        return [Column('sellable.code', _("Code"), sorted=True,
                       data_type=str, width=80),
                Column('sellable.base_sellable_info.description',
                       _("Description"), data_type=str, expand=True,
                       width=200),
                Column('quantity', _("Quantity"), data_type=int, width=100),
                Column('price', _("Price"), data_type=currency, width=100),
                Column('total', _("Total"), data_type=currency, width=100)]

    #
    # Kiwi handlers
    #

    def on_details_button__clicked(self, *args):
        # This button will be implemeted after bug 2360 fix.
        pass

    #
    # BaseEditor hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model, SaleDetailsDialog.proxy_widgets)
