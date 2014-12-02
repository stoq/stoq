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

from kiwi.currency import currency

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.reporting.financial import FinancialIntervalReport


class TestAccount(DomainTest):
    def test_report(self):
        f = FinancialIntervalReport(self.store, 2012)
        f.run()
        data = f.get_data()

        # ===> Check banks transactions per month <===
        banks = data.get(u'Banks')
        # January
        self.assertEquals(banks[0], [(u'Banks', 0), (u'Banco do Brasil', currency("33013.67"))])
        # February
        self.assertEquals(banks[1], [(u'Banks', 0), (u'Banco do Brasil', currency("-8325.35"))])
        # Other months (March - December)
        for n in range(2, 12):
            self.assertEquals(banks[n], [(u'Banks', 0), (u'Banco do Brasil', 0)])

        # ===> Check Expenses transactions <===
        expenses = data.get(u'Expenses')
        # January
        self.assertEquals(expenses[0],
                          [(u'Expenses', 0),
                           (u'Aluguel', currency("850")),
                           (u'Luz', currency("120.18")),
                           (u'Sal\xe1rios', currency("4692.76")),
                           (u'Telefonia', currency("232.30")),
                           (u'Impostos', currency("6843.91"))])
        # February
        self.assertEquals(expenses[1],
                          [(u'Expenses', 0),
                           (u'Aluguel', currency("850")),
                           (u'Luz', currency("138.48")),
                           (u'Sal\xe1rios', currency("4502.48")),
                           (u'Telefonia', 0),
                           (u'Impostos', currency("2834.39"))])
        # Other months (March - December)
        for n in range(2, 12):
            self.assertEquals(expenses[n],
                              [(u'Expenses', 0), (u'Aluguel', 0), (u'Luz', 0),
                               (u'Sal\xe1rios', 0), (u'Telefonia', 0), (u'Impostos', 0)])

        # ===> Check Income transactions <===
        income = data.get(u'Income')
        # January
        self.assertEquals(income[0],
                          [(u'Income', currency("-45752.82"))])
        # Other months (February - December)
        for n in range(1, 12):
            self.assertEquals(income[n],
                              [(u'Income', 0)])
