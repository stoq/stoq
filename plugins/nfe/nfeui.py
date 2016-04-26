# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import logging
import os
import time

from stoqlib.domain.events import SaleStatusChangedEvent
from stoqlib.domain.returnedsale import ReturnedSale
from stoqlib.domain.sale import Sale
from stoqlib.domain.uiform import UIField
from stoqlib.gui.events import (SaleReturnWizardFinishEvent,
                                StockTransferWizardFinishEvent,
                                StockDecreaseWizardFinishEvent)
from stoqlib.api import api
from stoqlib.lib.osutils import get_application_dir
from stoqlib.lib.parameters import sysparam, ParameterDetails
from stoqlib.lib.permissions import PermissionManager
from stoqlib.lib.translation import stoqlib_gettext

from nfe.nfegenerator import NFeGenerator

_ = stoqlib_gettext
log = logging.getLogger(__name__)

params = [
    ParameterDetails(
        u'NFE_SERIAL_NUMBER',
        _(u'NF-e'),
        _(u'Fiscal document serial number'),
        _(u'Fiscal document serial number. Fill with 0 if the NF-e have no '
          u'series. This parameter only has effect if the nfe plugin is enabled.'),
        int, initial=1),

    ParameterDetails(
        u'NFE_DANFE_ORIENTATION',
        _(u'NF-e'),
        _(u'Danfe printing orientation'),
        _(u'Orientation to use for printing danfe. Portrait or Landscape'),
        int, initial=0,
        options={0: _(u'Portrait'),
                 1: _(u'Landscape')}),

    ParameterDetails(
        u'NFE_FISCO_INFORMATION',
        _(u'NF-e'),
        _(u'Additional Information for the Fisco'),
        _(u'Additional information to add to the NF-e for the Fisco'), unicode,
        initial=(u'Documento emitido por ME ou EPP optante pelo SIMPLES '
                 u'NACIONAL. Não gera Direito a Crédito Fiscal de ICMS e de '
                 u'ISS. Conforme Lei Complementar 123 de 14/12/2006.'),
        multiline=True),
]


class NFeUI(object):
    def __init__(self):
        self._setup_params()
        self._setup_events()

        pm = PermissionManager.get_permission_manager()
        pm.set('InvoiceLayout', pm.PERM_HIDDEN)
        pm.set('InvoicePrinter', pm.PERM_HIDDEN)

        # since the nfe plugin was enabled, the user must not be able to print
        # the regular fiscal invoice (replaced by the nfe).
        pm.set('app.sales.print_invoice', pm.PERM_HIDDEN)
        self._update_forms()

    #
    # Private
    #

    def _setup_params(self):
        for detail in params:
            sysparam.register_param(detail)

    def _setup_events(self):
        SaleReturnWizardFinishEvent.connect(self._on_SaleReturnWizardFinish)
        SaleStatusChangedEvent.connect(self._on_SaleStatusChanged)
        StockDecreaseWizardFinishEvent.connect(self._on_StockDecreaseWizardFinish)
        StockTransferWizardFinishEvent.connect(self._on_StockTransferWizardFinish)
        # TODO: Before enable the the NF-e generation. Save the invoice data,
        # in Invoice table (for each operation below).
        #NewLoanWizardFinishEvent.connect(self._on_NewLoanWizardFinish)

    def _get_save_location(self, operation_dir):
        stoq_dir = get_application_dir()

        # Until we finish the stoqnfe app, we will only export the nfe, so it
        # can be imported by an external application.
        # nfe_dir = os.path.join(stoq_dir, 'generated_nfe')
        nfe_dir = os.path.join(stoq_dir, 'exported_nfe',
                               time.strftime('%Y'), time.strftime('%m'),
                               time.strftime('%d'), operation_dir)

        if not os.path.isdir(nfe_dir):
            os.makedirs(nfe_dir)

        return nfe_dir

    def _can_create_nfe(self, operation):
        # FIXME: certainly, there is more conditions to check before we create
        #        the nfe. Maybe the user should have a chance to fix the
        #        missing information before we create the nfe.
        # return operation.recipient is not None

        # Since we are only exporting the nfe there is no problem if there is
        # some missing information...

        # ... except the recipient
        if not operation.recipient:
            return False

        return True

    def _create_nfe(self, operation, store, operation_dir=''):
        if self._can_create_nfe(operation):
            generator = NFeGenerator(operation, store)
            generator.generate()
            generator.export_txt(location=self._get_save_location(operation_dir))

    def _update_forms(self):
        store = api.new_store()
        # To generate a NF-e this fields are mandatory
        forms = [u'street', u'district', u'city', u'state', u'country',
                 u'street_number']
        fields = store.find(UIField, UIField.field_name.is_in(forms))
        for field in fields:
            field.update_field(mandatory=True, visible=True)
        store.commit()

    #
    # Events
    #

    def _on_SaleStatusChanged(self, sale, old_status):
        if sale.status == Sale.STATUS_CONFIRMED:
            operation_dir = _('Sales')
            self._create_nfe(sale, sale.store, operation_dir)

    def _on_NewLoanWizardFinish(self, loan):
        operation_dir = _('Loans')
        self._create_nfe(loan, loan.store, operation_dir)

    def _on_StockTransferWizardFinish(self, transfer):
        operation_dir = _('Transfers')
        self._create_nfe(transfer, transfer.store, operation_dir)

    def _on_StockDecreaseWizardFinish(self, stock_decrease):
        operation_dir = _('Stock decreases')
        self._create_nfe(stock_decrease, stock_decrease.store, operation_dir)

    def _on_SaleReturnWizardFinish(self, returned_sale):
        if returned_sale.status == ReturnedSale.STATUS_CONFIRMED:
            operation_dir = _('Returned sales')
            self._create_nfe(returned_sale, returned_sale.store, operation_dir)
