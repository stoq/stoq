# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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
##
""" Test for lib/validators.py module. """

from decimal import Decimal

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.validators import (validate_cpf, validate_cnpj,
                                    validate_area_code, validate_int,
                                    validate_decimal, validate_directory,
                                    validate_percentage, validate_cfop,
                                    validate_phone_number, validate_invoice_key,
                                    is_date_in_interval, validate_cst)


class TestValidators(DomainTest):

    def test_validate_phone_number(self):
        for phone_number in [
                # 7 digits number
                '1234567', '123-4567', '123 4567',
                # 7 digits number with area code
                '161234567', '(16) 1234-567',
                # 7 digits number with area code and leading 0
                '0161234567', '(16) 1234-567', '(016) 1234-567',
                # 8 digits number
                '12345678', '1234-5678', '1234 5678',
                # 8 digits number with area code
                '1612345678', '(16) 1234-5678',
                # 8 digits number with area code and leading 0
                '01612345678', '(016) 12345678', '(016) 1234-5678',
                # 9 digits number
                '912345678', '9123 45678', '9123-45678',
                # 9 digits number with area code
                '16912345678', '(16) 9123-45678',
                # 9 digits number with area code and leading 0
                '016912345678', '(016) 912345678', '(016) 91234-5678']:
            self.assertTrue(validate_phone_number(phone_number),
                            msg="%s did not pass" % (phone_number, ))

        for phone_number in ['123456', '(16) 1234', '161234567890']:
            self.assertFalse(validate_phone_number(phone_number),
                             msg="%s did pass while it shouldn't" % (phone_number, ))

    def test_validate_c_p_f(self):
        self.assertTrue(validate_cpf('95524361503'))
        self.assertTrue(validate_cpf('955.243.615-03'))
        self.assertTrue(validate_cpf(' 9 5 5 2 4 3 6 1 5 0 3 '))

        self.assertFalse(validate_cpf('invalid cpf'))
        self.assertFalse(validate_cpf('42'))
        self.assertFalse(validate_cpf(''))
        self.assertFalse(validate_cpf(None))
        self.assertFalse(validate_cpf('15948726375'))
        # A number with more than 11 digits. Ex: a CNPJ
        self.assertFalse(validate_cpf('45.997.418/0001-53'))

    def test_validate_c_n_p_j(self):
        self.assertTrue(validate_cnpj('11222333000181'))
        self.assertTrue(validate_cnpj('11.222.333/0001-81'))
        self.assertTrue(validate_cnpj(' 1 1 2 2 2 3 3 3 0 0 0 1 8 1 '))

        self.assertFalse(validate_cnpj(' invalid cnpj'))
        self.assertFalse(validate_cnpj('42'))
        self.assertFalse(validate_cnpj(''))
        self.assertFalse(validate_cnpj(None))
        self.assertFalse(validate_cnpj('1594872637500'))

    def test_validate_c_f_o_p(self):
        self.assertTrue(validate_cfop('1.123'))
        self.assertTrue(validate_cfop(u'1.123'))

        self.assertFalse(validate_cfop(None))
        self.assertFalse(validate_cfop(''))
        self.assertFalse(validate_cfop(' '))
        self.assertFalse(validate_cfop('1234'))
        self.assertFalse(validate_cfop('12345'))
        self.assertFalse(validate_cfop('12.34'))
        self.assertFalse(validate_cfop('.12345'))
        self.assertFalse(validate_cfop('1.2345'))
        self.assertFalse(validate_cfop('12.345'))
        self.assertFalse(validate_cfop('123.45'))
        self.assertFalse(validate_cfop('1234.5'))
        self.assertFalse(validate_cfop('12345.'))
        self.assertFalse(validate_cfop(1234))
        self.assertFalse(validate_cfop(12345))
        self.assertFalse(validate_cfop(1.234))

    def test_validate_area_code(self):
        self.assertTrue(validate_area_code(10))
        self.assertTrue(validate_area_code(99))
        self.assertTrue(validate_area_code('10'))
        self.assertTrue(validate_area_code('99'))

        self.assertFalse(validate_area_code(9))
        self.assertFalse(validate_area_code(100))
        self.assertFalse(validate_area_code('9'))
        self.assertFalse(validate_area_code('100'))

    def test_validate_int(self):
        self.assertTrue(validate_int(0))
        self.assertTrue(validate_int(10))
        self.assertTrue(validate_int(-10))
        self.assertTrue(validate_int('0'))
        self.assertTrue(validate_int('10'))
        self.assertTrue(validate_int('-10'))

        self.assertFalse(validate_int(0.0))
        self.assertFalse(validate_int(10.5))
        self.assertFalse(validate_int('0.0'))
        self.assertFalse(validate_int('10.5'))
        self.assertFalse(validate_int('string'))

    def test_validate_decimal(self):
        self.assertTrue(validate_decimal(Decimal('0')))
        self.assertTrue(validate_decimal(Decimal('10')))
        self.assertTrue(validate_decimal(Decimal('-10')))
        self.assertTrue(validate_decimal(Decimal('10.5')))
        self.assertTrue(validate_decimal('0'))
        self.assertTrue(validate_decimal('10'))
        self.assertTrue(validate_decimal('-10'))
        self.assertTrue(validate_decimal('10.5'))

        self.assertFalse(validate_decimal(0))
        self.assertFalse(validate_decimal(10))
        self.assertFalse(validate_decimal(-10))
        self.assertFalse(validate_decimal(10.5))
        self.assertFalse(validate_decimal('string'))

    def test_validate_directory(self):
        self.assertTrue(validate_directory("/home"))
        self.assertTrue(validate_directory("~"))

        self.assertFalse(validate_int("~/SomeFolderNoOneWouldHabe"))
        self.assertFalse(validate_int("/SomeFolderSystemDoesntHave"))

    def test_validate_percentage(self):
        self.assertTrue(validate_percentage(0))
        self.assertTrue(validate_percentage(10))
        self.assertTrue(validate_percentage(100))
        self.assertTrue(validate_percentage(50.5))
        self.assertTrue(validate_percentage(Decimal('0')))
        self.assertTrue(validate_percentage(Decimal('10')))
        self.assertTrue(validate_percentage(Decimal('100')))
        self.assertTrue(validate_percentage(Decimal('50.5')))
        self.assertTrue(validate_percentage('0'))
        self.assertTrue(validate_percentage('10'))
        self.assertTrue(validate_percentage('100'))
        self.assertTrue(validate_percentage('50.5'))

        self.assertFalse(validate_percentage(-1))
        self.assertFalse(validate_percentage(101))
        self.assertFalse(validate_percentage(Decimal('-1')))
        self.assertFalse(validate_percentage(Decimal('101')))
        self.assertFalse(validate_percentage('-1'))
        self.assertFalse(validate_percentage('101'))
        self.assertFalse(validate_percentage('50%'))

    def test_validate_invoice_key(self):
        self.assertFalse(validate_invoice_key('3' * 43))
        self.assertFalse(validate_invoice_key('3' * 44))
        self.assertTrue(validate_invoice_key(
            '43161103852995000107650010000001821299676414'))

    def test_is_date_in_empty_interval(self):
        assert is_date_in_interval(localtoday(), None, None) is False

    def test_validate_cst(self):
        self.assertFalse(validate_cst(80))
        self.assertTrue(validate_cst(9))
