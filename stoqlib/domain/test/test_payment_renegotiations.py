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

from stoqlib.domain.payment.renegotiation import PaymentRenegotiation
from stoqlib.domain.test.domaintest import DomainTest


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
