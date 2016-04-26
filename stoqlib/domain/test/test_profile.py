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

__tests__ = 'stoqlib/domain/profile.py'

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
        profile = UserProfile(store=self.store, name=u"foo")
        assert profile.profile_settings.count() == 0
        profile.add_application_reference(
            u'my_app', has_permission=True)
        assert len(list(profile.profile_settings)) == 1
        assert profile.check_app_permission(u'my_app')

    def test_get_default(self):
        profile = UserProfile.get_default(self.store)
        self.failUnless(isinstance(profile, UserProfile))
        self.assertEquals(profile.name, _(u'Salesperson'))

        # Change Salesperson's profile name so get_default won't find it
        # and it will fallback to any
        profile.name = u'XXX'
        profile2 = UserProfile.get_default(self.store)
        self.assertTrue(isinstance(profile2, UserProfile))
        self.assertIn(profile2, self.store.find(UserProfile))


class TestProfileSettings(DomainTest):
    """{ProfileSettings} TestCase
    """
    def get_foreign_key_data(self):
        return [UserProfile(store=self.store, name=u'Manager')]

    def test_update_profile_applications(self):
        profile = UserProfile(store=self.store, name=u'assistant')

        profile.add_application_reference(u'stock',
                                          has_permission=True)
        items = profile.profile_settings
        assert len(list(items)) == 1

        new_profile = UserProfile(store=self.store, name=u'assistant')
        update_profile_applications(self.store, new_profile)
        items = new_profile.profile_settings

    def test_check_app_permission(self):
        profile = UserProfile(store=self.store, name=u'boss')
        profile.add_application_reference(u'test_application', True)
        assert profile.check_app_permission(u'test_application') is True

    def test_set_permission(self):
        profile = UserProfile(store=self.store, name=u'boss')
        profile.add_application_reference(u'app', False)
        setting = self.store.find(ProfileSettings, user_profile=profile,
                                  app_dir_name=u'app').one()
        self.failIf(setting.has_permission)
        ProfileSettings.set_permission(self.store, profile, u'app', True)
        self.failUnless(setting.has_permission)
        ProfileSettings.set_permission(self.store, profile, u'app', False)
        self.failIf(setting.has_permission)

    def test_get_permissions(self):
        profile = UserProfile(store=self.store, name=u'boss')
        profile.add_application_reference(u'app1', False)
        profile.add_application_reference(u'app2', True)
        profile.add_application_reference(u'app3', False)

        self.assertEqual(profile.get_permissions(),
                         {'app1': False,
                          'app2': True,
                          'app3': False,
                          'link': False})

        admin_ps = profile.add_application_reference(u'admin', False)
        self.assertEqual(profile.get_permissions(),
                         {'app1': False,
                          'app2': True,
                          'app3': False,
                          'admin': False,
                          'link': False})

        admin_ps.has_permission = True
        self.assertEqual(profile.get_permissions(),
                         {'app1': False,
                          'app2': True,
                          'app3': False,
                          'admin': True,
                          'link': True})
