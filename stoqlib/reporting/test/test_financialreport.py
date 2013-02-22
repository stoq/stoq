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
        self.assertEquals(
            data,
            {u'Banks': [[(u'Banks', 0), (u'Banco do Brasil', currency("58491.97"))],
                        [(u'Banks', 0), (u'Banco do Brasil', currency("8325.35"))],
                        [(u'Banks', 0), (u'Banco do Brasil', 0)],
                        [(u'Banks', 0), (u'Banco do Brasil', 0)],
                        [(u'Banks', 0), (u'Banco do Brasil', 0)],
                        [(u'Banks', 0), (u'Banco do Brasil', 0)],
                        [(u'Banks', 0), (u'Banco do Brasil', 0)],
                        [(u'Banks', 0), (u'Banco do Brasil', 0)],
                        [(u'Banks', 0), (u'Banco do Brasil', 0)],
                        [(u'Banks', 0), (u'Banco do Brasil', 0)],
                        [(u'Banks', 0), (u'Banco do Brasil', 0)],
                        [(u'Banks', 0), (u'Banco do Brasil', 0)]],
             u'Expenses': [[(u'Expenses', 0),
                            (u'Aluguel', currency("850")),
                            (u'Luz', currency("120.18")),
                            (u'Sal\xe1rios', currency("4692.76")),
                            (u'Telefonia', currency("232.30")),
                            (u'Impostos', currency("6843.91"))],
                           [(u'Expenses', 0),
                            (u'Aluguel', currency("850")),
                            (u'Luz', currency("138.48")),
                            (u'Sal\xe1rios', currency("4502.48")),
                            (u'Telefonia', 0),
                            (u'Impostos', currency("2834.39"))],
                           [(u'Expenses', 0),
                            (u'Aluguel', 0),
                            (u'Luz', 0),
                            (u'Sal\xe1rios', 0),
                            (u'Telefonia', 0),
                            (u'Impostos', 0)],
                           [(u'Expenses', 0),
                            (u'Aluguel', 0),
                            (u'Luz', 0),
                            (u'Sal\xe1rios', 0),
                            (u'Telefonia', 0),
                            (u'Impostos', 0)],
                           [(u'Expenses', 0),
                            (u'Aluguel', 0),
                            (u'Luz', 0),
                            (u'Sal\xe1rios', 0),
                            (u'Telefonia', 0),
                            (u'Impostos', 0)],
                           [(u'Expenses', 0),
                            (u'Aluguel', 0),
                            (u'Luz', 0),
                            (u'Sal\xe1rios', 0),
                            (u'Telefonia', 0),
                            (u'Impostos', 0)],
                           [(u'Expenses', 0),
                            (u'Aluguel', 0),
                            (u'Luz', 0),
                            (u'Sal\xe1rios', 0),
                            (u'Telefonia', 0),
                            (u'Impostos', 0)],
                           [(u'Expenses', 0),
                            (u'Aluguel', 0),
                            (u'Luz', 0),
                            (u'Sal\xe1rios', 0),
                            (u'Telefonia', 0),
                            (u'Impostos', 0)],
                           [(u'Expenses', 0),
                            (u'Aluguel', 0),
                            (u'Luz', 0),
                            (u'Sal\xe1rios', 0),
                            (u'Telefonia', 0),
                            (u'Impostos', 0)],
                           [(u'Expenses', 0),
                            (u'Aluguel', 0),
                            (u'Luz', 0),
                            (u'Sal\xe1rios', 0),
                            (u'Telefonia', 0),
                            (u'Impostos', 0)],
                           [(u'Expenses', 0),
                            (u'Aluguel', 0),
                            (u'Luz', 0),
                            (u'Sal\xe1rios', 0),
                            (u'Telefonia', 0),
                            (u'Impostos', 0)],
                           [(u'Expenses', 0),
                            (u'Aluguel', 0),
                            (u'Luz', 0),
                            (u'Sal\xe1rios', 0),
                            (u'Telefonia', 0),
                            (u'Impostos', 0)]],
             u'Income': [[(u'Income', currency("45752.82"))],
                         [(u'Income', 0)],
                         [(u'Income', 0)],
                         [(u'Income', 0)],
                         [(u'Income', 0)],
                         [(u'Income', 0)],
                         [(u'Income', 0)],
                         [(u'Income', 0)],
                         [(u'Income', 0)],
                         [(u'Income', 0)],
                         [(u'Income', 0)],
                         [(u'Income', 0)]],
             }
            )
