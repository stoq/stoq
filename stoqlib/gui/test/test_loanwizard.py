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

import datetime

import gtk
import mock

from stoqlib.api import api
from stoqlib.domain.loan import Loan, LoanItem
from stoqlib.domain.sale import Sale
from stoqlib.gui.uitestutils import GUITest
from stoqlib.gui.wizards.loanwizard import CloseLoanWizard, NewLoanWizard
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class TestNewLoanWizard(GUITest):
    @mock.patch('stoqlib.gui.wizards.loanwizard.print_report')
    @mock.patch('stoqlib.gui.wizards.loanwizard.yesno')
    def test_confirm(self, yesno, print_report):
        client = self.create_client()
        branch = api.get_current_branch(self.trans)
        storable = self.create_storable()
        storable.increase_stock(1, branch)
        sellable = storable.product.sellable
        wizard = NewLoanWizard(self.trans)

        step = wizard.get_current_step()
        step.client.update(client)
        step.expire_date.update(datetime.date.today())
        self.check_wizard(wizard, 'new-loan-wizard-start-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        step.barcode.set_text(sellable.barcode)
        step.sellable_selected(sellable)
        step.quantity.update(1)
        self.click(step.add_sellable_button)
        loan_item = LoanItem.selectOneBy(sellable=sellable, connection=self.trans)
        module = 'stoqlib.gui.events.NewLoanWizardFinishEvent.emit'
        with mock.patch(module) as emit:
            self.click(wizard.next_button)
            self.assertEquals(emit.call_count, 1)
            args, kwargs = emit.call_args
            self.assertTrue(isinstance(args[0], Loan))
        self.check_wizard(wizard, 'new-loan-wizard-item-step',
                          [wizard.retval, loan_item])

        yesno.assert_called_once_with(_('Would you like to print the receipt now?'),
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
        total_sales = Sale.selectBy(status=Sale.STATUS_ORDERED,
                                    connection=self.trans).count()
        wizard = CloseLoanWizard(self.trans)

        step = wizard.get_current_step()
        loan.open_date = datetime.datetime(2012, 1, 1, 12, 0)
        self.click(step.search.search.search_button)
        loan_view = step.search.results[0]
        step.search.results.select(loan_view)
        self.check_wizard(wizard, 'close-loan-wizard-select-loan-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        loan_item.return_quantity = 2
        loan_item.sale_quantity = 2
        step._validate_step(True)
        module = 'stoqlib.gui.events.CloseLoanWizardFinishEvent.emit'
        with mock.patch(module) as emit:
            self.click(wizard.next_button)
            self.assertEquals(emit.call_count, 1)
            args, kwargs = emit.call_args
            self.assertTrue(isinstance(args[0], Loan))
        self.check_wizard(wizard,
                          'close-loan-wizard-loan-item-selection-step',
                          [wizard.retval, loan_item])

        new_total_sales = Sale.selectBy(status=Sale.STATUS_ORDERED,
                                    connection=self.trans).count()
        self.assertEquals(total_sales + 1, new_total_sales)

        # Checks if stock is correct. 10 items were loaned, 2 were
        # returned and 2 were sold, but the sale was not completed, therefore
        # these 2 sold items are still in the branch stock
        branch = loan.branch
        self.assertEquals(loan_item.storable.get_balance_for_branch(branch), 4)

        info.assert_called_once_with(_('Close loan details...'), _("A sale was "
                                       "created from loan items. You can confirm "
                                       "that sale in the Till application later."))
