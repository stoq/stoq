# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Classes for sale details """


import datetime

import pango
import gtk
from kiwi.datatypes import currency
from kiwi.ui.widgets.list import Column, SummaryLabel, ColoredColumn

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.defaults import payment_value_colorize
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
from stoqlib.domain.sale import Sale
from stoqlib.domain.payment.views import PaymentChangeHistoryView
from stoqlib.domain.payment.renegotiation import PaymentRenegotiation

_ = stoqlib_gettext


class _RenegotiationItem(object):
    def __init__(self, payment_group):
        parent = payment_group.get_parent()
        self.parent_id = parent.id
        self.open_date = parent.open_date

        if isinstance(parent, Sale):
            desc = "Sale %04d" % (parent.id)
            self.total_amount = parent.total_amount
        elif isinstance(parent, PaymentRenegotiation):
            desc = "Renegotiation %04d" % (parent.id)
            self.total_amount = parent.total

        self.description = desc


class RenegotiationDetailsDialog(BaseEditor):
    gladefile = "RenegotiationDetailsDialog"
    model_type = PaymentRenegotiation
    title = _(u"Renegotiation Details")
    size = (750, 460)
    hide_footer = True
    proxy_widgets = ('status_lbl',
                     'client_lbl',
                     'responsible_name',
                     'open_date_lbl',
                     'total_lbl',
                     'notes',
                     'id',
                     'subtotal_lbl',
                     'surcharge_lbl',
                     'discount_lbl')

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

    def _get_renegotiation_items(self):
        for item in self.model.get_items():
            yield _RenegotiationItem(item)

    def _setup_widgets(self):
        if not self.model.client:
            self.details_button.set_sensitive(False)
        self._setup_columns()

        if self.model.status == PaymentRenegotiation.STATUS_RENEGOTIATED:
            self.status_details_button.show()
        else:
            self.status_details_button.hide()

        self.items_list.add_list(self._get_renegotiation_items())
        self.payments_list.add_list(self.model.payments)
        changes = PaymentChangeHistoryView.select_by_group(
            self.model.group, connection=self.conn)
        self.payments_info_list.add_list(changes)

        self._setup_summary_labels()

    def _get_payments_columns(self):
        return [Column('id', "#", data_type=int, width=50,
                       format='%04d', justify=gtk.JUSTIFY_RIGHT),
                Column('method.description', _("Type"),
                       data_type=str, width=60),
                Column('description', _("Description"), data_type=str,
                       width=150, expand=True),
                Column('due_date', _("Due date"), sorted=True,
                       data_type=datetime.date, width=90,
                       justify=gtk.JUSTIFY_RIGHT),
                Column('paid_date', _("Paid date"),
                       data_type=datetime.date, width=90),
                Column('status_str', _("Status"), data_type=str, width=80),
                ColoredColumn('base_value', _("Value"), data_type=currency,
                              width=90, color='red',
                              justify=gtk.JUSTIFY_RIGHT,
                              data_func=payment_value_colorize),
                ColoredColumn('paid_value', _("Paid value"), data_type=currency,
                              width=92, color='red',
                              justify=gtk.JUSTIFY_RIGHT,
                              data_func=payment_value_colorize)]

    def _get_items_columns(self):
        return [Column('description', _("Description"), sorted=True,
                       data_type=unicode, expand=True),
                Column('open_date', _("Open date"), data_type=datetime.date,
                       width=90),
                Column('total_amount', _("Total"), data_type=currency, width=100)]

    def _get_payments_info_columns(self):
        return [Column('change_date', _(u"When"),
                        data_type=datetime.date, sorted=True, ),
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
        self.add_proxy(self.model, RenegotiationDetailsDialog.proxy_widgets)

    #
    # Kiwi handlers
    #

    def on_details_button__clicked(self, button):
        run_dialog(ClientDetailsDialog, self, self.conn, self.model.client)

    def on_status_details_button__clicked(self, button):
        run_dialog(RenegotiationDetailsDialog, self, self.conn,
                   self.model.group.renegotiation)
