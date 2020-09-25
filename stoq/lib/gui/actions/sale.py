# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Copyright (C) 2018 Async Open Source <http://www.async.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
# Author(s): Stoq Team <stoq-devel@async.com.br>
#


from stoqlib.api import api
from stoqlib.domain.workorder import WorkOrder
from stoqlib.domain.sale import SaleView
from stoq.lib.gui.actions.base import BaseActions, action
from stoq.lib.gui.dialogs.saledetails import SaleDetailsDialog
from stoq.lib.gui.wizards.salequotewizard import SaleQuoteWizard
from stoq.lib.gui.wizards.workorderquotewizard import WorkOrderQuoteWizard
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class SaleActions(BaseActions):

    group_name = 'sale'

    def model_set(self, model):
        self.set_action_enabled('Details', model)
        self.set_action_enabled('Edit', model and model.can_edit())

    #
    #   Actions
    #

    @action('Details')
    def details(self, sale):
        with api.new_store() as store:
            sale_view = store.find(SaleView, id=sale.id).one()
            # sale details dialog uses SaleView instead of sale
            self.run_dialog(SaleDetailsDialog, store, sale_view)
            # XXX: We are setting this manually because the nfce plugin might change
            # the model. The infrastructure must be changed to consider this situation
            store.retval = store.get_pending_count() > 0

        if store.committed:
            self.emit('model-edited', sale)

    @action('Edit')
    def edit(self, sale):
        with api.new_store() as store:
            sale = store.fetch(sale)

            # If we have work orders on the sale (the sale is a pre-sale), we need
            # to run WorkOrderQuoteWizard instead of SaleQuoteWizard
            has_workorders = not WorkOrder.find_by_sale(store, sale).is_empty()
            if has_workorders:
                wizard = WorkOrderQuoteWizard
            else:
                wizard = SaleQuoteWizard
            self.run_dialog(wizard, store, sale)

        if store.committed:
            self.emit('model-edited', sale)
