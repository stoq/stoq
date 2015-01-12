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

from stoqlib.api import api
from stoqlib.domain.loan import Loan, LoanItem
from stoqlib.domain.sale import Sale
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.wizards.loanwizard import CloseLoanWizard, NewLoanWizard
from stoqlib.lib.dateutils import localdatetime, localtoday
from stoqlib.lib.defaults import MAX_INT


class TestNewLoanWizard(GUITest):
    @mock.patch('stoqlib.gui.wizards.loanwizard.print_report')
    @mock.patch('stoqlib.gui.wizards.loanwizard.yesno')
    def test_confirm(self, yesno, print_report):
        client = self.create_client()
        branch = api.get_current_branch(self.store)
        storable = self.create_storable(branch=branch, stock=1, unit_cost=10)
        sellable = storable.product.sellable
        wizard = NewLoanWizard(self.store)

        step = wizard.get_current_step()
        step.client_gadget.set_value(client)
        step.expire_date.update(localtoday().date())
        self.check_wizard(wizard, 'new-loan-wizard-start-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        step.barcode.set_text(sellable.barcode)
        step.sellable_selected(sellable)

        # This is a workaround to be able to set a value bigger than MAX_INT,
        # so we can get its validation
        step.quantity.get_adjustment().set_upper(MAX_INT + 1)
        # Checking values bigger than MAX_INT for quantity
        step.quantity.update(MAX_INT + 1)
        self.assertInvalid(step, ['quantity'])
        # Checking values bigger than we have on stock
        step.quantity.update(2)
        self.assertInvalid(step, ['quantity'])
        # Checking negative value
        step.quantity.update(-1)
        self.assertInvalid(step, ['quantity'])
        # Checking valid values
        step.quantity.update(1)
        self.assertValid(step, ['quantity'])

        # Checking negative value
        step.cost.update(-1)
        self.assertInvalid(step, ['cost'])
        # This is a workaround to be able to set a value bigger than MAX_INT,
        # so we can get its validation
        step.cost.get_adjustment().set_upper(MAX_INT + 1)
        # Checking values bigger than MAX_INT for cost
        step.cost.update(MAX_INT + 1)
        self.assertInvalid(step, ['cost'])
        # Checking valid value
        step.cost.update(10)
        self.assertValid(step, ['cost'])

        self.click(step.add_sellable_button)
        loan_item = self.store.find(LoanItem, sellable=sellable).one()
        module = 'stoqlib.gui.events.NewLoanWizardFinishEvent.emit'
        with mock.patch(module) as emit:
            with mock.patch.object(self.store, 'commit'):
                self.click(wizard.next_button)
            self.assertEquals(emit.call_count, 1)
            args, kwargs = emit.call_args
            self.assertTrue(isinstance(args[0], Loan))
        self.check_wizard(wizard, 'new-loan-wizard-item-step',
                          [wizard.retval, loan_item])

        yesno.assert_called_once_with('Would you like to print the receipt now?',
                                      gtk.RESPONSE_YES, 'Print receipt', "Don't print")
        self.assertEquals(print_report.call_count, 1)

        # verifies if stock was decreased correctly
        self.assertEquals(storable.get_balance_for_branch(branch), 0)


class TestCloseLoanWizard(GUITest):
    @mock.patch('stoqlib.gui.wizards.loanwizard.info')
    def test_confirm(self, info):
        loan = self.create_loan()
        loan.identifier = 9999
        loan.client = self.create_client()
        loan_item = self.create_loan_item(loan=loan, quantity=10)
        total_sales = self.store.find(Sale, status=Sale.STATUS_ORDERED).count()
        wizard = CloseLoanWizard(self.store)

        step = wizard.get_current_step()
        loan.open_date = localdatetime(2012, 1, 1, 12, 0)
        self.click(step.search.search_button)
        loan_view = step.search.results[0]
        step.search.results.select(loan_view)
        self.check_wizard(wizard, 'close-loan-wizard-select-loan-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        step.validate(True)
        objectlist = step.slave.klist
        self.assertNotSensitive(wizard, ['next_button'])
        loan_item.return_quantity = 2
        loan_item.sale_quantity = 2
        objectlist.update(loan_item)
        step.validate(True)
        self.assertSensitive(wizard, ['next_button'])

        module = 'stoqlib.gui.events.CloseLoanWizardFinishEvent.emit'
        with mock.patch(module) as emit:
            self.click(wizard.next_button)
            self.assertEquals(emit.call_count, 1)
            args, kwargs = emit.call_args
            # The event emits a list of loans
            self.assertTrue(isinstance(args[0], list))
            self.assertTrue(isinstance(args[0][0], Loan))
        self.check_wizard(wizard,
                          'close-loan-wizard-loan-item-selection-step',
                          wizard.retval + [loan_item])

        new_total_sales = self.store.find(Sale, status=Sale.STATUS_ORDERED).count()
        self.assertEquals(total_sales + 1, new_total_sales)

        # Checks if stock is correct. 10 items were loaned, 2 were
        # returned and 2 were sold, so those 2 should be have been returned to
        # branch's stock
        branch = loan.branch
        self.assertEquals(loan_item.storable.get_balance_for_branch(branch), 2)

        info.assert_called_once_with('Close loan details...',
                                     "A sale was created from loan items. "
                                     "You can confirm that sale in the Till "
                                     "application later.")
