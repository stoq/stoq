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
from stoqlib.domain.workorder import WorkOrderCategory
from stoqlib.gui.dialogs.clientdetails import ClientDetailsDialog
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.editors.personeditor import ClientEditor
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.wizards.salequotewizard import DiscountEditor
from stoqlib.lib.dateutils import localdate
from stoqlib.lib.translation import stoqlib_gettext

from ..opticalreport import OpticalWorkOrderReceiptReport
from ...optical.opticalwizard import (OpticalSaleQuoteWizard, _ItemEditor,
                                      _TempSaleItem)
from .test_optical_domain import OpticalDomainTest

_ = stoqlib_gettext


class TestItemEditor(GUITest, OpticalDomainTest):
    def _create_editor(self):
        return _ItemEditor(self.store, self._create_sale_item())

    def _create_sale_item(self):
        sale = self.create_sale()
        sellable = self.create_sellable()
        sellable.base_price = 100
        sale_item = sale.add_sellable(sellable)
        optical_wo = self.create_optical_work_order()
        wo = optical_wo.work_order
        wo.sale = sale
        wo_item = wo.add_sellable(sellable)
        wo_item.sale_item = sale_item

        return _TempSaleItem(sale_item)

    def test_show(self):
        editor = self._create_editor()
        self.check_editor(editor, 'editor-optical-item')

    def test_confirm(self):
        editor = self._create_editor()
        with mock.patch.object(editor.model, 'update') as update:
            self.click(editor.main_dialog.ok_button)
            update.assert_called_once()

    def test_cancel(self):
        editor = self._create_editor()
        editor.price.update(200)
        self.assertEqual(editor.model.price, 200)
        self.click(editor.main_dialog.cancel_button)
        self.assertEqual(editor.model.price, 100)

    def test_price_validation(self):
        user = api.get_current_user(self.store)
        user.profile.max_discount = 2
        editor = self._create_editor()
        self.assertValid(editor, ['price'])
        editor.price.update(98)
        self.assertValid(editor, ['price'])
        editor.price.update(97)
        self.assertInvalid(editor, ['price'])
        editor.price.update(-1)
        self.assertInvalid(editor, ['price'])

        with self.sysparam(REUTILIZE_DISCOUNT=u'1'):
            editor.price.update(10)
            self.assertInvalid(editor, ['price'])

        with self.sysparam(REUTILIZE_DISCOUNT=u'0'):
            editor.price.update(10)
            self.assertInvalid(editor, ['price'])

    @mock.patch('stoqlib.domain.sellable.Sellable.is_valid_quantity')
    def test_quantity_validation(self, is_valid_quantity):
        editor = self._create_editor()
        self.assertValid(editor, ['quantity'])
        editor.quantity.update(-1)
        self.assertInvalid(editor, ['quantity'])
        is_valid_quantity.return_value = False
        editor.quantity.update(1)
        self.assertInvalid(editor, ['quantity'])

    @mock.patch('plugins.optical.opticalwizard.run_dialog')
    def test_icon_press(self, run_dialog):
        user = api.get_current_user(self.store)
        run_dialog.return_value = user
        editor = self._create_editor()
        editor.price.emit('icon-press', gtk.ENTRY_ICON_SECONDARY, None)
        editor.price.emit('icon-press', gtk.ENTRY_ICON_PRIMARY, None)

    def test_sale_item_description(self):
        sale_item = self._create_sale_item()
        self.assertEquals(sale_item.description, u'Description')

    def test_sale_item_sale_discount(self):
        sale_item = self._create_sale_item()
        self.assertEquals(sale_item.sale_discount, 0)

    def test_sale_item_remove(self):
        sale_item = self._create_sale_item()
        sale_item.remove()


