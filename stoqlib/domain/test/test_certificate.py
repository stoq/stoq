# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2017 Async Open Source <http://www.async.com.br>
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


from stoqlib.domain.certificate import Certificate, PasswordObfuscator
from stoqlib.domain.test.domaintest import DomainTest


class TestCertificate(DomainTest):

    def test_type_str(self):
        cert = Certificate()
        cert.type = Certificate.TYPE_PKCS12
        self.assertEqual(cert.type_str, "A1: Digital certificate")

    def test_password(self):
        cert = Certificate()
        po = PasswordObfuscator()
        po.password = u'123456'
        cert.password = po
        self.assertEqual(cert._password, po.hashed_password)
        self.assertEqual(cert.password.password, u'123456')

    def test_get_active_certs(self):
        cert1 = Certificate(store=self.store, active=True)
        cert2 = Certificate(store=self.store, active=True)
        active_certs = Certificate.get_active_certs(self.store, exclude=cert2)
        self.assertEqual(active_certs.count(), 1)
        self.assertEqual(active_certs.one(), cert1)
