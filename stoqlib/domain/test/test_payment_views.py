# -*- coding: utf-8 -*-
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

__tests__ = 'stoqlib/domain/payment/views.py'

from dateutil.relativedelta import relativedelta

from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import InPaymentView
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.dateutils import localtoday


class TestInPaymentView(DomainTest):
    def test_has_late_payments(self):
        client = self.create_client()
        today = localtoday().date()
        method = PaymentMethod.get_by_name(self.store, u'bill')

        # client does not have any payments
        self.assertFalse(InPaymentView.has_late_payments(self.store,
                                                         client.person))

        # client has payments that are not overdue
        payment = self.create_payment(Payment.TYPE_IN,
                                      today + relativedelta(days=1),
                                      method=method)
        payment.group = self.create_payment_group()
        payment.group.payer = client.person
        self.assertFalse(InPaymentView.has_late_payments(self.store,
                                                         client.person))

        # client has overdue payments
        payment = self.create_payment(Payment.TYPE_IN,
                                      today - relativedelta(days=2),
                                      method=method)
        payment.status = Payment.STATUS_PENDING
        payment.group = self.create_payment_group()
        payment.group.payer = client.person
        self.assertTrue(InPaymentView.has_late_payments(self.store,
                                                        client.person))
