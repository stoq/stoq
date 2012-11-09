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

from stoqlib.api import api
from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.wizards.stockdecreasewizard import StockDecreaseWizard
from stoqlib.domain.stockdecrease import StockDecrease


class TestStockDecreaseWizard(GUITest):
    @mock.patch('stoqlib.gui.wizards.stockdecreasewizard.'
                'StockDecreaseWizard._receipt_dialog')
    def test_wizard(self, receipt_dialog):
        branch = api.get_current_branch(self.trans)
        storable = self.create_storable()
        storable.increase_stock(1, branch)
        sellable = storable.product.sellable
        wizard = StockDecreaseWizard(self.trans)

        step = wizard.get_current_step()
        self.assertNotSensitive(wizard, ['next_button'])
        step.reason.update('text')
        self.assertSensitive(wizard, ['next_button'])
        self.check_wizard(wizard, 'start-stock-decrease-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertNotSensitive(wizard, ['next_button'])
        step.barcode.set_text(sellable.barcode)
        step.sellable_selected(sellable)
        step.quantity.update(1)
        self.click(step.add_sellable_button)
        self.check_wizard(wizard, 'decrease-item-step')

        self.assertSensitive(wizard, ['next_button'])
        module = 'stoqlib.gui.events.StockDecreaseWizardFinishEvent.emit'
        with mock.patch(module) as emit:
            self.click(wizard.next_button)
            self.assertEquals(emit.call_count, 1)
            args, kwargs = emit.call_args
            self.assertTrue(isinstance(args[0], StockDecrease))

        self.assertEquals(receipt_dialog.call_count, 1)

        # Assert wizard decreased stock.
        self.assertEquals(storable.get_balance_for_branch(branch), 0)
