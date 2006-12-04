# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   Johan Dahlin      <jdahlin@async.com.br>
##

import datetime

from stoqlib.domain.interfaces import IPaymentGroup
from stoqlib.domain.payment.payment import Payment
from stoqlib.lib.defaults import INTERVALTYPE_MONTH, METHOD_BILL

from stoqlib.domain.test.domaintest import DomainTest

class TestPaymentGroup(DomainTest):
    def testConfirm(self):
        # Actually it tests SaleAdaptToPaymentGroup.confirm
        sale = self.create_sale()

        sellable = self.create_sellable()
        item = sellable.add_sellable_item(sale, price=150)

        group = sale.addFacet(IPaymentGroup,
                              default_method=METHOD_BILL,
                              intervals=1,
                              interval_type=INTERVALTYPE_MONTH,
                              connection=self.trans)
        self.assertRaises(ValueError, group.confirm)

        payment = group.add_payment(10, "foo", None, destination=None,
                                    due_date=datetime.datetime.now())
        self.assertEqual(payment.status, Payment.STATUS_PREVIEW)
        group.confirm()
        self.assertEqual(payment.status, Payment.STATUS_PENDING)

