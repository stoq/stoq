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

from stoqlib.domain.sellable import Sellable
from stoqlib.gui.wizards.stocktransferwizard import StockTransferWizard
from stoqlib.gui.uitestutils import GUITest


class TestStockTransferWizard(GUITest):
    def test_create(self):
        wizard = StockTransferWizard(self.trans)
        self.assertNotSensitive(wizard, ['next_button'])
        self.check_wizard(wizard, 'wizard-stock-transfer-create')

        step = wizard.get_current_step()

        # gets a sellable with a product storable
        sellables = [(sellable)
                        for sellable in Sellable.select(connection=self.trans)
                            if sellable.product_storable != None]

        # adds sellable to step
        step.sellable_selected(sellables[0])
        step._add_sellable()

        self.check_wizard(wizard, 'wizard-stock-transfer-products')
        self.assertSensitive(wizard, ['next_button'])

        self.click(wizard.next_button)

        self.check_wizard(wizard, 'wizard-stock-transfer-finish-step')
        self.assertNotSensitive(wizard, ['next_button'])
