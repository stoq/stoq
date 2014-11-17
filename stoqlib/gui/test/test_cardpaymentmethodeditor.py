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

from decimal import Decimal

from stoqlib.domain.payment.card import (CreditCardData, CreditProvider,
                                         CardPaymentDevice, CardOperationCost)
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.gui.editors.paymentmethodeditor import CardDeviceEditor
from stoqlib.gui.editors.paymentmethodeditor import CardDeviceListSlave
from stoqlib.gui.editors.paymentmethodeditor import CardOperationCostEditor
from stoqlib.gui.editors.paymentmethodeditor import CardOperationCostListSlave
from stoqlib.gui.editors.paymentmethodeditor import CardPaymentDetailsEditor
from stoqlib.gui.editors.paymentmethodeditor import CardPaymentMethodEditor
from stoqlib.gui.editors.paymentmethodeditor import CreditProviderEditor
from stoqlib.gui.editors.paymentmethodeditor import ProviderListSlave
from stoqlib.gui.test.uitestutils import GUITest


class TestCardDeviceEditor(GUITest):
    def test_create(self):
        editor = CardDeviceEditor(self.store)
        self.check_editor(editor, 'editor-carddeviceeditor-create')

    def test_show(self):
        device = self.create_card_device()
        editor = CardDeviceEditor(self.store, device)
        self.check_editor(editor, 'editor-carddeviceeditor-show')


class TestCardOperationCostEditor(GUITest):
    def test_create(self):
        device = self.create_card_device()
        editor = CardOperationCostEditor(self.store, None, device)
        self.check_editor(editor, 'editor-cardoperationcosteditor-create')

    def test_show(self):
        cost = self.create_operation_cost()
        device = cost.device
        editor = CardOperationCostEditor(self.store, cost, device)
        self.check_editor(editor, 'editor-cardoperationcosteditor-show')

    def test_installment_limits(self):
        card_method = self.store.find(PaymentMethod, method_name=u'card').one()
        card_method.max_installments = 16

        device = self.create_card_device()
        provider = self.create_credit_provider()
        cost = self.create_operation_cost(device=device, provider=provider,
                                          start=2, end=5)
        editor = CardOperationCostEditor(self.store, cost, cost.device)

        editor.card_type.update(CreditCardData.TYPE_CREDIT)

        upper_start = editor.installment_start.get_adjustment().get_upper()
        upper_end = editor.installment_end.get_adjustment().get_upper()

        self.assertEquals(upper_start, 1)
        self.assertEquals(upper_end, 1)

        editor.card_type.update(CreditCardData.TYPE_CREDIT_INSTALLMENTS_STORE)

        upper_start = editor.installment_start.get_adjustment().get_upper()
        upper_end = editor.installment_end.get_adjustment().get_upper()

        self.assertEquals(upper_start, 16)
        self.assertEquals(upper_end, 16)

    def test_validation(self):
        device = self.create_card_device()
        provider = self.create_credit_provider()
        # Create another cost to test validation
        self.create_operation_cost(device=device, provider=provider, start=4, end=6,
                                   card_type=CreditCardData.TYPE_CREDIT_INSTALLMENTS_STORE)

        cost = self.create_operation_cost(device=device, provider=provider,
                                          card_type=CreditCardData.TYPE_CREDIT_INSTALLMENTS_STORE)
        editor = CardOperationCostEditor(self.store, cost, cost.device)

        self.assertValid(editor, ['installment_start', 'installment_end'])

        # Range [1, 3] is invalid
        editor.installment_start.set_text('3')
        editor.installment_end.set_text('1')
        self.assertInvalid(editor, ['installment_start', 'installment_end'])

        editor.installment_start.set_text('1')
        editor.installment_end.set_text('3')
        self.assertValid(editor, ['installment_start', 'installment_end'])

        editor.installment_start.set_text('1')
        editor.installment_end.set_text('4')
        self.assertInvalid(editor, ['installment_start', 'installment_end'])

        editor.installment_start.set_text('7')
        editor.installment_end.set_text('8')
        self.assertValid(editor, ['installment_start', 'installment_end'])

        editor.fee.set_text('10')
        self.click(editor.main_dialog.ok_button)

        self.assertEquals(cost.fee, 10)
        self.assertEquals(cost.installment_start, 7)
        self.assertEquals(cost.installment_end, 8)


