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
from dateutil.relativedelta import relativedelta
from kiwi.currency import currency
import mock

from stoqlib.domain.costcenter import CostCenterEntry
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.sale import Sale
from stoqlib.enums import LatePaymentPolicy, ChangeSalespersonPolicy
from stoqlib.gui.test.uitestutils import GUITest
from stoqlib.gui.wizards.salewizard import ConfirmSaleWizard
from stoqlib.lib.dateutils import localdatetime, localtoday
from stoqlib.lib.parameters import sysparam


class TestConfirmSaleWizard(GUITest):

    def _create_wizard(self, sale=None, total_paid=0):
        if not sale:
            # Create a sale and the wizard that will be used in where
            sale = self.create_sale()
            sale.identifier = 12345
            self.add_product(sale, price=10)

        self.sale = sale
        self.wizard = ConfirmSaleWizard(self.store, sale,
                                        subtotal=sale.get_total_sale_amount(),
                                        total_paid=total_paid)
        self.step = self.wizard.get_current_step()

    def _go_to_next(self):
        self.click(self.wizard.next_button)
        self.step = self.wizard.get_current_step()

    def _select_method(self, name):
        widget = self.step.pm_slave._widgets[name]
        widget.set_active(True)

    def _check_wizard(self, name, extra_models=None):
        models = self.collect_sale_models(self.sale)
        if extra_models:
            models.extend(extra_models)

        self.check_wizard(self.wizard, name, models=models)

    def test_queries(self):
        sale = self.create_sale()
        sale.identifier = 12345
        self.add_product(sale, price=10)

        self.sale = sale
        total = sale.get_total_sale_amount()

        with self.count_tracer() as tracer:
            self.wizard = ConfirmSaleWizard(self.store, sale,
                                            subtotal=total,
                                            total_paid=0)

        # NOTE: Document increases/decreases
        # 3: select user/branch/station (normally cached)
        # 1: select sales_person
        # 1: select transporter
        # 1: select cost cebnter
        # 3: select invoice number
        # 1: select payment method
        # 4: select sale_item
        #  - one is need_adjust_batches
        # 1: select payment status
        # 1: select the branch acronym for sale repr()
        self.assertEquals(tracer.count, 16)

    def test_create(self):
        self._create_wizard()

        module = 'stoqlib.gui.events.ConfirmSaleWizardFinishEvent.emit'
        with mock.patch(module) as emit:
            with mock.patch.object(self.store, 'commit'):
                self._go_to_next()
            self.assertEquals(emit.call_count, 1)
            args, kwargs = emit.call_args
            self.assertTrue(isinstance(args[0], Sale))

        self._check_wizard('wizard-sale-done-sold')
        self.assertEquals(self.sale.payments[0].method.method_name, u'money')

    def test_money_payment_with_trade(self):
        # A trade just passes total_paid=value for the trade value (ie, the
        # products being returned)
        self._create_wizard(total_paid=3)
        with mock.patch.object(self.store, 'commit'):
            self._go_to_next()

        self._check_wizard('wizard-sale-with-trade')
        self.assertEquals(self.sale.payments[0].method.method_name, u'money')

        # Since $30 was already paid, the client only had to pay $70
        self.assertEquals(self.sale.payments[0].value, 7)

    def test_sale_with_trade_same_value(self):
        self._create_wizard(total_paid=10)
        with mock.patch.object(self.store, 'commit'):
            self._go_to_next()

        self.assertFalse(self.wizard.need_create_payment())
        self.assertNotVisible(self.step, ['select_method_holder',
                                          'subtotal_expander'])
        self.assertNotSensitive(self.step.cash_change_slave,
                                ['received_value'])

        self._check_wizard('wizard-sale-with-trade-same-value')

        # No payment created, since the client already paid the whole value
        self.assertEquals(self.sale.payments.count(), 0)

    def test_sale_with_trade_as_discount(self):
        with contextlib.nested(self.sysparam(USE_TRADE_AS_DISCOUNT=True),
                               mock.patch.object(self.store, 'commit')):
            trade = self.create_trade(trade_value=100)
            sale = trade.new_sale
            self._create_wizard(sale=sale)

            discount_slave = self.step.discount_slave
            self.assertSensitive(discount_slave, ['discount_value'])
            self.assertEquals(discount_slave.discount_value.get_text(), '100.00')
            self.assertSensitive(self.wizard, ['next_button'])

            # Discount, greater then max discount + trade discount
            discount_slave.discount_value.set_text('190')
            self.assertNotSensitive(self.wizard, ['next_button'])
            discount_slave.discount_value.validate(force=True)

    def test_sale_payment_reserved(self):
        sale = self.create_sale()
        sale.identifier = 12345
        self.add_product(sale, price=100)
        method = PaymentMethod.get_by_name(self.store, u'check')
        p1 = method.create_payment(
            Payment.TYPE_IN, sale.group, sale.branch, 50)
        p2 = method.create_payment(
            Payment.TYPE_IN, sale.group, sale.branch, 50)

        for p in [p1, p2]:
            p.set_pending()
            p.due_date = localdatetime(2013, 1, 1)

        # Pay only one payment so there are 50 paid and 50 confirmed
        # (waiting to be paid) totalizing in 100 that's the total here.
        p1.pay(paid_date=localdatetime(2013, 1, 2))
        total_paid = sale.group.get_total_confirmed_value()

        self._create_wizard(sale=sale, total_paid=total_paid)

        self._check_wizard('wizard-sale-payment-reserved')
        self.assertNotVisible(self.step, ['select_method_holder',
                                          'subtotal_expander'])

        with mock.patch.object(self.store, 'commit'):
            self._go_to_next()
        # Make sure no payments were created
        self.assertEqual(set(sale.payments), set([p1, p2]))

    def test_sale_with_cost_center(self):
        cost_center = self.create_cost_center()

        self._create_wizard()
        self.step.cost_center.select(cost_center)
        self.check_wizard(self.wizard, 'wizard-sale-with-cost-center')

        entry = self.store.find(CostCenterEntry, cost_center=self.sale.cost_center)
        self.assertEquals(len(list(entry)), 0)

        with mock.patch.object(self.store, 'commit'):
            self._go_to_next()
        # FiscalCoupon calls this method
        self.sale.confirm()

        self.assertEquals(self.sale.cost_center, cost_center)

        entry = self.store.find(CostCenterEntry, cost_center=self.sale.cost_center)
        self.assertEquals(len(list(entry)), 1)

    def test_param_accept_change_salesperson_allow(self):
        with self.sysparam(
                ACCEPT_CHANGE_SALESPERSON=int(ChangeSalespersonPolicy.ALLOW)):
            self._create_wizard()
            self.assertTrue(self.step.salesperson.get_sensitive())
            self.assertIsNotNone(self.step.salesperson.read())

    def test_param_accept_change_salesperson_disallow(self):
        with self.sysparam(
                ACCEPT_CHANGE_SALESPERSON=int(ChangeSalespersonPolicy.DISALLOW)):
            self._create_wizard()
            self.assertFalse(self.step.salesperson.get_sensitive())
            self.assertIsNotNone(self.step.salesperson.read())

    def test_param_accept_change_salesperson_force_choose(self):
        with self.sysparam(
                ACCEPT_CHANGE_SALESPERSON=int(ChangeSalespersonPolicy.FORCE_CHOOSE)):
            self._create_wizard()
            self.assertTrue(self.step.salesperson.get_sensitive())
            self.assertIsNone(self.step.salesperson.read())

    def test_step_payment_method_check(self):
        sysparam.set_bool(self.store, 'MANDATORY_CHECK_NUMBER', False)
        self._create_wizard()
        self._select_method('check')
        self._go_to_next()

        # populate check and bank data
        self.bank_id = 123
        self.bank_branch = 456
        self.bank_account = 789

        # Finish the checkout
        with mock.patch.object(self.store, 'commit'):
            self._go_to_next()
        self.assertEquals(self.sale.payments[0].method.method_name, u'check')

        self._check_wizard('wizard-sale-step-payment-method-check')

    # FIXME: add a test with a configured bank account
    def test_step_payment_method_bill(self):
        client = self.create_client()
        self._create_wizard()
        self.step.client_gadget.set_value(client)
        self._select_method('bill')
        self._go_to_next()

        # Finish the checkout
        with mock.patch.object(self.store, 'commit'):
            self._go_to_next()

        self.assertEquals(self.sale.payments[0].method.method_name, 'bill')
        self._check_wizard('wizard-sale-step-payment-method-bill')

    def test_step_payment_method_card(self):
        self._create_wizard()
        self._select_method('card')
        self._go_to_next()

        # XXX: The step could provide an api to get the slave.
        self.step._method_slave.auth_number.update(1234)

        # Finish the checkout
        with mock.patch.object(self.store, 'commit'):
            self._go_to_next()

        self.assertEquals(self.sale.payments[0].method.method_name, 'card')

        models = []
        operation = PaymentMethod.get_by_name(self.store, u'card').operation
        for p in self.sale.payments:
            models.append(operation.get_card_data_by_payment(p))
        self._check_wizard('wizard-sale-step-payment-method-card', models)

    def test_step_payment_method_deposit(self):
        self._create_wizard()
        self._select_method('deposit')
        self._go_to_next()

        # Finish the checkout
        with mock.patch.object(self.store, 'commit'):
            self._go_to_next()
        self._check_wizard('wizard-sale-step-payment-method-deposit')
        self.assertEquals(self.sale.payments[0].method.method_name, 'deposit')

    def test_step_payment_method_store_credit(self):
        client = self.create_client()
        client.credit_limit = 1000

        self._create_wizard()
        self.step.client_gadget.set_value(client)

        self._select_method('store_credit')
        self._go_to_next()

        # confirm the checkout
        with mock.patch.object(self.store, 'commit'):
            self._go_to_next()

        self._check_wizard('wizard-sale-step-payment-method-store-credit')

    def test_sale_to_client_without_store_credit(self):
        client = self.create_client(u'Juca')
        client2 = self.create_client(u'Chico')

        # Give $2 of store credit limit for client2
        client2.credit_limit = 2

        self._create_wizard()
        self.step.client_gadget.set_value(client)

        self._select_method(u'store_credit')

        # When the client has no credit at all, the option should not be there
        self.assertFalse(self.step.pm_slave._widgets['store_credit'].get_visible())

        self.step.client_gadget.set_value(client2)
        self.assertTrue(self.step.pm_slave._widgets['store_credit'].get_visible())

        # It should have fallback to money
        self.assertEquals(
            self.step.pm_slave.get_selected_method().method_name, u'money')

    def test_sale_to_client_without_credit(self):
        client = self.create_client(name=u'Juca')
        client2 = self.create_client(name=u'Chico')

        # Give $2 of credit to client2
        method = self.store.find(PaymentMethod, method_name=u'credit').one()
        payment = self.create_payment(payment_type=Payment.TYPE_OUT,
                                      value=2, method=method)
        payment.group.payer = client2.person
        payment.set_pending()
        payment.pay()

        self._create_wizard()
        self.step.client_gadget.set_value(client)
        self._select_method(u'credit')

        # When the client has no credit at all, the option should not be there
        self.assertFalse(self.step.pm_slave._widgets['credit'].get_visible())

        self.step.client_gadget.set_value(client2)
        self.assertEquals(client2, self.step.client.read())
        self.assertTrue(self.step.pm_slave._widgets['credit'].get_visible())

        # It should have fallback to money
        self.assertEquals(
            self.step.pm_slave.get_selected_method().method_name, u'money')

    @mock.patch('stoqlib.gui.widgets.searchentry.run_dialog')
    def test_sale_to_client_with_late_payments(self, run_dialog):
        #: this parameter allows a client to buy even if he has late payments
        sysparam.set_int(self.store, 'LATE_PAYMENTS_POLICY',
                         int(LatePaymentPolicy.ALLOW_SALES))

        sale = self.create_sale()
        sale.identifier = 12345
        self.add_product(sale)
        sale.client = self.create_client()
        self._create_wizard(sale=sale)
        wizard = self.wizard
        step = self.step

        money_method = PaymentMethod.get_by_name(self.store, u'money')
        today = localtoday().date()

        sale.client.credit_limit = currency('90000000000')
        step.client.emit('changed')
        self._select_method(u'money')

        # checks if a client can buy normally
        self.assertTrue(wizard.next_button.props.sensitive)

        # checks if a client with late payments can buy
        payment = self.create_payment(Payment.TYPE_IN,
                                      today - relativedelta(days=1),
                                      method=money_method)
        payment.status = Payment.STATUS_PENDING
        payment.group = self.create_payment_group()
        payment.group.payer = sale.client.person

        self._select_method('bill')
        self.assertTrue(wizard.next_button.props.sensitive)

        self._select_method(u'store_credit')
        self.assertTrue(wizard.next_button.props.sensitive)

        #: this parameter disallows a client with late payments to buy with
        #: store credit
        sysparam.set_int(self.store, 'LATE_PAYMENTS_POLICY',
                         int(LatePaymentPolicy.DISALLOW_STORE_CREDIT))

        # checks if a client can buy normally
        payment.due_date = today
        self.assertEquals(step.client.emit('validate', sale.client), None)
        self.assertTrue(wizard.next_button.props.sensitive)

        # checks if a client with late payments can buy with money method
        self._select_method(u'money')
        payment.due_date = today - relativedelta(days=3)
        self.assertEquals(step.client.emit('validate', sale.client), None)
        self.assertTrue(wizard.next_button.props.sensitive)

        # checks if a client with late payments can buy with store credit
        self._select_method(u'store_credit')
        self.assertEquals(
            unicode(step.client.emit('validate', sale.client)),
            u'It is not possible to sell with store credit for clients with '
            'late payments.')
        # self.assertFalse(wizard.next_button.props.sensitive)
        step.client.validate(force=True)
        # FIXME: This is not updating correcly
        # self.assertNotSensitive(wizard, ['next_button'])

        #: this parameter disallows a client with late payments to buy
        sysparam.set_int(self.store, 'LATE_PAYMENTS_POLICY',
                         int(LatePaymentPolicy.DISALLOW_SALES))

        # checks if a client can buy normally
        payment.due_date = today
        self.assertEquals(step.client.emit('validate', sale.client), None)

        # checks if a client with late payments can buy
        payment.due_date = today - relativedelta(days=3)

        self._select_method(u'store_credit')
        self.assertEquals(
            unicode(step.client.emit('validate', sale.client)),
            u'It is not possible to sell for clients with late payments.')
        step.client.activate()
        self.assertEquals(run_dialog.call_count, 0)

        self._select_method('check')
        self.assertEquals(
            unicode(step.client.emit('validate', sale.client)),
            u'It is not possible to sell for clients with late payments.')

        self._select_method(u'store_credit')
        sysparam.set_int(self.store, 'LATE_PAYMENTS_POLICY',
                         int(LatePaymentPolicy.ALLOW_SALES))

        sale.client.credit_limit = currency("9000")
        # Force validation since we changed the credit limit.
        step.force_validation()

        self.click(wizard.next_button)

        # finish wizard
        with mock.patch.object(self.store, 'commit'):
            self.click(wizard.next_button)

        self.assertEquals(sale.payments[0].method.method_name, u'store_credit')

    def test_overpaid_sale(self):
        sale = self.create_sale()
        sale.identifier = 1345
        self.add_product(sale, price=10)
        payment = self.create_payment(payment_type=Payment.TYPE_IN, value=50,
                                      group=sale.group)
        payment.set_pending()
        payment.pay()

        self._create_wizard(sale=sale, total_paid=50)
        self._check_wizard('wizard-sale-overpaid-sale')

        # The method selection holder should be hidden (since the client has
        # overpaid
        self.assertFalse(self.step.select_method_holder.get_visible())
        self.assertTrue(self.step.cash_change_slave.credit_checkbutton.get_visible())
        self.click(self.step.cash_change_slave.credit_checkbutton)

        # confirm the checkout
        with mock.patch.object(self.store, 'commit'):
            self._go_to_next()

        payments = list(sale.group.get_items())
        self.assertEquals(len(payments), 2)
        self.assertEquals(payments[0], payment)
        self.assertEquals(payments[1].payment_type, Payment.TYPE_OUT)
        self.assertEquals(payments[1].value, 40)

        sale.confirm(till=self.create_till())


