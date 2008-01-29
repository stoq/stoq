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
## Author(s):     George Kussumoto   <george@async.com.br>
##
##
""" Test for lib/validators.py module. """

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.validators import validate_cpf, validate_cnpj

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
