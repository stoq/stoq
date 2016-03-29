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

import contextlib
from decimal import Decimal

import gtk
from kiwi.python import Settable
import mock

from stoqlib.api import api
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.gui.dialogs.labeldialog import SkipLabelsEditor
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.wizards.receivingwizard import ReceivingOrderWizard
from stoqlib.lib.dateutils import localdatetime


class TestReceivingOrderWizard(GUITest):
    @mock.patch('stoqlib.gui.utils.printing.warning')
    @mock.patch('stoqlib.gui.wizards.receivingwizard.run_dialog')
    @mock.patch('stoqlib.gui.wizards.receivingwizard.yesno')
    def test_complete_receiving(self, yesno, run_dialog, warning):
        yesno.return_value = True
        run_dialog.return_value = Settable(skip=Decimal('0'))
        branch = api.get_current_branch(self.store)

        order = self.create_purchase_order(branch=branch)
        order.identifier = 65432
        order.open_date = localdatetime(2012, 10, 9)
        order.expected_receival_date = localdatetime(2012, 9, 25)
        sellable = self.create_sellable()
        package = self.create_product(description=u'Package', is_package=True)
        component = self.create_product(description=u'Component', stock=2)
        self.create_product_component(product=package, component=component)

        order.add_item(sellable, 1)
        parent = order.add_item(package.sellable, 1)
        order.add_item(component.sellable, 1, parent=parent)
        order.status = PurchaseOrder.ORDER_PENDING
        order.confirm()
        wizard = ReceivingOrderWizard(self.store)

        step = wizard.get_current_step()
        self.assertNotSensitive(wizard, ['next_button'])
        self.click(step.search.search_button)
        order_view = step.search.results[0]
        step.search.results.select(order_view)
        self.assertSensitive(wizard, ['next_button'])
        self.check_wizard(wizard, 'purchase-selection-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertSensitive(wizard, ['next_button'])
        self.check_wizard(wizard, 'receiving-order-product-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertNotSensitive(wizard, ['next_button'])
        step.invoice_slave.invoice_number.update(1)
        self.assertSensitive(wizard, ['next_button'])
        self.check_wizard(wizard, 'receiving-invoice-step')

        module = 'stoqlib.gui.events.ReceivingOrderWizardFinishEvent.emit'
        with contextlib.nested(
                mock.patch(module),
                mock.patch.object(wizard.model, 'confirm'),
                mock.patch.object(self.store, 'commit')) as (emit, confirm, _):
            # When this parameter is empty, the user should not be asked
            # to print labels
            with self.sysparam(LABEL_TEMPLATE_PATH=u''):
                self.click(wizard.next_button)

            self.assertEqual(confirm.call_count, 1)
            self.assertEqual(yesno.call_count, 0)
            emit.assert_called_once_with(wizard.model)

            emit.reset_mock()
            confirm.reset_mock()

            # When the file exists, it should ask to print labels, although it
            # will fail as the file is not valid
            with self.sysparam(LABEL_TEMPLATE_PATH=u'non-existing-file'):
                self.click(wizard.next_button)

            self.assertEqual(emit.call_count, 1)
            self.assertEqual(confirm.call_count, 1)
            emit.assert_called_once_with(wizard.model)

            yesno.assert_called_once_with(
                "Do you want to print the labels for the received products?",
                gtk.RESPONSE_YES, "Print labels", "Don't print")

            run_dialog.assert_called_once_with(
                SkipLabelsEditor, wizard, self.store)

            warning.assert_called_once_with(
                "It was not possible to print the labels. The template "
                "file was not found.")

    def test_complete_receiving_multiple_purchases(self):
        branch = api.get_current_branch(self.store)

        # Create purchase order 1
        product1 = self.create_product(description=u'Product 1', storable=True)
        order1 = self.create_purchase_order(branch=branch)
        order1.identifier = 10023
        order1.open_date = localdatetime(2012, 10, 9)
        order1.expected_receival_date = localdatetime(2012, 9, 25)
        order1.add_item(product1.sellable, 7)
        order1.status = PurchaseOrder.ORDER_PENDING
        order1.confirm()

        # And purchase order 2
        product2 = self.create_product(description=u'Product 2', storable=True)
        order2 = self.create_purchase_order(branch=branch,
                                            supplier=order1.supplier)
        order2.identifier = 10024
        order2.open_date = localdatetime(2012, 10, 9)
        order2.expected_receival_date = localdatetime(2012, 9, 25)
        order2.add_item(product2.sellable, 5)
        order2.status = PurchaseOrder.ORDER_PENDING
        order2.confirm()

        # Now to the wizard
        wizard = ReceivingOrderWizard(self.store)

        step = wizard.get_current_step()
        self.assertNotSensitive(wizard, ['next_button'])
        self.click(step.search.search_button)
        # Select both purchase orders. There is one bug in kiwi that we cannot
        # select all at once, so thats why we are using this private api.
        step.search.results._treeview.get_selection().select_all()
        self.assertSensitive(wizard, ['next_button'])
        self.check_wizard(wizard, 'receiving-order-multiple-purchase-selection-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertSensitive(wizard, ['next_button'])
        self.check_wizard(wizard, 'receiving-order-multiple-product-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        step.invoice_slave.invoice_number.update(10094)
        step.invoice_slave.freight.update(159)
        self.check_wizard(wizard, 'receiving-order-multiple-invoice-step')

        with contextlib.nested(
                mock.patch.object(self.store, 'commit')):
            # Confirm
            self.click(wizard.next_button)

        self.assertEquals(product1.storable.get_balance_for_branch(branch), 7)
        self.assertEquals(product2.storable.get_balance_for_branch(branch), 5)
