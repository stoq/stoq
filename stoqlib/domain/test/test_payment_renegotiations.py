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

__tests__ = 'stoqlib/domain/payment/renegotiation.py'

from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.renegotiation import PaymentRenegotiation
from stoqlib.domain.test.domaintest import DomainTest


class TestRenegotiation(DomainTest):
    def test_can_set_renegotiated(self):
        payment = self.create_payment()
        renegotiation = self.create_payment_renegotiation(group=payment.group)
        self.assertFalse(renegotiation.can_set_renegotiated())
        payment.status = Payment.STATUS_PENDING
        self.assertTrue(renegotiation.can_set_renegotiated())

    def test_get_client_name(self):
        renegotiation = self.create_payment_renegotiation()
        self.assertEquals(renegotiation.get_client_name(), u'Client')
        renegotiation.client = None
        self.assertEquals(renegotiation.get_client_name(), u'')

    def test_get_items(self):
        renegotiation = self.create_payment_renegotiation()
        self.assertFalse(renegotiation.get_items().count())
        group = self.create_payment_group()
        group.renegotiation = renegotiation
        self.assertEquals(renegotiation.get_items().count(), 1)

    def test_set_renegotiated(self):
        payment = self.create_payment()
        renegotiation = self.create_payment_renegotiation(group=payment.group)
        with self.assertRaises(AssertionError):
            renegotiation.set_renegotiated()
        payment.status = Payment.STATUS_PENDING
        renegotiation.set_renegotiated()
        self.assertEquals(renegotiation.status,
                          renegotiation.STATUS_RENEGOTIATED)

    def test_add_item(self):
        renegotiation = self.create_payment_renegotiation()
        self.assertIsNone(renegotiation.add_item(payment=None))

    def test_remove_item(self):
        renegotiation = self.create_payment_renegotiation()
        self.assertIsNone(renegotiation.remove_item(payment=None))


class TestInPaymentView(DomainTest):
    def testRenegotiation(self):
        branch = self.create_branch(name=u'Branch')
        client = self.create_client(name=u'TestClient')
        rows = self.store.find(PaymentRenegotiation, branch_id=branch.id,
                               client=client).count()
        self.assertEquals(rows, 0)
        PaymentRenegotiation(branch=branch, client=client)
        rows = self.store.find(PaymentRenegotiation, branch_id=branch.id,
                               client=client).count()
        self.assertEquals(rows, 1)

    def testRenegotiated(self):
        branch = self.create_branch(name=u'Branch')
        client = self.create_client(name=u'TestClient')
        renegotiation = PaymentRenegotiation(branch=branch, client=client)
        rows = self.store.find(PaymentRenegotiation, branch_id=branch.id,
                               client=client,
                               status=renegotiation.STATUS_RENEGOTIATED).count()
        self.assertEquals(rows, 0)
        renegotiation.status = renegotiation.STATUS_RENEGOTIATED
        rows = self.store.find(PaymentRenegotiation, branch_id=branch.id,
                               client=client,
                               status=renegotiation.STATUS_RENEGOTIATED).count()
        self.assertEquals(rows, 1)
