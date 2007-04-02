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

import gtk
from kiwi.datatypes import currency
from kiwi.ui.widgets.list import Column, SummaryLabel, ColoredColumn

from stoqlib.exceptions import StoqlibError
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import payment_value_colorize
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.base.dialogs import run_dialog, print_report
from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
from stoqlib.domain.interfaces import IClient, IPaymentGroup
from stoqlib.domain.person import Person
from stoqlib.domain.sale import SaleView, Sale
from stoqlib.reporting.sale import SaleOrderReport

_ = stoqlib_gettext


class SaleDetailsDialog(BaseEditor):
    gladefile = "SaleDetailsDialog"
    model_type = SaleView
    title = _(u"Sale Details")
    size = (650, 460)
    hide_footer = True
    proxy_widgets = ('status_lbl',
                     'client_lbl',
                     'salesperson_lbl',
                     'open_date_lbl',
                     'total_lbl',
                     'notes',
                     'order_number',
                     'subtotal_lbl',
                     'surcharge_lbl',
                     'discount_lbl')

    def __init__(self, conn, model=None, visual_mode=False):
        """
        @param conn: a database connection
        @param model: a L{stoqlib.domain.sale.Sale} object
        """
        BaseEditor.__init__(self, conn, model,
                            visual_mode=visual_mode)

    def _setup_columns(self):
        self.items_list.set_columns(self._get_items_columns())
        self.payments_list.set_columns(self._get_payments_columns())

    def _setup_summary_labels(self):
        summary_label = SummaryLabel(klist=self.payments_list,
                                     column='base_value',
                                     label='<b>%s</b>' % _(u"Total:"),
                                     value_format='<b>%s</b>')
        summary_label.show()
        self.payments_vbox.pack_start(summary_label, False)

    def _setup_widgets(self):
        if not self.model.client_id:
            self.details_button.set_sensitive(False)
        self._setup_columns()

        self.sale_order = Sale.get(self.model.id, connection=self.conn)

        if self.sale_order.status == Sale.STATUS_CANCELLED:
            self.cancel_details_button.show()
        else:
            self.cancel_details_button.hide()

        self.items_list.add_list(self.sale_order.get_items())
        group = IPaymentGroup(self.sale_order)
        self.payments_list.add_list(group.get_items())
        self._setup_summary_labels()

    def _get_payments_columns(self):
        return [Column('id', "#", data_type=int, width=50,
                       format='%04d', justify=gtk.JUSTIFY_RIGHT),
                Column('method.description', _("Type"),
                       data_type=str, width=90),
                Column('description', _("Description"), data_type=str,
                       width=190, expand=True),
                Column('due_date', _("Due Date"), sorted=True,
                       data_type=datetime.date, width=110,
                       justify=gtk.JUSTIFY_RIGHT),
                Column('status_str', _("Status"), data_type=str, width=80),
                ColoredColumn('base_value', _("Value"), data_type=currency,
                              width=90, color='red',
                              justify=gtk.JUSTIFY_RIGHT,
                              data_func=payment_value_colorize)]

    def _get_items_columns(self):
        return [Column('sellable.id', _("Code"), sorted=True,
                       data_type=int, width=80, format='%04d'),
                Column('sellable.base_sellable_info.description',
                       _("Description"), data_type=str, expand=True,
                       width=200),
                Column('quantity_unit_string', _("Quantity"), data_type=str,
                       width=100, justify=gtk.JUSTIFY_RIGHT),
                Column('price', _("Price"), data_type=currency, width=100),
                Column('total', _("Total"), data_type=currency, width=100)]

    #
    # BaseEditor hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model, SaleDetailsDialog.proxy_widgets)

    #
    # Kiwi handlers
    #

    def on_print_button__clicked(self, button):
        print_report(SaleOrderReport,
                     Sale.get(self.model.id, connection=self.conn))

    def on_details_button__clicked(self, button):
        if not self.model.client_id:
            raise StoqlibError("You should never call ClientDetailsDialog "
                               "for sales which clients were not specified")
        client = Person.iget(IClient, self.model.client_id,
                             connection=self.conn)
        run_dialog(ClientDetailsDialog, self, self.conn, client)

    def on_cancel_details_button__clicked(self, button):
        run_dialog(SaleCancellationDetailsDialog, self, self.conn,
                   self.sale_order)


class SaleCancellationDetailsDialog(BaseEditor):
    gladefile = "HolderTemplate"
    model_type = Sale
    title = _(u"Sale Cancellation Details")
    size = (650, 350)
    hide_footer = True

    def setup_slaves(self):
        from stoqlib.gui.slaves.saleslave import SaleReturnSlave
        if self.model.status != Sale.STATUS_CANCELLED:
            raise StoqlibError("Invalid status for sale order, it should be "
                               "cancelled")
        adapter = self.model.renegotiation_data
        self.slave = SaleReturnSlave(self.conn, self.model, adapter,
                                     visual_mode=True)
        self.attach_slave("place_holder", self.slave)
