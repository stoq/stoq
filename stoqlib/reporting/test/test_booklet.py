# -*- Mode: Python; coding: utf-8 -*-
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

import datetime
import decimal

from stoqlib.api import api
from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.reporting.test.reporttest import ReportTest
from stoqlib.reporting.booklet import BookletReport


class TestBooklet(ReportTest):
    """Booklet tests"""

    def setUp(self):
        super(TestBooklet, self).setUp()

        api.sysparam.set_string(
            self.store,
            'BOOKLET_INSTRUCTIONS',
            u"Instruction line 1\n"
            u"Instruction line 2\n"
            u"Instruction line 3\n"
            u"Instruction line 4\n"
            # This should not appear as it's limited to 4 lines
            u"Instruction line 5\n"
        )

    def test_booklet_with_sale_pdf(self):
        due_dates = [
            datetime.datetime(2012, 01, 05),
            datetime.datetime(2012, 02, 05),
            datetime.datetime(2012, 03, 05),
            datetime.datetime(2012, 04, 05),
            datetime.datetime(2012, 05, 05),
        ]
        items = [
            (u"Batata", 2, decimal.Decimal('10')),
            (u"Tomate", 3, decimal.Decimal('15.5')),
            (u"Banana", 1, decimal.Decimal('5.25')),
        ]

        client = self.create_client()
        client.credit_limit = decimal.Decimal('100000')
        address = self.create_address()
        address.person = client.person

        sale = self.create_sale(client=client,
                                branch=get_current_branch(self.store))
        for description, quantity, price in items:
            sellable = self.add_product(sale, price, quantity)
            sellable.description = description

        sale.order()
        method = PaymentMethod.get_by_name(self.store, u'store_credit')
        method.max_installments = 12
        method.create_payments(Payment.TYPE_IN,
                               sale.group, sale.branch,
                               value=sale.get_total_sale_amount(),
                               due_dates=due_dates)
        sale.confirm()
        sale.identifier = 123

        for i, payment in enumerate(sale.group.payments):
            payment.identifier = 66 + i

        self._diff_expected(BookletReport, 'booklet-with-sale',
                            sale.group.payments)

    def test_booklet_without_sale_pdf(self):
        method = PaymentMethod.get_by_name(self.store, u'store_credit')
        method.max_installments = 12
        group = self.create_payment_group()
        payment = self.create_payment(payment_type=Payment.TYPE_IN,
                                      date=datetime.datetime(2012, 03, 03),
                                      value=decimal.Decimal('10.5'),
                                      method=method)
        payment.group = group
        payment.identifier = 666

        client = self.create_client()
        address = self.create_address()
        address.person = client.person
        client.credit_limit = decimal.Decimal('100000')
        group.payer = client.person

        self._diff_expected(BookletReport, 'booklet-without-sale',
                            group.payments)
