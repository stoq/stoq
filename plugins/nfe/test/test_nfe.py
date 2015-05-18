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

from kiwi.python import strip_accents
from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.address import Address, CityLocation
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.person import Client, Individual
from stoqlib.domain.product import Storable, StockTransactionHistory
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.exceptions import ModelDataError
from stoqlib.lib.diffutils import diff_files
from stoqlib.lib.unittestutils import get_tests_datadir

from nfe.nfegenerator import NFeGenerator, NFeIdentification


class TestNfeGenerator(DomainTest):
    def _test_generated_files(self, new_client=None):
        due_date = datetime.datetime(2011, 10, 24, 0, 0, 0, 0)
        sale = self._create_sale(1666, due_date=due_date)
        sale.identifier = 1234
        if new_client:
            sale.client = new_client
        for p in sale.payments:
            p.identifier = 4321
        generator = NFeGenerator(sale, self.store)

        # If we generate random cnf, the test will always fail
        _get_random_cnf = NFeIdentification._get_random_cnf
        NFeIdentification._get_random_cnf = lambda s: 10000001
        # Mimic now_datetime behavior
        _get_now_datetime = NFeGenerator._get_now_datetime
        NFeGenerator._get_now_datetime = lambda s: due_date

        generator.generate()
        NFeIdentification._get_random_cnf = _get_random_cnf
        NFeGenerator._get_now_datetime = _get_now_datetime

        basedir = get_tests_datadir('plugins')

        if new_client is None:
            expected = os.path.join(basedir, "nfe-expected.txt")
        elif isinstance(sale.get_client_role(), Individual):
            expected = os.path.join(basedir, "individual-nfe-expected.txt")
        else:
            expected = os.path.join(basedir, "company-nfe-expected.txt")

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

    # Individual recipient(with CPF)
    def test_generated_file_with_individual(self):
        individual = self.create_individual()
        individual.cpf = u'123.123.123-23'
        client = Client(person=individual.person, store=self.store)
        self._create_address(individual.person,
                             street=u"Rua dos Tomates",
                             streetnumber=2666,
                             postal_code=u'87654-321')
        self._test_generated_files(client)

    # Company recipient(with CNPJ)
    def test_generated_file_with_company(self):
        company = self.create_company()
        company.cnpj = u'123.456.789/1234-00'
        client = Client(person=company.person, store=self.store)
        self._create_address(company.person,
                             street=u"Rua dos Tomates",
                             streetnumber=2666,
                             postal_code=u'87654-321')

        self._test_generated_files(client)

    def test_generated_files_without_document(self):
        self._test_generated_files()

    def test_invalid_cnpj(self):
        sale = self._create_sale(2666)
        company = sale.branch.person.company
        company.cnpj = u'123.321.678/4567-90'

        generator = NFeGenerator(sale, self.store)
        generator.sale_id = 2345
        generator.payment_ids = [5432]
        self.assertRaises(ModelDataError, generator.generate)

    def _create_sale(self, invoice_number, due_date=None):
        sale = self.create_sale()
        sale.invoice_number = invoice_number
        sale.branch = get_current_branch(self.store)

        # [0] - Description
        # [1] - Code
        # [2] - Price
        # [3] - Quantity
        # [4] - Base price
        for data in [(u"Laranja", u"1", Decimal(1), Decimal(10), Decimal('1.5')),
                     (u"Limão", u"2", Decimal('0.5'), Decimal(15), Decimal('0.3')),
                     (u"Abacaxi", u"3", Decimal(3), Decimal(1), Decimal('3.3')),
                     (u"Cenoura", u"4", Decimal('1.5'), Decimal(6), Decimal('1.9')),
                     (u"Pêssego", u"5", Decimal('3.5'), Decimal(3), Decimal('3.0'))]:
            sellable = self._create_sellable(data[0], data[1], data[2])

            storable = Storable(product=sellable.product,
                                store=self.store)
            storable.increase_stock(data[3], get_current_branch(self.store),
                                    StockTransactionHistory.TYPE_INITIAL,
                                    sale.id)

            sale_item = sale.add_sellable(sellable, data[3])
            # Set the base price to test the discount in NF-e.
            sale_item.base_price = data[4]
            icms_info = sale_item.icms_info
            icms_info.csosn = 201
            icms_info.p_icms_st = 1
            icms_info.update_values(sale_item)

        sale.client = self.create_client()
        self._create_address(sale.client.person,
                             street=u"Rua dos Tomates",
                             streetnumber=2666,
                             postal_code=u'87654-321')
        sale.order()

        method = PaymentMethod.get_by_name(self.store, u'money')
        method.create_payment(Payment.TYPE_IN, sale.group, sale.branch,
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
        city = CityLocation.get_default(self.store)

        return Address(store=self.store,
                       street=street,
                       streetnumber=streetnumber,
                       postal_code=postal_code,
                       is_main_address=True,
                       person=person,
                       city_location=city)
