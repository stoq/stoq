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
from stoqlib.domain.workorder import WorkOrder, WorkOrderCategory, WorkOrderItem
from stoqlib.enums import ChangeSalespersonPolicy
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.lib.dateutils import localdate
from stoqlib.lib.translation import stoqlib_gettext

from ..opticaldomain import OpticalMedic, OpticalProduct
from ..opticaleditor import MedicEditor
from ..opticalreport import OpticalWorkOrderReceiptReport
from ..opticalwizard import OpticalSaleQuoteWizard, MedicRoleWizard
from .test_optical_domain import OpticalDomainTest


_ = stoqlib_gettext


class TestSaleQuoteWizard(GUITest, OpticalDomainTest):
    def _create_work_order_category(self):
        return WorkOrderCategory(store=self.store,
                                 name=u'Category',
                                 color=u'#ff0000')

    @mock.patch('plugins.optical.opticalwizard.yesno')
    @mock.patch('stoqlib.gui.wizards.salequotewizard.run_dialog')
    def test_confirm(self, run_dialog, yesno):
        self._create_work_order_category()
        client = self.create_client()
        medic = self.create_optical_medic()
        self.create_address(person=client.person)

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

        product = self.create_product(description=u'Package', is_package=True)
        sellable5 = product.sellable
        sellable5.barcode = u'666'
        product2 = self.create_product(description=u'Component', stock=5,
                                       storable=True)
        self.create_product_component(product=product,
                                      component=product2,
                                      component_quantity=5,
                                      price=2)
        wizard = OpticalSaleQuoteWizard(self.store)

        # First Step
        step = wizard.get_current_step()
        step.client_gadget.set_value(client)

        run_dialog.return_value = False
        self.click(step.notes_button)
        self.assertEquals(run_dialog.call_count, 1)
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

        # OpticalWorkOrder step
        step = wizard.get_current_step()
        slave = step.slaves['WO 1']
        slave.patient.update('Patient')
        slave.medic_combo.update(medic)
        slave.estimated_finish.update(localdate(2020, 1, 5))

        sale = wizard.model
        self.check_wizard(wizard, 'wizard-optical-work-order-step')

        self.click(wizard.next_button)

        # OpticalWorkOrderItem Step
        step = wizard.get_current_step()

        for barcode in [batch.batch_number, sellable.barcode,
                        sellable2.barcode, sellable4.barcode,
                        sellable5.barcode]:
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
        category = self._create_work_order_category()

        sale = self.create_sale()
        sale.status = Sale.STATUS_QUOTE
        workorder = self.create_workorder()
        workorder.sale = sale
        workorder.category = category
        OpticalSaleQuoteWizard(self.store, model=sale)

    def test_param_accept_change_salesperson(self):
        with self.sysparam(
                ACCEPT_CHANGE_SALESPERSON=int(ChangeSalespersonPolicy.ALLOW)):
            wizard = OpticalSaleQuoteWizard(self.store)
            step = wizard.get_current_step()
            self.assertTrue(step.salesperson.get_sensitive())
            self.assertIsNotNone(step.salesperson.read())

        with self.sysparam(
                ACCEPT_CHANGE_SALESPERSON=int(ChangeSalespersonPolicy.DISALLOW)):
            wizard = OpticalSaleQuoteWizard(self.store)
            step = wizard.get_current_step()
            self.assertFalse(step.salesperson.get_sensitive())
            self.assertIsNotNone(step.salesperson.read())

        with self.sysparam(
                ACCEPT_CHANGE_SALESPERSON=int(ChangeSalespersonPolicy.FORCE_CHOOSE)):
            wizard = OpticalSaleQuoteWizard(self.store)
            step = wizard.get_current_step()
            self.assertTrue(step.salesperson.get_sensitive())
            self.assertIsNone(step.salesperson.read())

    @mock.patch('stoqlib.gui.wizards.workorderquotewizard.warning')
    def test_remove_work_orders(self, warning):
        client = self.create_client()

        wizard = OpticalSaleQuoteWizard(self.store)
        step = wizard.get_current_step()
        step.client_gadget.set_value(client)
        for i in range(3):
            wo = self.create_workorder()
            wo.sale = step.model
            if i == 1:
                wo.status = WorkOrder.STATUS_WORK_FINISHED
                finished_order = wo

        wo.add_sellable(self.create_sellable())

        self.click(wizard.next_button)
        self.check_wizard(wizard, 'wizard-optical-work-order-step-multiple-wo')

        step = wizard.get_current_step()
        self.assertEquals(step.work_orders_nb.get_n_pages(), 3)

        # Test removing the first, with no items
        self.click(step.slaves['WO 1'].close_button)
        self.assertEquals(step.work_orders_nb.get_n_pages(), 2)

        # Test trying to remove the second, since the WO is finished
        self.click(step.slaves['WO 2'].close_button)
        warning.assert_called_once_with(
            ("You cannot remove workorder with the status '%s'") % finished_order.status_str)
        self.assertEquals(step.work_orders_nb.get_n_pages(), 2)

        # Test removing the third, which has items
        warning.reset_mock()
        self.click(step.slaves['WO 3'].close_button)
        warning.assert_called_once_with(
            'This workorder already has items and cannot be removed')
        self.assertEquals(step.work_orders_nb.get_n_pages(), 2)

    def test_remove_last_work_order(self):
        client = self.create_client()

        wizard = OpticalSaleQuoteWizard(self.store)
        step = wizard.get_current_step()
        step.client_gadget.set_value(client)

        self.click(wizard.next_button)
        step = wizard.get_current_step()

        # Trying to remove the only workorder of that sale
        self.click(step.slaves['WO 1'].close_button)
        self.assertEquals(step.work_orders_nb.get_n_pages(), 1)

    def test_add_work_orders(self):
        client = self.create_client()

        wizard = OpticalSaleQuoteWizard(self.store)
        step = wizard.get_current_step()
        step.client_gadget.set_value(client)

        self.click(wizard.next_button)
        step = wizard.get_current_step()

        # Add a new tab
        self.click(step.new_tab_button)
        self.assertEquals(step.work_orders_nb.get_n_pages(), 2)

    def test_item_step(self):
        client = self.create_client()
        medic = self.create_optical_medic()
        wizard = OpticalSaleQuoteWizard(self.store)
        step = wizard.get_current_step()
        step.client_gadget.set_value(client)
        for i in range(2):
            wo = self.create_workorder()
            wo.sale = step.model

        self.click(wizard.next_button)

        step = wizard.get_current_step()
        for slave in step.slaves.values():
            slave.patient.update('Patient')
            slave.medic_combo.update(medic)
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

    def test_item_step_too_many(self):
        medic = self.create_optical_medic()
        client = self.create_client()
        client.status = client.STATUS_INDEBTED
        wizard = OpticalSaleQuoteWizard(self.store)
        step = wizard.get_current_step()
        step.client_gadget.set_value(client)
        for i in range(4):
            wo = self.create_workorder()
            wo.sale = step.model

        self.click(wizard.next_button)

        step = wizard.get_current_step()
        for slave in step.slaves.values():
            slave.patient.update('Patient')
            slave.medic_combo.update(medic)
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

    @mock.patch('plugins.optical.opticalwizard.yesno')
    def test_auto_reserve(self, yesno):
        # Data setup
        client = self.create_client()
        medic = self.create_optical_medic(crm_number=u'999')

        auto = self.create_storable(
            branch=api.get_current_branch(self.store),
            stock=10)
        auto.product.sellable.barcode = u'auto_reserve'
        OpticalProduct(store=self.store, product=auto.product,
                       auto_reserve=True)

        not_auto = self.create_storable(
            branch=api.get_current_branch(self.store),
            stock=10)
        not_auto.product.sellable.barcode = u'not_auto_reserve'
        OpticalProduct(store=self.store, product=not_auto.product,
                       auto_reserve=False)

        wizard = OpticalSaleQuoteWizard(self.store)
        # First step: Client
        step = wizard.get_current_step()
        step.client_gadget.set_value(client)
        self.click(wizard.next_button)

        # Second Step: optical data
        step = wizard.get_current_step()
        slave = step.slaves['WO 1']
        slave.patient.update('Patient')
        slave.medic_combo.update(medic)
        slave.estimated_finish.update(localdate(2020, 1, 5))

        # Third Step: Products
        self.click(wizard.next_button)
        step = wizard.get_current_step()

        # Add two items: One auto reserved and another not. Both with initially
        # 10 items on stock
        for barcode in ['auto_reserve', 'not_auto_reserve']:
            step.barcode.set_text(barcode)
            self.activate(step.barcode)
            step.quantity.update(5)
            self.click(step.add_sellable_button)

        # Finish the wizard
        yesno.return_value = False
        with mock.patch.object(self.store, 'commit'):
            self.click(wizard.next_button)

        # Now check the stock for the two items. The auto reverd should have the
        # stock decreased to 5. The one that not auto reserves should still be
        # at 10
        self.assertEquals(auto.get_total_balance(), 5)
        self.assertEquals(not_auto.get_total_balance(), 10)


