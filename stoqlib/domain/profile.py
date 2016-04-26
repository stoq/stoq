# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" User profile management for applications"""

# pylint: enable=E1101

from kiwi.component import get_utility
from storm.expr import And, Eq
from storm.references import Reference, ReferenceSet

from stoqlib.database.properties import BoolCol, IdCol, PercentCol, UnicodeCol
from stoqlib.domain.base import Domain
from stoqlib.lib.interfaces import IApplicationDescriptions
from stoqlib.lib.translation import stoqlib_gettext as _


class ProfileSettings(Domain):
    """Profile settings for user profile instances. Each instance of this
    class stores information about the access availability in a certain
    application."""

    __storm_table__ = 'profile_settings'

    #: The user profile that has these settings.
    user_profile_id = IdCol()

    user_profile = Reference(user_profile_id, 'UserProfile.id')

    #: The app name this user has or does not have access to.
    app_dir_name = UnicodeCol()

    #: Has this user permission to use this app?
    has_permission = BoolCol(default=False)

    #: Virtual apps. They will have permission if one of the apps mapped
    #: on the list have permission
    virtual_apps = {
        'link': ['admin'],
    }

    @classmethod
    def get_permission(cls, store, profile, app):
        """Check if a profile has access to an app

        :param store: A store
        :param profile: The :class:`.UserProfile` to check for permission
        :param app: The name of the application
        :return: Whether the profile has access to the profile or not
        """
        apps = [app] + cls.virtual_apps.get(app, [])
        res = store.find(
            cls, And(cls.user_profile_id == profile.id,
                     Eq(cls.has_permission, True),
                     cls.app_dir_name.is_in(apps)))
        res.config(limit=1)
        return res.one() is not None

    @classmethod
    def set_permission(cls, store, profile, app, permission):
        """
        Set the permission for a user profile to use a application
        :param store: a store
        :param profile: a UserProfile
        :param app: name of the application
        :param permission: a boolean of the permission
        """
        setting = store.find(cls, user_profile=profile,
                             app_dir_name=app).one()
        setting.has_permission = permission


class UserProfile(Domain):
    """User profile definition."""

    __storm_table__ = 'user_profile'

    #: Name of the user profile.
    name = UnicodeCol()

    #: Profile settings that describes the access this profile has to an app.
    profile_settings = ReferenceSet('id', 'ProfileSettings.user_profile_id')

    #: Maximum discount this profile can allow to sale items.
    max_discount = PercentCol(default=0)

    @classmethod
    def create_profile_template(cls, store, name,
                                has_full_permission=False):
        profile = cls(store=store, name=name)
        descr = get_utility(IApplicationDescriptions)
        for app_dir in descr.get_application_names():
            ProfileSettings(store=store,
                            has_permission=has_full_permission,
                            app_dir_name=app_dir, user_profile=profile)
        return profile

    @classmethod
    def get_default(cls, store):
        # FIXME: We need a way to set the default profile in the interface,
        # instead of relying on the name (the user may change it)
        profile = store.find(cls, name=_(u'Salesperson')).one()
        # regression: check if it was not created in english.
        if not profile:
            profile = store.find(cls, name=u'Salesperson').one()

        # Just return any other profile, so that the user is created with
        # one.
        if not profile:
            profile = store.find(cls).any()
        return profile

    def add_application_reference(self, app_name, has_permission=False):
        return ProfileSettings(
            store=self.store,
            app_dir_name=app_name,
            has_permission=has_permission,
            user_profile=self)

    def check_app_permission(self, app_name):
        """Check if the user has permission to use an application
        :param app_name: name of application to check
        """
        return ProfileSettings.get_permission(self.store, self, app_name)

    def get_permissions(self):
        apps = {setting.app_dir_name: setting.has_permission
                for setting in self.profile_settings}
        for virtual_app, references in ProfileSettings.virtual_apps.iteritems():
            apps[virtual_app] = any(apps.get(r, False) for r in references)

        return apps


def update_profile_applications(store, profile=None):
    """This method checks for all available applications and perform a
    comparision with the application names stored in user profiles. If a
    certain application is not there it is added.
    """
    app_list = get_utility(IApplicationDescriptions).get_application_names()
    profiles = profile and [profile] or store.find(UserProfile)
    for app_name in app_list:
        for profile in profiles:
            settings = profile.profile_settings
            app_names = [s.app_dir_name for s in settings]
            if not app_name in app_names:
                profile.add_application_reference(app_name)
