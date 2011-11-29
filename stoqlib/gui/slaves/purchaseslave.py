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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Slaves for purchase management """


from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.lib.defaults import interval_types


class PurchasePaymentSlave(BaseEditorSlave):
    gladefile = 'PurchasePaymentSlave'
    model_type = PaymentGroup
    proxy_widgets = ('interval_type_combo',
                     'intervals',
                     'installments_number')

    def _setup_widgets(self):
        items = [(desc, constant)
                    for constant, desc in interval_types.items()]
        self.interval_type_combo.prefill(items)

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    PurchasePaymentSlave.proxy_widgets)
        self._update_widgets()

    def on_installments_number__changed(self, widget):
        self._update_widgets()

    def _update_widgets(self):
        installments_is_one = self.installments_number.get_value() == 1
        self.intervals.set_sensitive(not installments_is_one)
        self.interval_type_combo.set_sensitive(not installments_is_one)
