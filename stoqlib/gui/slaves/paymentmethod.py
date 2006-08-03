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
## Author(s):    Evandro Vale Miquelito      <evandro@async.com.br>
##
##
""" Slaves for payment methods management"""

from kiwi.ui.delegates import SlaveDelegate
from kiwi.utils import gsignal

from stoqlib.gui.base.editors import BaseEditorSlave
from stoqlib.domain.interfaces import IGiftCertificatePM, IMultiplePM, IMoneyPM
from stoqlib.domain.payment.destination import PaymentDestination
from stoqlib.domain.payment.methods import (AbstractCheckBillAdapter,
                                            FinanceDetails,
                                            get_active_pm_ifaces)
from stoqlib.exceptions import StoqlibError

class CheckBillSettingsSlave(BaseEditorSlave):
    model_type = AbstractCheckBillAdapter
    gladefile = 'CheckBillSettingsSlave'
    proxy_widgets = ('installments_number',
                     'monthly_interest',
                     'daily_penalty')

    def setup_proxies(self):
        self.add_proxy(self.model, CheckBillSettingsSlave.proxy_widgets)


class InstallmentsNumberSettingsSlave(BaseEditorSlave):
    gladefile = 'InstallmentsNumberSettingsSlave'
    proxy_widgets = ('installments_number',)

    def __init__(self, conn, model):
        self.model_type = type(model)
        BaseEditorSlave.__init__(self, conn, model)

    def setup_proxies(self):
        self.add_proxy(self.model,
                       InstallmentsNumberSettingsSlave.proxy_widgets)


class FinanceDetailsSlave(BaseEditorSlave):
    gladefile = 'FinanceDetailsSlave'
    model_type = FinanceDetails
    proxy_widgets = ('destination',
                     'commission',
                     'receive_days')

    def setup_proxies(self):
        table = PaymentDestination
        destinations = [(p.description, p)
                        for p in table.select(connection=self.conn)]
        self.destination.prefill(destinations, sort=True)
        self.add_proxy(self.model,
                       FinanceDetailsSlave.proxy_widgets)

class SelectPaymentMethodSlave(SlaveDelegate):
    """ This slave show a radion button group with three payment method options:
    Money, Gift Certificate and Other (any other method supported by the system).
    The visibility of these buttons are directly related to payment method
    availabiltiy in the company.
    """
    gladefile = 'SelectPaymentMethodSlave'
    gsignal('method-changed', object)

    def __init__(self, method_iface=IMoneyPM):
        SlaveDelegate.__init__(self, gladefile=SelectPaymentMethodSlave.gladefile)
        self._setup_widgets()
        self._select_payment_method_by_iface(method_iface)

    def _select_payment_method_by_iface(self, method_iface):
        if not method_iface in get_active_pm_ifaces():
            raise StoqlibError("The payment method %r can't be used, since "
                               "it isn't active." % method_iface)
        if method_iface == IMoneyPM:
            widget = self.cash_check
        elif method_iface == IGiftCertificatePM:
            widget = self.certificate_check
        else:
            widget = self.othermethods_check
        widget.set_active(True)

    def _setup_widgets(self):
        active_pm_ifaces = get_active_pm_ifaces()
        if not IGiftCertificatePM in active_pm_ifaces:
            self.certificate_check.hide()
        else:
            active_pm_ifaces.remove(IGiftCertificatePM)
        if not IMoneyPM in active_pm_ifaces:
            raise StoqlibError("The money payment method should be always "
                               "available")
        active_pm_ifaces.remove(IMoneyPM)
        if not active_pm_ifaces:
            self.othermethods_check.hide()

    def get_selected_method(self):
        if self.cash_check.get_active():
            return IMoneyPM
        elif self.certificate_check.get_active():
            return IGiftCertificatePM
        elif self.othermethods_check.get_active():
            return IMultiplePM
        else:
            raise StoqlibError("You should have a valid payment method "
                               "selected at this point.")

    #
    # Kiwi callbacks
    #

    def on_cash_check__toggled(self, *args):
        self.emit('method-changed', IMoneyPM)

    def on_certificate_check__toggled(self, *args):
        self.emit('method-changed', IGiftCertificatePM)

    def on_othermethods_check__toggled(self, *args):
        self.emit('method-changed', IMultiplePM)
