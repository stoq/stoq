# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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

from stoqlib.database.viewable import Viewable
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.search.sellablesearch import (SellableSearch,
                                               PurchaseSellableSearch)
from stoqlib.gui.wizards.loanwizard import (NewLoanWizard, LoanItemStep)
from stoqlib.gui.wizards.productionwizard import (ProductionWizard, ProductionItemStep,
                                                  ProductionServiceStep)
from stoqlib.gui.wizards.purchasequotewizard import (QuotePurchaseWizard,
                                                     QuoteItemStep)
from stoqlib.gui.wizards.purchasewizard import (PurchaseWizard,
                                                PurchaseItemStep)
from stoqlib.gui.wizards.salequotewizard import (SaleQuoteWizard,
                                                 SaleQuoteItemStep)
from stoqlib.gui.wizards.stockdecreasewizard import (StockDecreaseWizard,
                                                     DecreaseItemStep)
from stoqlib.gui.wizards.stocktransferwizard import (StockTransferWizard,
                                                     StockTransferItemStep)


class BaseTest(object):
    wizard_class = None
    step_class = None
    search_name = None
    search_class = SellableSearch

    def setUp(self):
        super(BaseTest, self).setUp()

        self.wizard = self.wizard_class(self.store)
        self.step = self.step_class(self.wizard, None, self.store, self.wizard.model)

    def test_get_sellable_view_query(self):
        retval = self.step.get_sellable_view_query()
        self.assertTrue(isinstance(retval, tuple))
        self.assertEquals(len(retval), 2)
        self.assertTrue(issubclass(retval[0], Viewable))

    def test_sellable_search(self):
        viewable, query = self.step.get_sellable_view_query()
        hide_toolbar = not self.step.sellable_editable
        search = self.search_class(self.store, search_spec=viewable,
                                   search_query=query, hide_toolbar=hide_toolbar)
        search.search.refresh()
        self.check_search(search, self.search_name)

    @mock.patch('stoqlib.gui.wizards.abstractwizard.SellableItemStep._run_advanced_search')
    def test_barcode_activate_(self, advanced_search):
        self.step.barcode.set_text('invalid barcode')
        self.step.barcode.activate()
        advanced_search.assert_called_once_with('invalid barcode')


class TestProductionServiceStep(BaseTest, GUITest):
    wizard_class = ProductionWizard
    step_class = ProductionServiceStep
    search_name = 'item-step-production-service'


class TestProductionItemStep(BaseTest, GUITest):
    wizard_class = ProductionWizard
    step_class = ProductionItemStep
    search_name = 'item-step-production-item'

    def setUp(self):
        BaseTest.setUp(self)
        product = self.create_product()
        product.is_composed = True
        self.create_product_component(product=product)


class TestQuoteItemStep(BaseTest, GUITest):
    wizard_class = QuotePurchaseWizard
    step_class = QuoteItemStep
    search_class = PurchaseSellableSearch
    search_name = 'item-step-quote-wizard'


class TestPurchaseItemStep(BaseTest, GUITest):
    wizard_class = PurchaseWizard
    step_class = PurchaseItemStep
    search_class = PurchaseSellableSearch
    search_name = 'item-step-purchase-wizard'


class TestSaleQuoteItemStep(BaseTest, GUITest):
    wizard_class = SaleQuoteWizard
    step_class = SaleQuoteItemStep
    search_name = 'item-step-sale-quote-wizard'


class TestDecreaseItemStep(BaseTest, GUITest):
    wizard_class = StockDecreaseWizard
    step_class = DecreaseItemStep
    search_name = 'item-step-decrease-wizard'


class TestStockTransferItemStep(BaseTest, GUITest):
    wizard_class = StockTransferWizard
    step_class = StockTransferItemStep
    search_name = 'item-step-stock-transfer-wizard'


class TestLoanItemStep(BaseTest, GUITest):
    wizard_class = NewLoanWizard
    step_class = LoanItemStep
    search_name = 'item-step-new-loan-wizard'
