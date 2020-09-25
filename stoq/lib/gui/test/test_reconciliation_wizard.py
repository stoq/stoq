# -*- coding: utf-8 -*-
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

import contextlib
from gi.repository import Gtk
import mock

from stoqlib.domain.receiving import ReceivingInvoice
from stoq.lib.gui.test.uitestutils import GUITest
from stoq.lib.gui.wizards.reconciliationwizard import PurchaseReconciliationWizard
from stoqlib.lib.dateutils import localdatetime


class TestPurchaseReconciliationWizard(GUITest):
    def test_complete_reconciliation(self):
        sellable = self.create_sellable()
        purchase_item = self.create_purchase_order_item(sellable=sellable)
        purchase = purchase_item.order
        purchase.identifier = 65432
        purchase.group = None
        receiving = self.create_receiving_order(purchase_order=purchase)
        receiving.identifier = 45633
        receiving.receival_date = localdatetime(2012, 10, 9)
        receiving_item = self.create_receiving_order_item(receiving_order=receiving,
                                                          purchase_item=purchase_item,
                                                          quantity=2)
        receiving.receiving_invoice = None
        wizard = PurchaseReconciliationWizard(self.store)

        step = wizard.get_current_step()
        self.assertNotSensitive(wizard, ['next_button'])
        self.click(step.search.search_button)
        order_view = step.search.results[0]
        step.search.results.select(order_view)
        self.assertSensitive(wizard, ['next_button'])
        self.check_wizard(wizard, 'wizard-reconciliation-receiving-selection-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertSensitive(wizard, ['next_button'])
        self.check_wizard(wizard, 'wizard-reconciliation-check-receiving-cost-step')
        receiving_item.cost = 130
        step._update_view()
        self.assertEqual(step.total_received.read(), 260)
        self.click(wizard.next_button)
        self.assertEqual(type(wizard.model), ReceivingInvoice)
        invoice = wizard.model
        invoice.identifier = 22222
        # Test cell data func
        renderer = Gtk.CellRendererText()
        col = step.purchase_items.get_columns()[6]
        item = step.purchase_items[0]
        step._on_purchase_items__cell_data_func(col, renderer, item, 'aa')
        self.assertTrue(renderer.get_property('editable-set'))
        self.assertTrue(renderer.get_property('editable'))

        step = wizard.get_current_step()
        self.assertNotSensitive(wizard, ['next_button'])
        step.invoice_slave.invoice_number.update(1)
        self.assertSensitive(wizard, ['next_button'])
        self.check_wizard(wizard, 'wizard-reconciliation-receiving-invoice-step')
        self.click(wizard.next_button)

        self.assertSensitive(wizard, ['next_button'])
        self.check_wizard(wizard, 'wizard-reconciliation-payment-step')
        with contextlib.nested(
                mock.patch.object(self.store, 'close'),
                mock.patch.object(self.store, 'commit')) as (close, commit):
            self.click(wizard.next_button)
