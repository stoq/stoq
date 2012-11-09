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

import operator

import gtk
import mock
from nose.exc import SkipTest

from stoqlib.domain.person import Employee
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.transfer import TransferOrder
from stoqlib.gui.wizards.stocktransferwizard import StockTransferWizard
from stoqlib.gui.uitestutils import GUITest

from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class TestStockTransferWizard(GUITest):
    @mock.patch('stoqlib.gui.wizards.stocktransferwizard.print_report')
    @mock.patch('stoqlib.gui.wizards.stocktransferwizard.yesno')
    def test_create(self, yesno, print_report):
        raise SkipTest("unstable sellable selection")
        wizard = StockTransferWizard(self.trans)
        self.assertNotSensitive(wizard, ['next_button'])
        self.check_wizard(wizard, 'wizard-stock-transfer-create')

        step = wizard.get_current_step()

        # gets a sellable with a product storable
        sellables = sorted(
            [s for s in Sellable.select(connection=self.trans)
                   if s.product_storable != None],
            key=operator.attrgetter('id'))

        # adds sellable to step
        step.sellable_selected(sellables[0])
        step._add_sellable()

        self.check_wizard(wizard, 'wizard-stock-transfer-products')
        self.click(wizard.next_button)
        step = wizard.get_current_step()

        self.check_wizard(wizard, 'wizard-stock-transfer-finish-step')
        # No source or destination responsible selected. Finish is disabled
        self.assertNotSensitive(wizard, ['next_button'])

        employee = Employee.select(connection=self.trans)[0]

        # Select a source responsible
        step.source_responsible.select(employee)

        # Finish should still be disable until we select a destination
        # responsible
        self.assertNotSensitive(wizard, ['next_button'])
        step.destination_responsible.select(employee)

        module = 'stoqlib.gui.events.StockTransferWizardFinishEvent.emit'
        with mock.patch(module) as emit:
            self.click(wizard.next_button)
            self.assertEquals(emit.call_count, 1)
            args, kwargs = emit.call_args
            self.assertTrue(isinstance(args[0], TransferOrder))

        yesno.assert_called_once_with(
                     _('Would you like to print a receipt for this transfer?'),
                     gtk.RESPONSE_YES, 'Print receipt', "Don't print")
        self.assertEquals(print_report.call_count, 1)
