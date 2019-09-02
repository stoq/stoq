# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

#
# Copyright (C) 2019 Stoq Tecnologia <https://stoq.com.br/>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
# Author(s): Stoq Team <stoq-devel@async.com.br>
#
""" This module test all classes in stoqlib/domain/token.py """

from jwt.exceptions import DecodeError, ExpiredSignatureError
import mock

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.token import AccessToken


class TestToken(DomainTest):

    def test_status(self):
        access_token = self.create_access_token()

        self.assertEqual(access_token.status, AccessToken.STATUS_VALID)

        with mock.patch('stoqlib.domain.token.jwt.decode') as jwt_decode:
            jwt_decode.side_effect = ExpiredSignatureError
            self.assertEqual(access_token.status, AccessToken.STATUS_EXPIRED)

            jwt_decode.side_effect = DecodeError
            self.assertEqual(access_token.status, AccessToken.STATUS_INVALID)

        access_token.revoke()
        self.assertEqual(access_token.status, AccessToken.STATUS_REVOKED)

    def test_get_or_create(self):
        user = self.create_user()
        station = self.create_station()
        first_access_token = AccessToken.get_or_create(store=self.store, user=user, station=station)
        sec_access_token = AccessToken.get_or_create(store=self.store, user=user, station=station)

        self.assertEqual(first_access_token.id, sec_access_token.id)

    def test_get_by_token(self):
        token_created = self.create_access_token()
        token_found = AccessToken.get_by_token(self.store, token_created.token)

        self.assertEqual(token_created.id, token_found.id)

    def test_revoke(self):
        access_token = self.create_access_token()
        access_token.revoke()

        self.assertEqual(access_token.status, AccessToken.STATUS_REVOKED)

    def test_is_valid(self):
        access_token = self.create_access_token()
        self.assertTrue(access_token.is_valid())

        with mock.patch('stoqlib.domain.token.jwt.decode') as jwt_decode:
            jwt_decode.side_effect = ExpiredSignatureError
            self.assertFalse(access_token.is_valid())

            jwt_decode.side_effect = DecodeError
            self.assertFalse(access_token.is_valid())

        access_token.revoke()
        self.assertFalse(access_token.is_valid())
