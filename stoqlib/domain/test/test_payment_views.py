import datetime

from dateutil.relativedelta import relativedelta

from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import InPaymentView
from stoqlib.domain.test.domaintest import DomainTest


class TestInPaymentView(DomainTest):
    def test_has_late_payments(self):
        client = self.create_client()
        today = datetime.date.today()
        method = PaymentMethod.get_by_name(self.trans, 'bill')

        #client does not have any payments
        self.assertFalse(InPaymentView.has_late_payments(self.trans,
                                                         client.person))

        #client has payments that are not overdue
        payment = self.create_payment(Payment.TYPE_IN,
                                      today + relativedelta(days=1),
                                      method)
        payment.group = self.create_payment_group()
        payment.group.payer = client.person
        self.assertFalse(InPaymentView.has_late_payments(self.trans,
                                                         client.person))

        #client has overdue payments
        payment = self.create_payment(Payment.TYPE_IN,
                                      today - relativedelta(days=2),
                                      method)
        payment.status = Payment.STATUS_PENDING
        payment.group = self.create_payment_group()
        payment.group.payer = client.person
        self.assertTrue(InPaymentView.has_late_payments(self.trans,
                                                         client.person))