class TestMedicRoleWizard(GUITest):
    @mock.patch('stoqlib.gui.templates.persontemplate.run_dialog')
    def test_medic_with_crm(self, run_dialog):
        individual = self.create_individual()
        person = individual.person
        person.name = u'Medic without crm'
        OpticalMedic(store=self.store, crm_number=u'', person=person)

        wizard = MedicRoleWizard(self.store, MedicEditor)
        step = wizard.get_current_step()
        step.person_document.update('0123')
        self.assertNotSensitive(wizard, ['next_button'])

        step.person_document.update('123')
        self.assertSensitive(wizard, ['next_button'])

    @mock.patch('stoqlib.gui.templates.persontemplate.run_dialog')
    def test_medic_without_crm(self, run_dialog):
        individual = self.create_individual()
        person = individual.person
        person.name = u'Medic without crm'
        OpticalMedic(store=self.store, crm_number=u'', person=person)

        wizard = MedicRoleWizard(self.store, MedicEditor)
        step = wizard.get_current_step()
        self.check_wizard(wizard, 'wizard-medic-without-crm-role-type-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertNotSensitive(wizard, ['next_button'])
        step.person_slave.name.update('medic without crm')
        step.person_slave.address_slave.street.update('street')
        step.person_slave.address_slave.streetnumber.update(123)
        step.person_slave.address_slave.district.update('district')
        self.assertNotSensitive(wizard, ['next_button'])
        crm_entry = step.role_editor.medic_details_slave.crm_number
        self.assertEquals(crm_entry.read(), u'')
        crm_entry.update('6789')
        self.assertSensitive(wizard, ['next_button'])
        self.click(wizard.next_button)

        medic = wizard.retval
        self.check_wizard(wizard, 'wizard-medic-without-crm-role-finish',
                          [medic, medic.person] + list(medic.person.addresses))

    @mock.patch('stoqlib.gui.templates.persontemplate.run_dialog')
    def test_individual_medic(self, run_dialog):
        individual = self.create_individual()
        person = individual.person
        person.name = u'Medic'
        individual_medic = OpticalMedic(store=self.store, crm_number=u'4321',
                                        person=person)

        wizard = MedicRoleWizard(self.store, MedicEditor)
        step = wizard.get_current_step()
        step.person_document.update(individual_medic.crm_number)
        self.check_wizard(wizard, 'wizard-individual-medic-role-type-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertNotSensitive(wizard, ['next_button'])
        step.person_slave.name.update('individual medic name')
        step.person_slave.address_slave.street.update('street')
        step.person_slave.address_slave.streetnumber.update(789)
        step.person_slave.address_slave.district.update('district')
        crm_entry = step.role_editor.medic_details_slave.crm_number
        self.assertEquals(crm_entry.read(), individual_medic.crm_number)
        self.assertSensitive(wizard, ['next_button'])
        self.click(wizard.next_button)

        medic = wizard.retval
        self.check_wizard(wizard, 'wizard-individual-medic-role-finish',
                          [medic, medic.person] + list(medic.person.addresses))

    @mock.patch('stoqlib.gui.templates.persontemplate.run_dialog')
    def test_company_medic(self, run_dialog):
        company = self.create_company()
        person = company.person
        company_medic = OpticalMedic(store=self.store, crm_number=u'1234',
                                     person=person)

        wizard = MedicRoleWizard(self.store, MedicEditor)
        step = wizard.get_current_step()
        step.person_document.update(company_medic.crm_number)
        step.company_check.set_active(True)
        self.check_wizard(wizard, 'wizard-company-medic-role-type-step')
        self.click(wizard.next_button)

        step = wizard.get_current_step()
        self.assertNotSensitive(wizard, ['next_button'])
        step.person_slave.name.update('company medic name')
        step.person_slave.address_slave.street.update('street')
        step.person_slave.address_slave.streetnumber.update(456)
        step.person_slave.address_slave.district.update('district')
        crm_entry = step.role_editor.medic_details_slave.crm_number
        self.assertEquals(crm_entry.read(), company_medic.crm_number)
        self.assertSensitive(wizard, ['next_button'])
        self.click(wizard.next_button)

        medic = wizard.retval
        self.check_wizard(wizard, 'wizard-company-medic-role-finish',
                          [medic, medic.person] + list(medic.person.addresses))
