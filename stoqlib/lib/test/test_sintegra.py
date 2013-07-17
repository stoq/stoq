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

from decimal import Decimal
import os

from dateutil.relativedelta import relativedelta

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.devices import FiscalDayHistory, FiscalDayTax
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.dateutils import localdate, localdatetime
from stoqlib.lib.diffutils import diff_files
from stoqlib.lib.sintegra import SintegraFile
from stoqlib.lib.unittestutils import get_tests_datadir


def compare_sintegra_file(sfile, basename):
    expected = basename + '-expected.txt'
    output = basename + '-output.txt'

    sfile.write(output)
    expected = get_tests_datadir(expected)
    diff = diff_files(expected, output)
    os.unlink(output)
    if diff:
        raise AssertionError('%s\n%s' % ("Files differ, output:", diff))


class SintegraTest(DomainTest):
    def test_complete(self):
        station = self.create_station()
        today = localdate(2007, 1, 1)
        reduction_date = localdatetime(2007, 1, 1, 23, 59)
        day = FiscalDayHistory(store=self.store,
                               emission_date=today,
                               station=station,
                               serial=u'Stoqlib test serial',
                               serial_id=1,
                               coupon_start=1,
                               coupon_end=23,
                               crz=18,
                               cro=25,
                               period_total=Decimal("456.00"),
                               total=Decimal("123141.00"),
                               reduction_date=reduction_date)
        for code, value, type in [(u'2500', Decimal("123.00"), u'ICMS'),
                                  (u'F', Decimal("789.00"), u'ICMS')]:
            FiscalDayTax(fiscal_day_history=day, code=code, value=value, type=type,
                         store=self.store)

        branch = get_current_branch(self.store)
        user = self.create_employee()
        branch.manager = user
        manager = branch.manager.person
        company = branch.person.company
        address = branch.person.get_main_address()

        start = today + relativedelta(day=1)
        end = today + relativedelta(day=31)

        s = SintegraFile()
        s.add_header(company.get_cnpj_number(),
                     u'110042490114',
                     branch.get_description(),
                     address.get_city(),
                     address.get_state(),
                     branch.person.get_fax_number_number(),
                     start, end)
        # if we don't a street number, use zero for sintegra
        s.add_complement_header(address.street, address.streetnumber or 0,
                                address.complement,
                                address.district,
                                address.get_postal_code_number(),
                                manager.name,
                                branch.person.get_phone_number_number())

        for item in self.store.find(FiscalDayHistory):
            s.add_fiscal_coupon(
                item.emission_date, item.serial, item.serial_id,
                item.coupon_start, item.coupon_end,
                item.cro, item.crz, item.period_total, item.total)
            for tax in item.taxes:
                s.add_fiscal_tax(item.emission_date, item.serial,
                                 tax.code, tax.value)
        s.close()

        try:
            compare_sintegra_file(s, 'sintegra')
        except AssertionError as e:
            self.fail(e)
