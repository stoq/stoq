# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##
##
""" Sale return wizards definition """

from kiwi.argcheck import argcheck

from stoqlib.exceptions import StoqlibError
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.domain.sale import (Sale, SaleView,
                                 GiftCertificateOverpaidSettings)
from stoqlib.domain.interfaces import IPaymentGroup
from stoqlib.domain.renegotiation import AbstractRenegotiationAdapter
from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.wizards.salewizard import SaleRenegotiationOverpaidStep


_ = stoqlib_gettext


#
# Wizard Steps
#

class SaleReturnStep(WizardEditorStep):
    gladefile = 'HolderTemplate'
    model_type = SaleView

    def __init__(self, conn, wizard, model):
        WizardEditorStep.__init__(self, conn, wizard, model)

    #
    # WizardStep hooks
    #

    def post_init(self):
        if not self.renegotiation_data.paid_total:
            self.wizard.enable_finish()
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def next_step(self):
        overpaid_value = self.renegotiation_data.get_return_total()
        if not overpaid_value:
            # Return None here means call wizard.finish, which is exactly
            # what we need
            return

        group = IPaymentGroup(self.order)
        if not group:
            raise StoqlibError("You should have a payment group defined "
                               "at this point")

        step_class = SaleRenegotiationOverpaidStep
        step = step_class(self.wizard, self, self.conn, self.order, group,
                          overpaid_value)
        step.connect('on-validate-step',
                     self.wizard.set_gift_certificate_settings)
        return step

    #
    # BaseEditorSlave hooks
    #

    def setup_slaves(self):
        from stoqlib.gui.slaves.sale import SaleReturnSlave
        self.order = Sale.get(self.model.id, connection=self.conn)
        self.adapter = self.order.create_sale_return_adapter()
        self.renegotiation_data = self.adapter.get_adapted()
        self.slave = SaleReturnSlave(self.conn, self.order, self.adapter)
        self.slave.connect('on-penalty-changed', self.on_penalty_changed)
        self.attach_slave("place_holder", self.slave)
        self.wizard.set_renegotiation_adapter(self.adapter)

    #
    # Callbacks
    #

    def on_penalty_changed(self, slave, return_total):
        if not return_total:
            self.wizard.enable_finish()
        else:
            self.wizard.disable_finish()

#
# Main wizard
#


class SaleReturnWizard(BaseWizard):
    size = (450, 350)
    title = _('Return Sale Order')

    def __init__(self, conn, model):
        self._gift_certificate_settings = None
        self._renegotiation_adapter = None
        first_step = SaleReturnStep(conn, self, model)
        BaseWizard.__init__(self, conn, first_step, model)

    @argcheck(object, GiftCertificateOverpaidSettings)
    def set_gift_certificate_settings(self, slave, settings):
        self._gift_certificate_settings = settings

    @argcheck(AbstractRenegotiationAdapter)
    def set_renegotiation_adapter(self, adapter):
        self._renegotiation_adapter = adapter

    #
    # BaseWizard hooks
    #

    def finish(self):
        order = Sale.get(self.model.id, connection=self.conn)
        settings = self._gift_certificate_settings
        self._renegotiation_adapter.confirm(order, settings)
        self.retval = True
        self.close()