class TestSalesPersonStep(GUITest):
    def test_update_widgets(self):
        client1 = self.create_client(name=u'Client01')
        client2 = self.create_client(name=u'Client02')
        client1.credit_limit = 1000
        sale_item = self.create_sale_item()
        subtotal = sale_item.sale.get_sale_subtotal()
        wizard = ConfirmSaleWizard(store=self.store, model=sale_item.sale,
                                   subtotal=subtotal, total_paid=0)
        salespersonstep = wizard._first_step

        # Right now, there should be no client selected and the methods store
        # credit and credit should be disabled
        self.check_wizard(wizard=wizard,
                          ui_test_name='wizard-sales-person-step')

        # After selecting the client1, the option store credit should be available
        salespersonstep.client_gadget.set_value(client1)
        self.check_wizard(wizard=wizard,
                          ui_test_name=
                          'wizard-sales-person-step-with-store-credit-radio')

        # selecting the client2 should disable the store credit again.
        salespersonstep.client_gadget.set_value(client2)
        self.check_wizard(wizard=wizard,
                          ui_test_name=
                          'wizard-sales-person-step-without-store-credit-radio')

        # De-selecting the client should not break, and also disable the methods
        # IE, they should be just like when the dialog was opened
        salespersonstep.client_gadget.set_value(None)
        self.check_wizard(wizard=wizard,
                          ui_test_name='wizard-sales-person-step-client-none')
