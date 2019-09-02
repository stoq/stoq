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
#  Author(s): Stoq Team <stoq-devel@async.com.br>

import datetime
import jwt
from jwt.exceptions import DecodeError, ExpiredSignatureError
import logging
from storm.references import Reference
from typing import Dict

from stoqlib.api import api
from stoqlib.database.properties import UnicodeCol, IdCol, BoolCol, DateTimeCol
from stoqlib.domain.base import Domain
from stoqlib.domain.person import LoginUser
from stoqlib.domain.station import BranchStation


log = logging.getLogger(__name__)


class AccessToken(Domain):
    """Represents single access that is done by a user in a particular branch station"""
    __storm_table__ = 'access_token'

    STATUS_VALID = 'valid'
    STATUS_INVALID = 'invalid'
    STATUS_REVOKED = 'revoked'
    STATUS_EXPIRED = 'expired'

    #: the token that can be used to grant access to some resources
    token = UnicodeCol()

    #: date the token was generated
    issue_date = DateTimeCol()

    #: if the token is unusable
    revoked = BoolCol(default=False)

    #: the |login_user| for which the token was generated
    user_id = IdCol()
    user = Reference(user_id, 'LoginUser.id')

    #: the |branch_station| at which the access was made
    station_id = IdCol()
    station = Reference(station_id, 'BranchStation.id')

    # this constructor will only accept keyword arguments
    def __init__(self, *, user, payload=None, issue_date=None, exp_timedelta=None, **kwargs):
        secret = api.sysparam.get_string('USER_HASH')
        payload = payload or {}
        issue_date = issue_date or datetime.datetime.utcnow()

        payload['iss'] = 'Stoq Tecnologia'
        payload['iat'] = issue_date
        payload['sub'] = user.username
        if exp_timedelta:
            payload['exp'] = issue_date + exp_timedelta

        token = jwt.encode(payload, secret, algorithm='HS256').decode()

        super().__init__(token=token, issue_date=issue_date, user=user, **kwargs)

    #
    # Properties
    #

    @property
    def payload(self) -> Dict[str, str]:
        secret = api.sysparam.get_string('USER_HASH')
        return jwt.decode(self.token, secret, algorithms=['HS256'], leeway=10)

    @property
    def status(self) -> str:
        if self.revoked:
            return self.STATUS_REVOKED
        try:
            self.payload
        except ExpiredSignatureError:
            return self.STATUS_EXPIRED
        except DecodeError:
            return self.STATUS_INVALID

        return self.STATUS_VALID

    #
    # Classmethods
    #

    @classmethod
    def get_or_create(cls, store, user: LoginUser, station: BranchStation,
                      exp_timedelta: datetime.timedelta=None) -> 'AccessToken':
        """Creates or retrieves an AccessToken with the specified parameters."""
        access_token = store.find(cls, user=user,
                                  station=station, revoked=False).order_by(cls.te_id).last()

        if not access_token:
            payload = {
                'user_id': user.id,
                'station_id': station.id,
            }
            access_token = AccessToken(
                store=store,
                payload=payload,
                exp_timedelta=exp_timedelta,
                user=user,
                station=station
            )

        return access_token

    @classmethod
    def get_by_token(cls, store, token: str) -> 'AccessToken':
        """Returns the instance of AccessToken that contains a particular token."""
        return store.find(cls, token=token).one()

    #
    #  Public API
    #

    def revoke(self):
        self.revoked = True

    def is_valid(self):
        return self.status == AccessToken.STATUS_VALID
