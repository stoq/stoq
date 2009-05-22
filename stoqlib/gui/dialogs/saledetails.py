# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2008 Async Open Source <http://www.async.com.br>
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

import pango
import gtk
from kiwi.datatypes import currency
from kiwi.ui.widgets.list import Column, SummaryLabel, ColoredColumn

from stoqlib.exceptions import StoqlibError
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import payment_value_colorize
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
from stoqlib.gui.dialogs.renegotiationdetails import RenegotiationDetailsDialog
from stoqlib.gui.printing import print_report
from stoqlib.domain.interfaces import IClient, IOutPayment
from stoqlib.domain.person import Person
from stoqlib.domain.sale import SaleView, Sale
from stoqlib.domain.payment.views import PaymentChangeHistoryView
from stoqlib.domain.renegotiation import RenegotiationData
from stoqlib.reporting.sale import SaleOrderReport

_ = stoqlib_gettext



# A workaround to show negative values in the interface
class _TemporaryOutPayment(object):

    class method:
        description = None

    def __init__(self, payment):
        self.id = payment.id
        self.description = payment.description
        self.method.description = payment.method.description
        self.due_date = payment.due_date
        self.paid_date = payment.paid_date
        self.status_str = payment.get_status_str()
        self.base_value = -payment.base_value
        self.paid_value = -payment.paid_value


class SaleDetailsDialog(BaseEditor):
    gladefile = "SaleDetailsDialog"
    model_type = SaleView
    title = _(u"Sale Details")
    size = (750, 460)
    hide_footer = True
    proxy_widgets = ('status_lbl',
                     'client_lbl',
                     'salesperson_lbl',
                     'open_date_lbl',
                     'total_lbl',
                     'order_number',
                     'subtotal_lbl',
                     'surcharge_lbl',
                     'discount_lbl')

    def __init__(self, conn, model=None, visual_mode=False):
        """ Creates a new SaleDetailsDialog object

        @param conn: a database connection
        @param model: a L{stoqlib.domain.sale.Sale} object
        """
        BaseEditor.__init__(self, conn, model,
                            visual_mode=visual_mode)

    def _setup_columns(self):
        self.items_list.set_columns(self._get_items_columns())
        self.payments_list.set_columns(self._get_payments_columns())
        self.payments_info_list.set_columns(self._get_payments_info_columns())

    def _setup_summary_labels(self):
        summary_label = SummaryLabel(klist=self.payments_list,
                                     column='paid_value',
                                     label='<b>%s</b>' % _(u"Total:"),
                                     value_format='<b>%s</b>')
        summary_label.show()
        self.payments_vbox.pack_start(summary_label, False)

    def _get_payments(self, sale):
        for payment in sale.payments:
            if IOutPayment(payment, None):
                yield _TemporaryOutPayment(payment)
            else:
                yield payment

    def _setup_widgets(self):
        if not self.model.client_id:
            self.details_button.set_sensitive(False)
        self._setup_columns()

        self.sale_order = Sale.get(self.model.id, connection=self.conn)

        if (self.sale_order.status == Sale.STATUS_RETURNED or
            self.sale_order.status == Sale.STATUS_RENEGOTIATED):
            self.status_details_button.show()
        else:
            self.status_details_button.hide()

        sale_items = self.sale_order.get_items()
        self.items_list.add_list(sale_items)

        notes = [self.sale_order.notes]
        notes.extend([s.notes for s in sale_items if s.notes])
        buffer = gtk.TextBuffer()
        buffer.set_text(u'\n'.join(notes))
        self.notes.set_buffer(buffer)

        self.payments_list.add_list(self._get_payments(self.sale_order))
        changes = PaymentChangeHistoryView.select_by_group(
            self.sale_order.group,
            connection=self.conn)
        self.payments_info_list.add_list(changes)

        self._setup_summary_labels()

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

    def _get_items_columns(self):
        return [Column('sellable.code', _("Code"), sorted=True,
                       data_type=str, width=130),
                Column('sellable.base_sellable_info.description',
                       _("Description"), data_type=str, expand=True,
                       width=200),
                Column('quantity_unit_string', _("Quantity"), data_type=str,
                       width=100, justify=gtk.JUSTIFY_RIGHT),
                Column('price', _("Price"), data_type=currency, width=100),
                Column('total', _("Total"), data_type=currency, width=100)]

    def _get_payments_info_columns(self):
        return [Column('change_date', _(u"When"),
                        data_type=datetime.date, sorted=True,),
                Column('description', _(u"Payment"),
                        data_type=str, expand=True,
                        ellipsize=pango.ELLIPSIZE_END),
                Column('changed_field', _(u"Changed"),
                        data_type=str, justify=gtk.JUSTIFY_RIGHT),
                Column('from_value', _(u"From"),
                        data_type=str, justify=gtk.JUSTIFY_RIGHT),
                Column('to_value', _(u"To"),
                        data_type=str, justify=gtk.JUSTIFY_RIGHT),
                Column('reason', _(u"Reason"),
                        data_type=str, expand=True,
                        ellipsize=pango.ELLIPSIZE_END)]
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

    def on_status_details_button__clicked(self, button):
        if self.sale_order.status == Sale.STATUS_RETURNED:
            run_dialog(SaleReturnDetailsDialog, self, self.conn,
                       self.sale_order)
        elif self.sale_order.status == Sale.STATUS_RENEGOTIATED:
            # XXX: Rename to renegotiated
            run_dialog(RenegotiationDetailsDialog, self, self.conn,
                       self.sale_order.group.renegotiation)


class SaleReturnDetailsDialog(BaseEditor):
    gladefile = "HolderTemplate"
    model_type = Sale
    title = _(u"Sale Cancellation Details")
    size = (650, 350)
    hide_footer = True

    def setup_slaves(self):
        from stoqlib.gui.slaves.saleslave import SaleReturnSlave
        if self.model.status != Sale.STATUS_RETURNED:
            raise StoqlibError("Invalid status for sale order, it should be "
                               "cancelled")

        renegotiation = RenegotiationData.selectOneBy(sale=self.model,
                                                      connection=self.conn)
        if renegotiation is None:
            raise StoqlibError("Returned sales must have the renegotiation "
                               "information.")

        self.slave = SaleReturnSlave(self.conn, self.model, renegotiation,
                                     visual_mode=True)
        self.attach_slave("place_holder", self.slave)
