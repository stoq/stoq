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
from stoqlib.lib.validators import (validate_cpf, validate_cnpj,
                                    validate_area_code, validate_int,
                                    validate_decimal, validate_directory,
                                    validate_percentage, validate_cfop)


class TestValidators(DomainTest):

    def testValidateCPF(self):
        self.failUnless(validate_cpf('95524361503'))
        self.failUnless(validate_cpf('955.243.615-03'))
        self.failUnless(validate_cpf(' 9 5 5 2 4 3 6 1 5 0 3 '))

        self.failIf(validate_cpf('invalid cpf'))
        self.failIf(validate_cpf('42'))
        self.failIf(validate_cpf(''))
        self.failIf(validate_cpf(None))
        self.failIf(validate_cpf('15948726375'))

    def testValidateCNPJ(self):
        self.failUnless(validate_cnpj('11222333000181'))
        self.failUnless(validate_cnpj('11.222.333/0001-81'))
        self.failUnless(validate_cnpj(' 1 1 2 2 2 3 3 3 0 0 0 1 8 1 '))

        self.failIf(validate_cnpj(' invalid cnpj'))
        self.failIf(validate_cnpj('42'))
        self.failIf(validate_cnpj(''))
        self.failIf(validate_cnpj(None))
        self.failIf(validate_cnpj('1594872637500'))

    def testValidateCFOP(self):
        self.failUnless(validate_cfop('1.123'))
        self.failUnless(validate_cfop(u'1.123'))

        self.failIf(validate_cfop(None))
        self.failIf(validate_cfop(''))
        self.failIf(validate_cfop(' '))
        self.failIf(validate_cfop('1234'))
        self.failIf(validate_cfop('12345'))
        self.failIf(validate_cfop('12.34'))
        self.failIf(validate_cfop('.12345'))
        self.failIf(validate_cfop('1.2345'))
        self.failIf(validate_cfop('12.345'))
        self.failIf(validate_cfop('123.45'))
        self.failIf(validate_cfop('1234.5'))
        self.failIf(validate_cfop('12345.'))
        self.failIf(validate_cfop(1234))
        self.failIf(validate_cfop(12345))
        self.failIf(validate_cfop(1.234))

    def testValidateAreaCode(self):
        self.failUnless(validate_area_code(10))
        self.failUnless(validate_area_code(99))
        self.failUnless(validate_area_code('10'))
        self.failUnless(validate_area_code('99'))

        self.failIf(validate_area_code(9))
        self.failIf(validate_area_code(100))
        self.failIf(validate_area_code('9'))
        self.failIf(validate_area_code('100'))

    def testValidateInt(self):
        self.failUnless(validate_int(0))
        self.failUnless(validate_int(10))
        self.failUnless(validate_int(-10))
        self.failUnless(validate_int('0'))
        self.failUnless(validate_int('10'))
        self.failUnless(validate_int('-10'))

        self.failIf(validate_int(0.0))
        self.failIf(validate_int(10.5))
        self.failIf(validate_int('0.0'))
        self.failIf(validate_int('10.5'))
        self.failIf(validate_int('string'))

    def testValidateDecimal(self):
        self.failUnless(validate_decimal(Decimal('0')))
        self.failUnless(validate_decimal(Decimal('10')))
        self.failUnless(validate_decimal(Decimal('-10')))
        self.failUnless(validate_decimal(Decimal('10.5')))
        self.failUnless(validate_decimal('0'))
        self.failUnless(validate_decimal('10'))
        self.failUnless(validate_decimal('-10'))
        self.failUnless(validate_decimal('10.5'))

        self.failIf(validate_decimal(0))
        self.failIf(validate_decimal(10))
        self.failIf(validate_decimal(-10))
        self.failIf(validate_decimal(10.5))
        self.failIf(validate_decimal('string'))

    def testValidateDirectory(self):
        self.failUnless(validate_directory("/home"))
        self.failUnless(validate_directory("~"))

        self.failIf(validate_int("~/SomeFolderNoOneWouldHabe"))
        self.failIf(validate_int("/SomeFolderSystemDoesntHave"))

    def testValidatePercentage(self):
        self.failUnless(validate_percentage(0))
        self.failUnless(validate_percentage(10))
        self.failUnless(validate_percentage(100))
        self.failUnless(validate_percentage(50.5))
        self.failUnless(validate_percentage(Decimal('0')))
        self.failUnless(validate_percentage(Decimal('10')))
        self.failUnless(validate_percentage(Decimal('100')))
        self.failUnless(validate_percentage(Decimal('50.5')))
        self.failUnless(validate_percentage('0'))
        self.failUnless(validate_percentage('10'))
        self.failUnless(validate_percentage('100'))
        self.failUnless(validate_percentage('50.5'))

        self.failIf(validate_percentage(-1))
        self.failIf(validate_percentage(101))
        self.failIf(validate_percentage(Decimal('-1')))
        self.failIf(validate_percentage(Decimal('101')))
        self.failIf(validate_percentage('-1'))
        self.failIf(validate_percentage('101'))
        self.failIf(validate_percentage('50%'))