class TestCreditProviderEditor(GUITest):
    def test_show(self):
        provider = self.create_credit_provider()
        editor = CreditProviderEditor(self.store, provider)
        self.check_editor(editor, 'editor-creditprovidereditor-show')

    def test_validation(self):
        provider = self.create_credit_provider()
        editor = CreditProviderEditor(self.store, provider)

        editor.max_installments.set_value(-1)
        self.assertInvalid(editor, ['max_installments'])
        self.assertNotSensitive(editor.main_dialog, ['ok_button'])
        editor.max_installments.set_value(0)
        self.assertInvalid(editor, ['max_installments'])
        self.assertNotSensitive(editor.main_dialog, ['ok_button'])
        editor.max_installments.set_value(1)
        self.assertValid(editor, ['max_installments'])
        self.assertSensitive(editor.main_dialog, ['ok_button'])


class TestCardPaymentDetailsEditor(GUITest):
    def test_show(self):
        provider = self.create_credit_provider(u'VISANET')
        device = self.create_card_device()

        card = self.create_credit_card_data(provider, device)

        editor = CardPaymentDetailsEditor(self.store, card)
        self.check_editor(editor, 'editor-cardpaymentdetailseditor-show')

    def test_edit(self):
        # Create original card data with operation costs
        card_data_old = self._create_card_data(device_description=u'CRED1',
                                               provider_name=u'CARD1',
                                               fee=Decimal('5'),
                                               fare=Decimal('1.23'),
                                               payment_value=Decimal('10'))

        # Create a card payment associated with a device and a credit provider
        payment_value = Decimal('10')
        card_payment = self.create_credit_card_data(card_data_old.provider,
                                                    card_data_old.device,
                                                    payment_value=payment_value)
        card_payment.auth = 654321

        card_payment.fee = card_data_old.fee
        card_payment.fare = card_data_old.fare
        card_payment.fee_value = card_data_old.fee_value

        # Create new card data
        card_data_new = self._create_card_data(device_description=u'CRED2',
                                               provider_name=u'CARD2',
                                               fee=Decimal('7'),
                                               fare=Decimal('3.11'),
                                               payment_value=Decimal('10'))

        editor = CardPaymentDetailsEditor(self.store, card_payment)

        # Verify if the original card data was loaded correctly
        self.assertEquals(editor.device.get_selected(), card_payment.device)
        self.assertEquals(editor.provider.get_selected(), card_payment.provider)
        self.assertEquals(int(editor.auth.get_text()), card_payment.auth)

        self.assertEquals(card_payment.fee, card_data_old.fee)
        self.assertEquals(card_payment.fee_value, card_data_old.fee_value)
        self.assertEquals(card_payment.fare, card_data_old.fare)

        # add new providers on GUI
        editor.device.append_item(card_data_new.device.description, card_data_new.device)
        editor.provider.append_item(card_data_new.provider.short_name, card_data_new.provider)

        # Change data on editor
        editor.device.select_item_by_data(card_data_new.device)
        editor.provider.select_item_by_data(card_data_new.provider)
        editor.auth.set_text('123456')

        self.click(editor.main_dialog.ok_button)

        # Verify if the changes were saved into the model correctly
        self.assertEquals(card_payment.device, card_data_new.device)
        self.assertEquals(card_payment.provider, card_data_new.provider)
        self.assertEquals(card_payment.auth, 123456)
        self.assertEquals(card_payment.fee, card_data_new.fee)
        self.assertEquals(card_payment.fee_value, card_data_new.fee_value)
        self.assertEquals(card_payment.fare, card_data_new.fare)

    def _create_card_data(self, device_description=u'', provider_name=u'',
                          fee=0, fare=0, payment_value=0):
        provider = self.create_credit_provider(short_name=provider_name)
        device = self.create_card_device(device_description)

        operation_cost = self.create_operation_cost(device=device,
                                                    provider=provider)
        operation_cost.fee = fee
        operation_cost.fare = fare
        operation_cost.fee_value = operation_cost.fee * payment_value / 100

        return operation_cost


