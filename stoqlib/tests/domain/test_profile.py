# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s): Rudá Porto Filgueiras  <rudazz@gmail.com>
##
""" This module tests all classes in stoq/domain/profile.py"""

from stoqlib.domain.profile import UserProfile, ProfileSettings
from stoqlib.domain.profile import update_profile_applications
from stoqlib.lib.runtime import get_application_names
from stoqlib.tests.domain.base import BaseDomainTest


class TestUserProfile(BaseDomainTest):
    """
    C{UserProfile} TestCase
    """
    _table = UserProfile


class TestProfileSettings(BaseDomainTest):
    """
    C{ProfileSettings} TestCase
    """
    _table = ProfileSettings
    foreign_key_attrs = {'user_profile': TestUserProfile}

    def test_update_profile_applications(self):
        profile = UserProfile(connection=self.conn, name='assistant')

        profile.add_application_reference('warehouse',
                                          has_permission=True)
        items = profile.profile_settings
        assert len(items) == 1

        new_profile = UserProfile(connection=self.conn, name='assistant')
        update_profile_applications(self.conn, new_profile)
        items = new_profile.profile_settings
        assert len(items) == len(get_application_names())

    def test_create_profile_template(self):
        profile_name = 'Boss'
        table = UserProfile
        self.boss_profile = table.create_profile_template(self.conn,
                                                          profile_name,
                                                          has_full_permission=
                                                          True)
        items = self.boss_profile.profile_settings
        assert len(items) == len(get_application_names())

    def test_check_app_permission(self):
        profile = UserProfile(connection=self.conn, name='boss')
        profile.add_application_reference('test_application', True)
        assert profile.check_app_permission('test_application') == True
