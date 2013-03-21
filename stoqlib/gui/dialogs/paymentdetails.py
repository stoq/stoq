# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source <http://www.async.com.br>
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

import datetime

import gtk
import pango

from kiwi.currency import currency
from kiwi.ui.objectlist import Column

from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import PaymentChangeHistoryView
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class LonelyPaymentDetailsDialog(BaseEditor):
    gladefile = 'LonelyPaymentDetailsDialog'
    size = (550, 350)
    model_type = Payment
    proxy_widgets = ['value',
                     'interest',
                     'paid_value',
                     'penalty',
                     'description',
                     'discount',
                     'due_date',
                     'paid_date',
                     'status']

    def __init__(self, store, payment):
        BaseEditor.__init__(self, store, payment)
        self._setup_widgets()

    def _setup_widgets(self):
        self.payment_info_list.set_columns(self._get_columns())
        changes = PaymentChangeHistoryView.find_by_group(self.store, self.model.group)
        self.payment_info_list.add_list(changes)

        # workaround to improve the dialog looking
        if self.model.paid_value:
            penalty = self._get_penalty()
            self.penalty.update(penalty)
            self.interest.update(self.model.interest)
        else:
            self.paid_value.update(currency(0))

    def _get_penalty(self):
        penalty = (self.model.paid_value -
                  (self.model.value - self.model.discount + self.model.interest))

        return currency(penalty)

    def _get_columns(self):
        return [Column('change_date', _("When"),
                       data_type=datetime.date, sorted=True, ),
                Column('description', _("Payment"),
                       data_type=str, expand=True,
                       ellipsize=pango.ELLIPSIZE_END),
                Column('changed_field', _("Changed"),
                       data_type=str, justify=gtk.JUSTIFY_RIGHT),
                Column('from_value', _("From"),
                       data_type=str, justify=gtk.JUSTIFY_RIGHT),
                Column('to_value', _("To"),
                       data_type=str, justify=gtk.JUSTIFY_RIGHT),
                Column('reason', _("Reason"),
                       data_type=str, expand=True,
                       ellipsize=pango.ELLIPSIZE_END)]

    #
    # BaseEditor
    #

    def setup_proxies(self):
        self._proxy = self.add_proxy(
            self.model, LonelyPaymentDetailsDialog.proxy_widgets)

    def get_title(self, model):
        if model is None:
            return

        if model.is_inpayment():
            return _('Receiving Details')

        if model.is_outpayment():
            return _('Payment Details')
