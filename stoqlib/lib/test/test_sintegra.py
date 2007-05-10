# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##

from cStringIO import StringIO
import datetime
from decimal import Decimal
import os

from dateutil.relativedelta import relativedelta

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.devices import FiscalDayHistory, FiscalDayTax
from stoqlib.domain.interfaces import ICompany
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.sintegra import SintegraFile
from stoqlib.lib.diffutils import diff_files
from stoqlib.lib import test

class SintegraTest(DomainTest):
    def testComplete(self):
        settings = self.create_device_settings()
        today = datetime.date(2007, 1, 1)
        day = FiscalDayHistory(connection=self.trans,
                               emission_date=today,
                               device=settings,
                               serial='Stoqlib test serial',
                               serial_id=1,
                               coupon_start=1,
                               coupon_end=23,
                               crz=18,
                               cro=25,
                               period_total=Decimal("456.00"),
                               total=Decimal("123141.00"))
        for code, value in [('2500', Decimal("123.00")),
                            ('F', Decimal("789.00"))]:
            FiscalDayTax(fiscal_day_history=day, code=code, value=value,
                         connection=self.trans)

        branch = get_current_branch(self.trans)
        company = ICompany(branch.person)
        address = branch.person.get_main_address()

        start = today + relativedelta(day=1)
        end = today + relativedelta(day=31)

        s = SintegraFile()
        s.add_header(company.get_cnpj_number(),
                     '110042490114',
                     company.fancy_name,
                     address.get_city(),
                     address.get_state(),
                     branch.person.get_fax_number_number(),
                     start, end)
        s.add_complement_header(address.street, address.number,
                                address.complement,
                                address.district,
                                address.get_postal_code_number(),
                                company.fancy_name,
                                branch.person.get_phone_number_number())

        for item in FiscalDayHistory.select(connection=self.trans):
            s.add_fiscal_coupon(
                item.emission_date, item.serial, item.serial_id,
                item.coupon_start, item.coupon_end,
                item.cro, item.crz, item.period_total, item.total)
            for tax in item.taxes:
                s.add_fiscal_tax(item.emission_date, item.serial,
                                 tax.code, tax.value)
        s.close()

        fp = StringIO()
        s.write('sintegra-output.txt')
        expected = os.path.join(test.__path__[0], 'sintegra-expected.txt')
        retval = diff_files('sintegra-output.txt', expected)
        os.unlink('sintegra-output.txt')
        if retval:
            raise AssertionError("Files differ, check output above")
