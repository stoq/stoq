# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
""" Sale return wizards definition """

from stoqlib.domain.events import ECFIsLastSaleEvent
from stoqlib.domain.payment.operation import register_payment_operations
from stoqlib.domain.sale import Sale, SaleView
from stoqlib.lib.message import info
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.slaves.saleslave import SaleReturnSlave


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
        self.wizard.enable_finish()
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def next_step(self):
        return

    #
    # BaseEditorSlave hooks
    #

    def setup_slaves(self):
        self.order = Sale.get(self.model.id, connection=self.conn)
        self.wizard.renegotiation = self.order.create_sale_return_adapter()
        self.slave = SaleReturnSlave(self.conn, self.order,
                                     self.wizard.renegotiation)
        self.slave.connect('on-penalty-changed', self.on_penalty_changed)
        self.attach_slave("place_holder", self.slave)

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
        register_payment_operations()
        self.renegotiation = None
        first_step = SaleReturnStep(conn, self, model)
        BaseWizard.__init__(self, conn, first_step, model)

    #
    # BaseWizard hooks
    #

    def finish(self):
        sale = Sale.get(self.model.id, connection=self.conn)
        ecf_last_sale = ECFIsLastSaleEvent.emit(sale)
        if ecf_last_sale:
            info(_("That is last sale in ECF. Return using the menu "
                   "ECF - Cancel Last Document"))
            return
        sale.return_(self.renegotiation)

        self.retval = True
        self.close()
