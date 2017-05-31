# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2017 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import collections

from storm.expr import And, Eq

from stoqlib.database.properties import EnumCol, BLOBCol, UnicodeCol, BoolCol
from stoqlib.domain.base import Domain
from stoqlib.lib.algorithms import PasswordObfuscator
from stoqlib.lib.translation import stoqlib_gettext as _


class Certificate(Domain):
    __storm_table__ = 'certificate'

    TYPE_PKCS11 = u'pkcs11'
    TYPE_PKCS12 = u'pkcs12'

    types_str = collections.OrderedDict([
        (TYPE_PKCS11, _("A3: Smartcard")),
        (TYPE_PKCS12, _("A1: Digital certificate")),
    ])

    #: The type of the certificate
    type = EnumCol(allow_none=False, default=TYPE_PKCS12)

    #: If the certificate is active or not
    active = BoolCol(default=True)

    #: The name of the certificate/lib when it was uploaded to the dataabse
    name = UnicodeCol(default=u'')

    #: The content of the certificate. The library file for PKCS11
    #: or the certificate itself for PKCS12
    content = BLOBCol()

    #: The certificate password. If it is ``None`` it means that the user
    #: should be asked each time it is going to be used (for PKCS11 only)
    _password = BLOBCol(name='password', allow_none=True, default=None)

    @property
    def password(self):
        po = PasswordObfuscator()
        po.hashed_password = self._password and self._password
        return po

    @password.setter
    def password(self, password):
        assert isinstance(password, PasswordObfuscator)
        hashed = password.hashed_password
        self._password = hashed

    @property
    def type_str(self):
        return self.types_str[self.type]

    @classmethod
    def get_active_certs(cls, store, exclude=None):
        """Get active certificates except the one given in exclude parameter"""
        except_id = exclude and exclude.id
        return store.find(cls, And(Eq(cls.active, True), cls.id != except_id))