class TestProviderListSlave(GUITest):
    def test_show(self):
        self.create_credit_provider()
        slave = ProviderListSlave(store=self.store, reuse_store=True)
        self.check_slave(slave, 'slave-providerlist-show')

    @mock.patch('stoqlib.gui.editors.paymentmethodeditor.info')
    @mock.patch('stoqlib.gui.editors.paymentmethodeditor.yesno')
    def test_remove(self, yesno, info):
        provider = self.create_credit_provider(u'Default Provider')
        check_provider = self.store.find(CreditProvider, short_name=u'Default Provider').count()
        self.assertEquals(check_provider, 1)
        slave = ProviderListSlave(store=self.store, reuse_store=True)
        slave.listcontainer.list.select(provider)

        # Try remove the provider it's being referenced by a operation cost
        operation_cost = self.create_operation_cost(provider=provider)
        yesno.return_value = gtk.RESPONSE_OK
        self.click(slave.listcontainer.remove_button)
        info.assert_called_with("You can not remove this provider.\n"
                                "It is being used in card device.")

        # Try remove the provider it's being referenced by a credit card data
        operation_cost.provider = None
        card_data = self.create_credit_card_data(provider=provider)
        self.click(slave.listcontainer.remove_button)
        info.assert_called_with("You can not remove this provider.\n"
                                "You already have payments using this provider.")

        card_data.provider = None
        self.click(slave.listcontainer.remove_button)
        yesno.assert_called_with("Do you want remove %s?" % provider.short_name,
                                 gtk.RESPONSE_NO,
                                 "Remove",
                                 "Cancel")
        check_provider = self.store.find(CreditProvider, short_name=u'Default Provider').count()
        self.assertEquals(check_provider, 0)


class TestCardDeviceListSlave(GUITest):

    def test_show(self):
        self.create_card_device(u'Cielo')
        self.create_card_device(u'Santander')

        slave = CardDeviceListSlave(store=self.store, reuse_store=True)
        self.check_slave(slave, 'slave-carddevicelist-show')

    @mock.patch('stoqlib.gui.editors.paymentmethodeditor.yesno')
    @mock.patch('stoqlib.gui.editors.paymentmethodeditor.info')
    def test_remove(self, info, yesno):
        device = self.create_card_device(u'Default Device')
        devices = self.store.find(CardPaymentDevice, description=u'Default Device').count()
        self.assertEquals(devices, 1)

        slave = CardDeviceListSlave(store=self.store, reuse_store=True)
        slave.listcontainer.list.select(device)
        yesno.return_value = True

        self.create_operation_cost(device=device)
        provider = self.create_credit_provider(u"Provider")
        provider.provider_id = u"PROVIDER TEST"
        provider.default_device = device
        self.create_credit_card_data(device=device, provider=provider)

        self.click(slave.listcontainer.remove_button)
        providers = self.store.find(CreditProvider, default_device=device).count()
        info.assert_called_with("Can not remove this device.\n"
                                "It is being used as default device in %s credit provider(s)."
                                % providers)

        provider.default_device = None
        self.click(slave.listcontainer.remove_button)
        yesno.assert_called_once_with("Removing this device will also remove"
                                      " all related costs.", gtk.RESPONSE_NO,
                                      "Remove",
                                      "Keep device")

        # Check if device and its references were deleted
        devices = self.store.find(CardPaymentDevice, description=u'Default Device').count()
        operations = self.store.find(CardOperationCost, device=device).count()
        card_data = self.store.find(CreditCardData, device=device).count()
        self.assertEquals(devices, 0)
        self.assertEquals(operations, 0)
        self.assertEquals(card_data, 0)


class TestCardOperationCostListSlave(GUITest):

    def test_show(self):
        device = self.create_card_device(u'Cielo')
        cost = self.create_operation_cost(device=device)

        slave = CardOperationCostListSlave(store=self.store, device=device,
                                           reuse_store=True)
        self.check_slave(slave, 'slave-cardoperationcost-show')

        slave.listcontainer.list.select(cost)

        self.click(slave.listcontainer.remove_button)


class TestCardPaymentMethodEditor(GUITest):
    def test_show(self):
        method = self.get_payment_method(u'card')
        editor = CardPaymentMethodEditor(self.store, method)
        self.check_editor(editor, 'editor-cardpaymentmethod-show')