class TestSaleQuoteWizard(GUITest):
    @mock.patch('plugins.optical.opticalwizard.yesno')
    @mock.patch('plugins.optical.opticalwizard.run_dialog')
    @mock.patch('plugins.optical.opticalwizard.run_person_role_dialog')
    def test_confirm(self, run_person_role_dialog, run_dialog, yesno):
        WorkOrderCategory(store=self.store,
                          name=u'Category',
                          color=u'#ff0000')
        client = self.create_client()
        self.create_address(person=client.person)

        run_person_role_dialog.return_value = client
        yesno.return_value = False

        sellable = self.create_sellable()
        sellable.barcode = u'12345678'

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
        self.click(step.observations_button)
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

        self.check_wizard(wizard, 'wizard-optical-item-step',
                          [sale, client] + list(sale.get_items()) + [sellable])

        module = 'stoqlib.gui.events.SaleQuoteWizardFinishEvent.emit'
        with mock.patch(module) as emit:
            self.click(wizard.next_button)
            self.assertEquals(emit.call_count, 1)
            args, kwargs = emit.call_args
            self.assertTrue(isinstance(args[0], Sale))

        self.assertEqual(wizard.model.payments.count(), 0)
        yesno.assert_called_once_with(_('Would you like to print the quote '
                                        'details now?'), gtk.RESPONSE_YES,
                                      _("Print quote details"), _("Don't print"))

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
        with self.sysparam(ACCEPT_CHANGE_SALESPERSON=u'1'):
            wizard = OpticalSaleQuoteWizard(self.store)
            step = wizard.get_current_step()
            self.assertTrue(step.salesperson.get_sensitive())

        with self.sysparam(ACCEPT_CHANGE_SALESPERSON=u'0'):
            wizard = OpticalSaleQuoteWizard(self.store)
            step = wizard.get_current_step()
            self.assertFalse(step.salesperson.get_sensitive())

    @mock.patch('plugins.optical.opticalwizard.localtoday')
    def test_expire_date_validate(self, localtoday_):
        localtoday_.return_value = localdate(2020, 1, 5)

        wizard = OpticalSaleQuoteWizard(self.store)
        step = wizard.get_current_step()

        res = step.expire_date.emit('validate', localdate(2013, 1, 1).date())
        self.assertEquals(
            unicode(res),
            u"The expire date must be set to today or a future date.")

    @mock.patch('plugins.optical.opticalwizard.warning')
    @mock.patch('plugins.optical.opticalwizard.run_person_role_dialog')
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

    @mock.patch('plugins.optical.opticalwizard.run_person_role_dialog')
    def test_item_step_slave(self, run_person_role_dialog):
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
        step = wizard.get_current_step()
        item_slave = step.item_slave

        m = 'plugins.optical.opticalwizard._ItemSlave.get_remaining_quantity'
        with mock.patch(m) as get_remaining_quantity:
            get_remaining_quantity.return_value = decimal.Decimal("5")
            item_slave.get_order_item(sellable,
                                      decimal.Decimal("1"),
                                      decimal.Decimal("10"))
        saved = list(item_slave.get_saved_items())
        item_slave.remove_items(saved)

        with self.sysparam(REUTILIZE_DISCOUNT=u'0'):
            self.assertIsNone(item_slave.get_extra_discount(sellable))

        with self.sysparam(REUTILIZE_DISCOUNT=u'1'):
            self.assertIsNotNone(item_slave.get_extra_discount(sellable))

        for radio in step._radio_group.get_group():
            radio.toggled()

    @mock.patch('plugins.optical.opticalwizard.run_person_role_dialog')
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
        self.assertEquals(step.get_work_order(), step.work_orders_combo.read())

    @mock.patch('plugins.optical.opticalwizard.run_person_role_dialog')
    @mock.patch('plugins.optical.opticalwizard.run_dialog')
    def test_apply_discount(self, run_dialog, run_person_role_dialog):
        client = self.create_client()
        self.create_address(person=client.person)
        run_person_role_dialog.return_value = client

        sellable = self.create_sellable(price=100, product=True)
        sellable.barcode = u'123'

        wizard = OpticalSaleQuoteWizard(self.store)

        step = wizard.get_current_step()
        self.click(step.create_client)
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        slave = step.slaves['WO 1']
        slave.patient.update('Patient')
        slave.estimated_finish.update(localdate(2020, 1, 5))
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        step.item_slave.barcode.set_text(u'123')
        self.activate(step.item_slave.barcode)
        self.click(step.item_slave.add_sellable_button)

        label = step.item_slave.summary.get_value_widget()
        self.assertEqual(label.get_text(), '$100.00')

        # 10% of discount
        step.model.set_items_discount(decimal.Decimal(10))
        run_dialog.return_value = True
        self.click(step.item_slave.discount_btn)
        run_dialog.assert_called_once_with(
            DiscountEditor, step.item_slave.parent, step.item_slave.store,
            step.item_slave.model, user=api.get_current_user(step.store))
        self.assertEqual(label.get_text(), '$90.00')

        # Cancelling the dialog this time
        run_dialog.reset_mock()
        run_dialog.return_value = None
        self.click(step.item_slave.discount_btn)
        run_dialog.assert_called_once_with(
            DiscountEditor, step.item_slave.parent, step.item_slave.store,
            step.item_slave.model, user=api.get_current_user(step.store))
        self.assertEqual(label.get_text(), '$90.00')

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
