# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):        Henrique Romano            <henrique@async.com.br>
##                   Evandro Vale Miquelito     <evandro@async.com.br>
##
"""
stoq/gui/editors/till.py:

    Editors implementation for open/close operation on till operation.
"""

import gettext

from stoqlib.gui.editors import BaseEditor
from kiwi.datatypes import ValidationError

from stoq.domain.till import Till
from stoq.lib.validators import get_price_format_str

_ = gettext.gettext

class TillOpeningEditor(BaseEditor):
    model_name = _('Till Opening')
    model_type = Till
    gladefile = 'TillOpening'
    widgets = ('open_date', 
               'initial_cash_amount')

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)

    def _setup_widgets(self):
        self.initial_cash_amount.set_data_format(get_price_format_str())



    #
    # BaseEditor hooks
    # 



    def get_title_model_attribute(self, model):
        return self.model_name

    def setup_proxies(self):
        self.model.open_till()
        self._setup_widgets()
        self.add_proxy(self.model, self.widgets)


class TillClosingEditor(BaseEditor):
    model_name = _('Till Closing')
    model_type = Till
    gladefile = 'TillClosing'
    widgets = ('closing_date',
               'final_cash_amount',
               'balance_to_send')

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)
        self.total_balance = model.get_balance()

    def _setup_widgets(self):
        for widget in (self.balance_to_send, self.final_cash_amount):
            widget.set_data_format(get_price_format_str())

    def update_final_cash_amount(self):
        balance_to_send = self.model.balance_sent or 0.0
        self.model.final_cash_amount = self.total_balance - balance_to_send
        self.proxy.update('final_cash_amount')

    def update_balance_to_send(self):
        final_cash_amount = self.model.final_cash_amount or 0.0
        self.model.balance_sent = self.total_balance - final_cash_amount 
        self.proxy.update('balance_sent')



    #
    # BaseEditor hooks
    # 



    def get_title_model_attribute(self, model):
        return self.model_name

    def setup_proxies(self):
        self.model.close_till()
        self.final_cash = self.model.final_cash_amount
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, self.widgets)



    #
    # Kiwi handlers
    #



    def after_final_cash_amount__validate(self, widget, value):
        if value <= self.final_cash:
            return
        return ValidationError(_("You can not specifiy a final"
                                 " cash amount greater than the "
                                 "calculated value."))

    def after_balance_to_send__changed(self, *args):
        self.handler_block(self.final_cash_amount, 'changed')
        self.update_final_cash_amount()
        self.handler_unblock(self.final_cash_amount, 'changed')

    def after_final_cash_amount__changed(self, *args):
        self.handler_block(self.balance_to_send, 'changed')
        self.update_balance_to_send()
        self.handler_unblock(self.balance_to_send, 'changed')

