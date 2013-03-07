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

from stoqlib.domain.payment.card import CreditCardData
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.gui.editors.paymentmethodeditor import CardDeviceEditor
from stoqlib.gui.editors.paymentmethodeditor import CardDeviceListSlave
from stoqlib.gui.editors.paymentmethodeditor import CardOperationCostEditor
from stoqlib.gui.editors.paymentmethodeditor import CardOperationCostListSlave
from stoqlib.gui.editors.paymentmethodeditor import CardPaymentMethodEditor
from stoqlib.gui.editors.paymentmethodeditor import CreditProviderEditor
from stoqlib.gui.uitestutils import GUITest


class TestCardDeviceEditor(GUITest):
    def testCreate(self):
        editor = CardDeviceEditor(self.store)
        self.check_editor(editor, 'editor-carddeviceeditor-create')

    def testShow(self):
        device = self.create_card_device()
        editor = CardDeviceEditor(self.store, device)
        self.check_editor(editor, 'editor-carddeviceeditor-show')


class TestCardOperationCostEditor(GUITest):
    def testCreate(self):
        device = self.create_card_device()
        editor = CardOperationCostEditor(self.store, None, device)
        self.check_editor(editor, 'editor-cardoperationcosteditor-create')

    def testShow(self):
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
        self.create_operation_cost(device=device, provider=provider, start=4, end=6)

        cost = self.create_operation_cost(device=device, provider=provider)
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
    def testShow(self):
        provider = self.create_credit_provider()
        editor = CreditProviderEditor(self.store, provider)
        self.check_editor(editor, 'editor-creditprovidereditor-show')


class TestCardDeviceListSlave(GUITest):

    @mock.patch('stoqlib.gui.editors.paymentmethodeditor.yesno')
    def testShow(self, yesno):
        device = self.create_card_device(u'Cielo')
        self.create_card_device(u'Santander')

        slave = CardDeviceListSlave(store=self.store)
        slave.set_reuse_store(self.store)
        self.check_slave(slave, 'slave-carddevicelist-show')

        slave.listcontainer.list.select(device)

        yesno.return_value = True
        self.click(slave.listcontainer.remove_button)
        yesno.assert_called_once_with('Removing this device will also remove'
                                      ' all related costs.', gtk.RESPONSE_NO,
                                  "Remove",
                                  "Keep device")


class TestCardOperationCostListSlave(GUITest):

    def testShow(self):
        device = self.create_card_device(u'Cielo')
        cost = self.create_operation_cost(device=device)

        slave = CardOperationCostListSlave(store=self.store, device=device)
        slave.set_reuse_store(self.store)
        self.check_slave(slave, 'slave-cardoperationcost-show')

        slave.listcontainer.list.select(cost)

        self.click(slave.listcontainer.remove_button)


class TestCardPaymentMethodEditor(GUITest):
    def testShow(self):
        method = self.get_payment_method(u'card')
        editor = CardPaymentMethodEditor(self.store, method)
        self.check_editor(editor, 'editor-cardpaymentmethod-show')
