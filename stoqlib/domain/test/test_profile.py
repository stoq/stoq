# -*- coding: utf-8 -*-
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" This module tests all classes in stoq/domain/profile.py"""

from stoqlib.domain.profile import UserProfile
from stoqlib.domain.profile import ProfileSettings
from stoqlib.domain.profile import update_profile_applications
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class TestUserProfile(DomainTest):
    """C{UserProfile} TestCase
    """
    def test_add_application_reference(self):
        profile = UserProfile(connection=self.trans, name="foo")
        assert not profile.profile_settings
        profile.add_application_reference(
            'my_app', has_permission=True)
        assert len(list(profile.profile_settings)) == 1
        assert profile.check_app_permission('my_app')

    def test_get_default(self):
        profile = UserProfile.get_default(self.trans)
        self.failUnless(isinstance(profile, UserProfile))
        self.assertEquals(profile.name, _('Salesperson'))


class TestProfileSettings(DomainTest):
    """{ProfileSettings} TestCase
    """
    def get_foreign_key_data(self):
        return [UserProfile(connection=self.trans, name='Manager')]

    def test_update_profile_applications(self):
        profile = UserProfile(connection=self.trans, name='assistant')

        profile.add_application_reference('stock',
                                          has_permission=True)
        items = profile.profile_settings
        assert len(list(items)) == 1

        new_profile = UserProfile(connection=self.trans, name='assistant')
        update_profile_applications(self.trans, new_profile)
        items = new_profile.profile_settings

    def test_create_profile_template(self):
        profile_name = 'Boss'
        table = UserProfile
        self.boss_profile = table.create_profile_template(self.trans,
                                                          profile_name,
                                                          has_full_permission=True)
        self.failIf(self.boss_profile.profile_settings)

    def test_check_app_permission(self):
        profile = UserProfile(connection=self.trans, name='boss')
        profile.add_application_reference('test_application', True)
        assert profile.check_app_permission('test_application') == True

    def test_set_permission(self):
        profile = UserProfile(connection=self.trans, name='boss')
        profile.add_application_reference('app', False)
        setting = ProfileSettings.selectOneBy(user_profile=profile,
                                             app_dir_name='app',
                                             connection=self.trans)
        self.failIf(setting.has_permission)
        ProfileSettings.set_permission(self.trans, profile, 'app', True)
        self.failUnless(setting.has_permission)
        ProfileSettings.set_permission(self.trans, profile, 'app', False)
        self.failIf(setting.has_permission)
