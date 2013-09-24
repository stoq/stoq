# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

import mock
import gtk

from stoqlib.domain.base import Domain
from stoqlib.domain.product import Storable
from stoqlib.gui.base.lists import SimpleListDialog
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.wizards.purchasewizard import PurchaseWizard
from stoqlib.gui.wizards.purchasequotewizard import (QuotePurchaseWizard,
                                                     ReceiveQuoteWizard)
from stoqlib.lib.dateutils import localdate, localdatetime
from stoqlib.lib.parameters import sysparam
from stoqlib.reporting.purchase import PurchaseQuoteReport


class TestQuotePurchaseeWizard(GUITest):
    def _check_start_step(self, uitest=''):
        start_step = self.wizard.get_current_step()
        start_step.quote_deadline.update(localdatetime(2020, 1, 1))
        start_step.quote_group.set_text("12345")
        if uitest:
            self.check_wizard(self.wizard, uitest)
        self.click(self.wizard.next_button)

    def _check_item_step(self, uitest=''):
        item_step = self.wizard.get_current_step()
        product = self.create_product()
        Storable(product=product, store=self.store)
        item_step.sellable_selected(product.sellable)
        self.click(item_step.add_sellable_button)
        if uitest:
            self.check_wizard(self.wizard, uitest)
        self.click(self.wizard.next_button)

    def _check_supplier_step(self, uitest=''):
        if uitest:
            self.check_wizard(self.wizard, uitest)
        self.click(self.wizard.next_button)

    @mock.patch('stoqlib.database.runtime.StoqlibStore.commit')
    @mock.patch('stoqlib.domain.purchase.PurchaseOrder.delete')
    def test_create(self, delete, commit):
        # Allow creating purchases in the past.
        sysparam.set_bool(self.store, 'ALLOW_OUTDATED_OPERATIONS', True)

        self.wizard = QuotePurchaseWizard(self.store)
        self.wizard.model.branch = self.create_branch()
        self.wizard.model.identifier = 12345
        self.wizard.model.open_date = localdate(2010, 1, 3).date()
        self._check_start_step('wizard-purchasequote-start-step')
        self._check_item_step('wizard-purchasequote-item-step')

        supplier_step = self.wizard.get_current_step()
        supplier_step.quoting_list.select(supplier_step.quoting_list[0])
        patch = 'stoqlib.gui.wizards.purchasequotewizard.run_dialog'
        with mock.patch(patch) as run_dialog:
            self.click(supplier_step.missing_products_button)
            run_dialog.assert_called_once_with(SimpleListDialog, self.wizard,
                                               supplier_step.product_columns,
                                               set([]), title='Missing Products')

        sellable = supplier_step.model.get_items()[0].sellable
        with mock.patch(patch) as run_dialog:
            self.click(supplier_step.view_products_button)
            run_dialog.assert_called_once_with(
                SimpleListDialog, self.wizard, supplier_step.product_columns,
                [sellable], title='Products supplied by Supplier')

        patch = 'stoqlib.gui.wizards.purchasequotewizard.print_report'
        with mock.patch(patch) as print_report:
            self.click(supplier_step.print_button)
            print_report.assert_called_once_with(
                PurchaseQuoteReport, self.wizard.model)

        self._check_supplier_step('wizard-purchasequote-supplier-step')

        # FIXME: How many times?
        self.assertEquals(commit.call_count, 1)

        purchase = self.wizard.model
        models = [purchase]
        models.extend(purchase.get_items())

        self.check_wizard(self.wizard, 'wizard-purchasequote-finish-step',
                          models=models)


class TestReceiveQuoteWizard(GUITest):
    def _check_start_step(self, uitest=''):
        if uitest:
            self.check_wizard(self.wizard, uitest)
        self.click(self.wizard.next_button)

    @mock.patch('stoqlib.gui.wizards.purchasequotewizard.run_dialog')
    @mock.patch('stoqlib.gui.wizards.purchasequotewizard.yesno')
    def test_create(self, yesno, run_dialog):
        # Allow creating purchases in the past.
        sysparam.set_bool(self.store, 'ALLOW_OUTDATED_OPERATIONS', True)

        quotation = self.create_quotation()
        quotation.identifier = 12345
        quotation.group.identifier = 67890

        def _purchase_clone():
            self.purchase_clone = Domain.clone(self.purchase)
            return self.purchase_clone

        purchase = self.purchase = quotation.purchase
        purchase.clone = _purchase_clone
        purchase.open_date = localdate(2012, 1, 1).date()
        self.create_purchase_order_item(purchase)

        self.wizard = ReceiveQuoteWizard(self.store)
        start_step = self.wizard.get_current_step()
        start_step.search.refresh()
        start_step.search.results.select(start_step.search.results[0])
        self._check_start_step('wizard-receivequote-start-step')
        self._check_start_step('wizard-receivequote-item-step')

        item_step = self.wizard.get_current_step()
        new_store = 'stoqlib.gui.wizards.purchasequotewizard.api.new_store'
        with mock.patch(new_store) as new_store:
            with mock.patch.object(self.store, 'commit'):
                with mock.patch.object(self.store, 'close'):
                    new_store.return_value = self.store
                    self.click(item_step.create_order_button)
                    run_dialog.assert_called_once_with(PurchaseWizard,
                                                       self.wizard,
                                                       self.store,
                                                       self.purchase_clone)
                    yesno.assert_called_once_with(
                        'Should we close the quotes used to compose the '
                        'purchase order ?', gtk.RESPONSE_NO, 'Close quotes',
                        "Don't close")

        self.click(self.wizard.next_button)

        models = [quotation, quotation.group, purchase]
        models.extend(purchase.get_items())
        self.check_wizard(self.wizard, 'wizard-receivequote-finish-step',
                          models=models)
