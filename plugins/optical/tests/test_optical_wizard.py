# -*- Mode: Python; coding: utf-8 -*-
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

__tests__ = 'plugins/optical/opticalwizard.py'

import decimal

import mock
import gtk

from stoqlib.api import api
from stoqlib.domain.sale import Sale, SaleComment
from stoqlib.domain.workorder import WorkOrderCategory, WorkOrderItem
from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.editors.personeditor import ClientEditor
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localdate
from stoqlib.lib.translation import stoqlib_gettext

from ..opticalreport import OpticalWorkOrderReceiptReport
from ...optical.opticalwizard import OpticalSaleQuoteWizard

_ = stoqlib_gettext


class TestSaleQuoteWizard(GUITest):
    @mock.patch('plugins.optical.opticalwizard.yesno')
    @mock.patch('stoqlib.gui.wizards.salequotewizard.run_dialog')
    @mock.patch('stoqlib.gui.wizards.salequotewizard.run_person_role_dialog')
    def test_confirm(self, run_person_role_dialog, run_dialog, yesno):
        WorkOrderCategory(store=self.store,
                          name=u'Category',
                          color=u'#ff0000')
        client = self.create_client()
        self.create_address(person=client.person)

        run_person_role_dialog.return_value = client
        yesno.return_value = False

        # Test for reserve without storable
        sellable = self.create_sellable()
        sellable.barcode = u'12345678'
        # Test for reserve with storable
        sellable2 = self.create_sellable()
        sellable2.barcode = u'12345679'
        self.create_storable(
            product=sellable2.product,
            branch=api.get_current_branch(self.store),
            stock=10)
        # Test for reserve for a batch with storable
        sellable3 = self.create_sellable()
        sellable3.barcode = u'12345680'
        storable, batch = self.create_storable(
            product=sellable3.product,
            branch=api.get_current_branch(self.store),
            is_batch=True, stock=10)
        # Test for return_to_stock
        sellable4 = self.create_sellable()
        sellable4.barcode = u'12345681'
        self.create_storable(product=sellable4.product)

        wizard = OpticalSaleQuoteWizard(self.store)

        step = wizard.get_current_step()

        self.click(step.create_client)
        self.assertEquals(run_person_role_dialog.call_count, 1)
        args, kwargs = run_person_role_dialog.call_args
        editor, parent, store, model = args
        self.assertEquals(editor, ClientEditor)
        self.assertEquals(parent, wizard)
        self.assertTrue(store is not None)
        self.assertTrue(model is None)

        self.click(step.client_details)
        self.assertEquals(run_dialog.call_count, 1)
        args, kwargs = run_dialog.call_args
        dialog, parent, store, model = args
        self.assertEquals(dialog, ClientDetailsDialog)
        self.assertEquals(parent, wizard)
        self.assertTrue(store is not None)
        self.assertEquals(model, client)

        run_dialog.return_value = False
        self.click(step.notes_button)
        self.assertEquals(run_dialog.call_count, 2)
        args, kwargs = run_dialog.call_args
        editor, parent, store, model, comment = args
        self.assertEquals(editor, NoteEditor)
        self.assertEquals(parent, wizard)
        self.assertTrue(store is not None)
        self.assertTrue(isinstance(model, SaleComment))
        self.assertEquals(comment, 'comment')
        self.assertEquals(kwargs['title'], _("Additional Information"))

        self.check_wizard(wizard, 'wizard-optical-start-sale-quote-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        slave = step.slaves['WO 1']
        slave.patient.update('Patient')
        slave.estimated_finish.update(localdate(2020, 1, 5))

        sale = wizard.model
        self.check_wizard(wizard, 'wizard-optical-work-order-step')

        self.click(wizard.next_button)
        step = wizard.get_current_step()

        for barcode in [batch.batch_number, sellable.barcode,
                        sellable2.barcode, sellable4.barcode]:
            step.barcode.set_text(barcode)
            self.activate(step.barcode)
            step.quantity.update(1)
            self.click(step.add_sellable_button)

        for item in step.slave.klist:
            if item.sellable == sellable4:
                wo_item = WorkOrderItem.get_from_sale_item(self.store, item)
                wo_item.quantity_decreased = 10

        self.check_wizard(wizard, 'wizard-optical-item-step',
                          [sale, client] +
                          list(sale.get_items().order_by('te_id')))

        module = 'stoqlib.gui.events.SaleQuoteWizardFinishEvent.emit'
        with mock.patch(module) as emit:
            with mock.patch.object(self.store, 'commit'):
                self.click(wizard.next_button)
            self.assertEquals(emit.call_count, 1)
            args, kwargs = emit.call_args
            self.assertTrue(isinstance(args[0], Sale))

        self.assertEqual(wizard.model.payments.count(), 0)
        yesno.assert_called_once_with(_('Would you like to print the quote '
                                        'details now?'), gtk.RESPONSE_YES,
                                      _("Print quote details"), _("Don't print"))

        # Test get_saved_items, using the existing model here
        wizard2 = OpticalSaleQuoteWizard(self.store, model=wizard.model)
        self.click(wizard2.next_button)
        self.click(wizard2.next_button)

    def test_with_work_order(self):
        category = WorkOrderCategory(store=self.store,
                                     name=u'Category',
                                     color=u'#ff0000')

        sale = self.create_sale()
        sale.status = Sale.STATUS_QUOTE
        workorder = self.create_workorder()
        workorder.sale = sale
        workorder.category = category
        OpticalSaleQuoteWizard(self.store, model=sale)

    def test_param_accept_change_salesperson(self):
        with self.sysparam(ACCEPT_CHANGE_SALESPERSON=True):
            wizard = OpticalSaleQuoteWizard(self.store)
            step = wizard.get_current_step()
            self.assertTrue(step.salesperson.get_sensitive())

        with self.sysparam(ACCEPT_CHANGE_SALESPERSON=False):
            wizard = OpticalSaleQuoteWizard(self.store)
            step = wizard.get_current_step()
            self.assertFalse(step.salesperson.get_sensitive())

    @mock.patch('stoqlib.gui.wizards.workorderquotewizard.warning')
    @mock.patch('stoqlib.gui.wizards.salequotewizard.run_person_role_dialog')
    def test_multiple_work_orders(self, run_person_role_dialog, warning):
        client = self.create_client()

        run_person_role_dialog.return_value = client

        wizard = OpticalSaleQuoteWizard(self.store)
        step = wizard.get_current_step()
        for i in range(3):
            wo = self.create_workorder()
            wo.sale = step.model

        wo.add_sellable(self.create_sellable())

        self.click(step.create_client)
        self.click(wizard.next_button)
        self.check_wizard(wizard, 'wizard-optical-work-order-step-multiple-wo')

        step = wizard.get_current_step()
        assert step.work_orders_nb.get_n_pages() == 3

        # Test removing the first, with no items
        self.click(step.slaves['WO 1'].close_button)

        # Test removing the third, which has items
        self.click(step.slaves['WO 3'].close_button)
        warning.assert_called_once_with(
            'This workorder already has items and cannot be removed')

        # Test removing the second, which has no items
        self.click(step.slaves['WO 2'].close_button)

        # Test removing the third, which is not possible any more since
        # it's the last
        self.click(step.slaves['WO 3'].close_button)

        # Add a new
        self.click(step.new_tab_button)

    @mock.patch('stoqlib.gui.wizards.salequotewizard.run_person_role_dialog')
    def test_item_step(self, run_person_role_dialog):
        client = self.create_client()
        run_person_role_dialog.return_value = client
        wizard = OpticalSaleQuoteWizard(self.store)
        step = wizard.get_current_step()
        for i in range(2):
            wo = self.create_workorder()
            wo.sale = step.model

        self.click(step.create_client)
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        for slave in step.slaves.values():
            slave.patient.update('Patient')
            slave.estimated_finish.update(localdate(2020, 1, 5))

        self.click(wizard.next_button)

        sellable = self.create_sellable()
        item_slave = wizard.get_current_step()

        m = 'stoqlib.gui.wizards.salequotewizard.SaleQuoteItemStep.get_remaining_quantity'
        with mock.patch(m) as get_remaining_quantity:
            get_remaining_quantity.return_value = decimal.Decimal("5")
            item_slave.get_order_item(sellable,
                                      decimal.Decimal("1"),
                                      decimal.Decimal("10"))
        saved = list(item_slave.get_saved_items())
        item_slave.remove_items(saved)

        with self.sysparam(REUTILIZE_DISCOUNT=False):
            self.assertIsNone(item_slave.get_extra_discount(sellable))

        with self.sysparam(REUTILIZE_DISCOUNT=True):
            self.assertIsNotNone(item_slave.get_extra_discount(sellable))

        for radio in item_slave._radio_group.get_group():
            radio.toggled()

    @mock.patch('stoqlib.gui.wizards.salequotewizard.run_person_role_dialog')
    def test_item_step_too_many(self, run_person_role_dialog):
        client = self.create_client()
        client.status = client.STATUS_INDEBTED
        run_person_role_dialog.return_value = client
        wizard = OpticalSaleQuoteWizard(self.store)
        step = wizard.get_current_step()
        for i in range(4):
            wo = self.create_workorder()
            wo.sale = step.model

        self.click(step.create_client)
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        for slave in step.slaves.values():
            slave.patient.update('Patient')
            slave.estimated_finish.update(localdate(2020, 1, 5))

        self.click(wizard.next_button)

        step = wizard.get_current_step()
        step.work_orders_combo.show()

    @mock.patch('plugins.optical.opticalwizard.yesno')
    @mock.patch('plugins.optical.opticalwizard.print_report')
    def test_print_quote_details(self, print_report, yesno):
        sale = self.create_sale()
        sale.status = Sale.STATUS_QUOTE
        workorder = self.create_workorder()
        workorder.sale = sale

        wizard = OpticalSaleQuoteWizard(self.store, model=sale)
        wizard.print_quote_details(workorder)

        yesno.assert_called_once_with('Would you like to print the quote details now?',
                                      gtk.RESPONSE_YES,
                                      'Print quote details',
                                      "Don't print")
        print_report.assert_called_once_with(OpticalWorkOrderReceiptReport, [workorder])
