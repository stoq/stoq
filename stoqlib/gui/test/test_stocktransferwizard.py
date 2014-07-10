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

import gtk
import mock

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.transfer import TransferOrder
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.wizards.stocktransferwizard import StockTransferWizard

from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class TestStockTransferWizard(GUITest):
    @mock.patch('stoqlib.gui.wizards.stocktransferwizard.print_report')
    @mock.patch('stoqlib.gui.wizards.stocktransferwizard.yesno')
    def test_create(self, yesno, print_report):
        sellable = self.create_sellable(description=u"Product to transfer")
        self.create_storable(sellable.product, get_current_branch(self.store),
                             stock=10)

        wizard = StockTransferWizard(self.store)
        self.assertNotSensitive(wizard, ['next_button'])
        self.check_wizard(wizard, 'wizard-stock-transfer-create')

        step = wizard.get_current_step()
        step.destination_branch.set_active(0)
        self.assertSensitive(wizard, ['next_button'])

        self.click(wizard.next_button)
        step = wizard.get_current_step()

        # adds sellable to step
        step.sellable_selected(sellable)
        step._add_sellable()

        self.check_wizard(wizard, 'wizard-stock-transfer-products')

        module = 'stoqlib.gui.events.StockTransferWizardFinishEvent.emit'
        with mock.patch(module) as emit:
            with mock.patch.object(self.store, 'commit'):
                self.click(wizard.next_button)
            self.assertEquals(emit.call_count, 1)
            args, kwargs = emit.call_args
            self.assertTrue(isinstance(args[0], TransferOrder))

        yesno.assert_called_once_with(
            _('Would you like to print a receipt for this transfer?'),
            gtk.RESPONSE_YES, 'Print receipt', "Don't print")
        self.assertEquals(print_report.call_count, 1)
