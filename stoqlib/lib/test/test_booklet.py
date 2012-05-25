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
import os
import tempfile

from stoqlib.api import api
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib import test
from stoqlib.lib.diffutils import diff_pdf_htmls
from stoqlib.lib.pdf import pdftohtml
from stoqlib.reporting.booklet import BookletReport


class TestBooklet(DomainTest):
    """Booklet tests"""

    def setUp(self):
        super(TestBooklet, self).setUp()

        api.sysparam(self.trans).BOOKLET_INSTRUCTIONS = (
            "Instruction line 1\n"
            "Instruction line 2\n"
            "Instruction line 3\n"
            "Instruction line 4\n"
            # This should not appear as it's limited to 4 lines
            "Instruction line 5\n"
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
            ("Batata", 2, decimal.Decimal('10')),
            ("Tomate", 3, decimal.Decimal('15.5')),
            ("Banana", 1, decimal.Decimal('5.25')),
            ]

        sale = self.create_sale(666)
        sale.client = self.create_client()
        for description, quantity, price in items:
            sellable = self.add_product(sale, price, quantity)
            sellable.description = description

        sale.order()
        method = PaymentMethod.get_by_name(self.trans, 'store_credit')
        method.max_installments = 12
        method.create_inpayments(sale.group,
                                 value=sale.get_total_sale_amount(),
                                 due_dates=due_dates)
        sale.confirm()

        for i, payment in zip(range(len(due_dates)), sale.group.payments):
            payment.id = 66 + i

        self._diff_expected(sale.group.payments, 'with-sale')

    def test_booklet_without_sale_pdf(self):
        method = PaymentMethod.get_by_name(self.trans, 'store_credit')
        method.max_installments = 12
        group = self.create_payment_group()
        payment = self.create_payment(payment_type=Payment.TYPE_IN,
                                      date=datetime.datetime(2012, 03, 03),
                                      value=decimal.Decimal('10.5'),
                                      method=method)
        payment.group = group
        payment.id = 666

        client = self.create_client()
        group.payer = client.person

        self._diff_expected(group.payments, 'without-sale')

    def _diff_expected(self, payments, expected_name):
        basedir = test.__path__[0]
        expected = os.path.join(basedir,
                                'booklet-%s.pdf.html' % expected_name)
        output = os.path.join(basedir,
                              'booklet-%s-tmp.pdf.html' % expected_name)

        def save_report(filename, payments):
            report = BookletReport(fp_tmp.name, payments)
            report._add_payments()
            pdf = report._pdf
            for booklet in pdf._booklets:
                date = datetime.date(2012, 01, 01)
                booklet.emission_date = report._format_date(date)
            report.save()

        if not os.path.isfile(expected):
            with tempfile.NamedTemporaryFile(prefix='stoq-booklet') as fp_tmp:
                save_report(fp_tmp.name, payments)
                with open(expected, 'w') as fp:
                    pdftohtml(fp_tmp.name, fp.name)
            return
        with tempfile.NamedTemporaryFile(prefix='stoq-booklet') as fp_tmp:
            save_report(fp_tmp.name, payments)
            with open(output, 'w') as fp:
                pdftohtml(fp_tmp.name, fp.name)

        # Diff and compare
        diff = diff_pdf_htmls(expected, output)
        os.unlink(output)

        self.failIf(diff, '%s\n%s' % ("Files differ, output:", diff))
