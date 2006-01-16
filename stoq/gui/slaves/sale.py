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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##
"""
stoq/gui/slaves/sale.py

    Slaves for sale management
"""

from kiwi.utils import gsignal
from kiwi.decorators import signal_block
from stoqlib.gui.editors import BaseEditorSlave

from stoq.lib.validators import get_price_format_str


class DiscountChargeSlave(BaseEditorSlave):
    """A slave for discounts and charge management

    Notes:
        after_value_changed_handler     = a function which will be called
                                          always after a discount or charge 
                                          is changed
    """
    gladefile = 'DiscountChargeSlave'
    proxy_widgets = ('discount_value',
                     'charge_value',
                     'discount_perc',
                     'charge_perc')
    gsignal('discount-changed')

    def __init__(self, conn, model, model_type):
        self.model_type = model_type
        BaseEditorSlave.__init__(self, conn, model)

    def setup_widgets(self):
        float_widgets = [self.discount_perc, self.discount_value, 
                         self.charge_perc, self.charge_value]
        format_str = get_price_format_str()
        for widget in float_widgets:
            widget.set_data_format(format_str)
        self.update_widget_status()

    def update_widget_status(self):
        charge_by_value = not self.charge_perc_ck.get_active()
        self.charge_value.set_sensitive(charge_by_value)
        self.charge_perc.set_sensitive(not charge_by_value)

        discount_by_value = not self.discount_perc_ck.get_active()
        self.discount_value.set_sensitive(discount_by_value)
        self.discount_perc.set_sensitive(not discount_by_value)

    def setup_discount_charge(self):
        if self.discount_perc_ck.get_active():
            self.proxy.update('discount_value')
        else:
            self.proxy.update('discount_percentage')

        if self.charge_perc_ck.get_active():
            self.proxy.update('charge_value')
        else:
            self.proxy.update('charge_percentage')
        self.emit('discount-changed')

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self.setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    DiscountChargeSlave.proxy_widgets)

    #
    # Kiwi callbacks
    #

    @signal_block('discount_value.changed')
    def after_discount_perc__changed(self, *args):
        self.setup_discount_charge()
   
    @signal_block('discount_perc.changed') 
    def after_discount_value__changed(self, *args):
        self.setup_discount_charge()
    
    @signal_block('charge_value.changed')
    def after_charge_perc__changed(self, *args):
        self.setup_discount_charge()
    
    @signal_block('charge_perc.changed')
    def after_charge_value__changed(self, *args):
        self.setup_discount_charge()

    def on_charge_perc_ck__toggled(self, *args):
        self.update_widget_status()

    def on_charge_value_ck__toggled(self, *args):
        self.update_widget_status()

    def on_discount_perc_ck__toggled(self, *args):
        self.update_widget_status()

    def on_discount_value_ck__toggled(self, *args):
        self.update_widget_status()
