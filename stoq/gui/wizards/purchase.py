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
stoq/gui/wizards/purchase.py:

    Purchase wizard definition
"""

import gettext

from stoqlib.gui.wizards import BaseWizardStep, BaseWizard

from stoq.lib.validators import get_price_format_str
from stoq.domain.person import Person
from stoq.domain.purchase import PurchaseOrder
from stoq.domain.interfaces import ISupplier, IBranch, ITransporter
from stoq.gui.wizards.person import run_person_role_dialog
from stoq.gui.editors.person import SupplierEditor, TransporterEditor

_ = gettext.gettext


#
# Wizard Steps
#


class FinishPurchaseStep(BaseWizardStep):
    gladefile = 'FinishPurchaseStep'
    model_type = PurchaseOrder
    widgets = ('salesperson_name', 
               'receival_date',
               'transporter',
               'notes',
               'transporter_button')

    def __init__(self, wizard, previous, conn, model):
        BaseWizardStep.__init__(self, conn, wizard, model, previous)

    def _setup_transporter_entry(self):
        table = Person.getAdapterClass(ITransporter)
        transporters = table.get_active_transporters(self.conn)
        names = [t.get_adapted().name for t in transporters]
        self.transporter.set_completion_strings(names, list(transporters))

    #
    # WizardStep hooks
    #

    def has_next_step(self):
        return False

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self._setup_transporter_entry()
        self.proxy = self.add_proxy(self.model, self.widgets)

    #
    # Kiwi callbacks
    #

    def on_transporter_button__clicked(self, *args):
        if run_person_role_dialog(TransporterEditor, self, self.conn, 
                                  self.model.transporter):
            self.conn.commit()
            self._setup_transporter_entry()


class StartPurchaseStep(BaseWizardStep):
    gladefile = 'StartPurchaseStep'
    model_type = PurchaseOrder
    proxy_widgets = ('open_date', 
                     'order_number',
                     'supplier',
                     'branch',
                     'supplier_button',
                     'freight')
    widgets = proxy_widgets + ('cif_radio',
                               'fob_radio')

    def __init__(self, wizard, conn, model):
        BaseWizardStep.__init__(self, conn, wizard, model)
        self._update_widgets()

    def _setup_supplier_entry(self):
        table = Person.getAdapterClass(ISupplier)
        suppliers = table.get_active_suppliers(self.conn)
        names = [s.get_adapted().name for s in suppliers]
        self.supplier.set_completion_strings(names, list(suppliers))

    def _setup_widgets(self):
        self._setup_supplier_entry()
        table = Person.getAdapterClass(IBranch)
        branches = table.get_active_branches(self.conn)
        items = [(s.get_adapted().name, s) for s in branches]
        self.branch.prefill(items)
        self.freight.set_data_format(get_price_format_str())

    def _update_widgets(self):
        has_freight = self.fob_radio.get_active()
        self.freight.set_sensitive(has_freight)

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def next_step(self):
        if self.cif_radio.get_active():
            self.model.freight_type = self.model_type.FREIGHT_CIF
        else:
            self.model.freight_type = self.model_type.FREIGHT_FOB
        return FinishPurchaseStep(self.wizard, self, self.conn, 
                                  self.model)

    def has_previous_step(self):
        return False

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    #
    # Kiwi callbacks
    #

    def on_cif_radio__toggled(self, *args):
        self._update_widgets()

    def on_fob_radio__toggled(self, *args):
        self._update_widgets()

    def on_supplier_button__clicked(self, *args):
        if run_person_role_dialog(SupplierEditor, self, self.conn, 
                                  self.model.supplier):
            self.conn.commit()
            self._setup_supplier_entry()


#
# Main wizard
#


class PurchaseWizard(BaseWizard):
    size = (600, 400)
    
    def __init__(self, conn, model=None):
        title = self._get_title(model)
        model = model or self._create_model(conn)
        if model.status != PurchaseOrder.ORDER_PENDING:
            raise ValueError('Invalid order status. It should'
                             'be ORDER_PENDING')
        first_step = StartPurchaseStep(self, conn, model)
        BaseWizard.__init__(self, conn, first_step, model, title=title)

    def _get_title(self, model=None):
        if not model:
            return _('New Order')
        return _('Edit Order')

    def _create_model(self, conn):
        status = PurchaseOrder.ORDER_PENDING
        return PurchaseOrder(supplier=None, branch=None, status=status,
                             connection=conn)

    #
    # WizardStep hooks
    #

    def finish(self):
        # TODO generate preview payments for this order
        self.model.validate()
        self.retval = self.model
        self.close()
