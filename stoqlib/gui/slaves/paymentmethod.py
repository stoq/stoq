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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):    Evandro Vale Miquelito      <evandro@async.com.br>
##
##
""" Slaves for payment methods management"""

from kiwi.ui.delegates import SlaveDelegate
from kiwi.utils import gsignal

from stoqlib.gui.base.editors import BaseEditorSlave
from stoqlib.domain.interfaces import (ICheckPM, ICardPM, IBillPM,
                                       IFinancePM, IGiftCertificatePM,
                                       IMultiplePM, IMoneyPM)
from stoqlib.domain.payment.destination import PaymentDestination
from stoqlib.domain.payment.methods import (AbstractCheckBillAdapter,
                                            FinanceDetails)


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


class SelectCashMethodSlave(SlaveDelegate):
    toplevel = gladefile = 'SelectCashMethodSlave'


class SelectPaymentMethodSlave(SlaveDelegate):
    toplevel = gladefile = 'SelectPaymentMethodSlave'
    gsignal('method-changed', object)

    def __init__(self, active_pm_ifaces):
        SlaveDelegate.__init__(self, toplevel=self.toplevel,
                               gladefile=self.gladefile)
        self._setup_widgets(active_pm_ifaces)

    def _setup_widgets(self, active_pm_ifaces):
        if len(active_pm_ifaces) == 1:
            raise ValueError("You should have more than one "
                             "active payment methods to use "
                             "this slave")
        if not IGiftCertificatePM in active_pm_ifaces:
            self.certificate_check.hide()
            return
        otherm_ifaces = [iface for iface in (ICheckPM, ICardPM,
                                             IBillPM, IFinancePM)
                                if iface in active_pm_ifaces]
        if not otherm_ifaces:
            self.othermethods_check.hide()

    #
    # Kiwi callbacks
    #

    def on_cash_check__toggled(self, *args):
        self.emit('method-changed', IMoneyPM)

    def on_certificate_check__toggled(self, *args):
        self.emit('method-changed', IGiftCertificatePM)

    def on_othermethods_check__toggled(self, *args):
        self.emit('method-changed', IMultiplePM)
