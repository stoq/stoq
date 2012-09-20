# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

"""NF-e tests"""

import datetime
from decimal import Decimal
import os
import sys

from kiwi.python import strip_accents

import stoqlib
from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.address import Address, CityLocation
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.product import Storable
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.exceptions import ModelDataError
from stoqlib.lib import test
from stoqlib.lib.diffutils import diff_files

# This test should be inside plugins/nfe, but it's not reachable there
sys.path.append(os.path.join(os.path.dirname(stoqlib.__file__), '..',
    'plugins', 'nfe'))
from nfegenerator import NFeGenerator, NFeIdentification


class TestNfeGenerator(DomainTest):
    def test_generated_files(self):
        due_date = datetime.datetime(2011, 10, 24)
        sale = self._create_sale(1666, due_date=due_date)
        generator = NFeGenerator(sale, self.trans)

        # If we generate random cnf, the test will always fail
        _get_random_cnf = NFeIdentification._get_random_cnf
        NFeIdentification._get_random_cnf = lambda s: 10000001
        # Mimic today behavior
        _get_today_date = NFeGenerator._get_today_date
        NFeGenerator._get_today_date = lambda s: due_date

        generator.sale_id = 1234
        generator.payment_ids = [4321]
        generator.generate()
        NFeIdentification._get_random_cnf = _get_random_cnf
        NFeGenerator._get_today_date = _get_today_date

        basedir = test.__path__[0]
        expected = os.path.join(basedir, "nfe-expected.txt")
        output = os.path.join(basedir, "nfe-output.txt")
        if not os.path.isfile(expected):
            with open(expected, 'wb') as fp:
                fp.write(strip_accents(generator._as_txt()))
            return
        with open(output, 'wb') as fp:
            fp.write(strip_accents(generator._as_txt()))

        # Diff and compare
        diff = diff_files(expected, output)
        os.unlink(output)

        self.failIf(diff, '%s\n%s' % ("Files differ, output:", diff))

    def test_invalid_cnpj(self):
        sale = self._create_sale(2666)
        company = sale.branch.person.company
        company.cnpj = '123.321.678/4567-90'

        generator = NFeGenerator(sale, self.trans)
        generator.sale_id = 2345
        generator.payment_ids = [5432]
        self.assertRaises(ModelDataError, generator.generate)

    def _create_sale(self, invoice_number, due_date=None):
        sale = self.create_sale()
        sale.invoice_number = invoice_number
        sale.branch = get_current_branch(self.trans)

        # [0] - Description
        # [1] - Code
        # [2] - Price
        # [3] - Quantity
        for data in [("Laranja", "1", Decimal(1), Decimal(10)),
                     ("Limão", "2", Decimal('0.5'), Decimal(15)),
                     ("Abacaxi", "3", Decimal(3), Decimal(1)),
                     ("Cenoura", "4", Decimal('1.5'), Decimal(6)),
                     ("Pêssego", "5", Decimal('3.5'), Decimal(3))]:
            sellable = self._create_sellable(data[0], data[1], data[2])

            storable = Storable(product=sellable.product,
                                connection=self.trans)
            storable.increase_stock(data[3], get_current_branch(self.trans))

            sale.add_sellable(sellable, data[3])

        sale.client = self.create_client()
        self._create_address(sale.client.person,
                             street="Rua dos Tomates",
                             streetnumber=2666,
                             postal_code='87654-321')
        sale.order()

        method = PaymentMethod.get_by_name(self.trans, 'money')
        method.create_inpayment(sale.group, sale.branch,
                                sale.get_sale_subtotal(),
                                due_date=due_date)
        sale.confirm()

        return sale

    def _create_sellable(self, desc, code, price):
        sellable = self.create_sellable(price=price)

        sellable.code = code
        sellable.description = desc

        return sellable

    def _create_address(self, person, street, streetnumber, postal_code):
        city = CityLocation.get_default(self.trans)

        return Address(connection=self.trans,
                       street=street,
                       streetnumber=streetnumber,
                       postal_code=postal_code,
                       is_main_address=True,
                       person=person,
                       city_location=city)
