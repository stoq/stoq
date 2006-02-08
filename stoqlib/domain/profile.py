# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
""" User profile management for applications"""


from sqlobject import StringCol, ForeignKey, MultipleJoin, BoolCol

from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.lib.runtime import get_application_names
from stoqlib.domain.base import Domain
    

class ProfileSettings(Domain):
    """Profile settings for user profile instances. Each instance of this
    class stores information about the access availability in a certain
    application."""

    app_dir_name = StringCol()
    has_permission = BoolCol(default=False)
    user_profile = ForeignKey('UserProfile')
    

class UserProfile(Domain):
    """User profile definition."""

    name = StringCol()
    profile_settings = MultipleJoin('ProfileSettings')

    @classmethod
    def create_profile_template(cls, conn, name, 
                                has_full_permission=False):
        profile = cls(connection=conn, name=name)
        for app_dir in get_application_names():
            ProfileSettings(connection=conn,
                            has_permission=has_full_permission,
                            app_dir_name=app_dir, user_profile=profile)
        return profile

    def add_application_reference(self, app_name, has_permission=False):
        conn = self.get_connection()
        ProfileSettings(connection=conn, app_dir_name=app_name,
                        has_permission=has_permission, user_profile=self)

    def check_app_permission(self, app_name):
        settings = [s for s in self.profile_settings 
                            if s.app_dir_name == app_name 
                                    and s.has_permission]
        if not settings:
            return False
        if len(settings) > 1:
            raise DatabaseInconsistency("You should have only one "
                                        "ProfileSettings instance for "
                                        "directory name %s, got %d" 
                                        % (app_name, len(settings)))
        return True


def update_profile_applications(conn, profile=None):
    """This method checks for all available applications and perform a
    comparision with the application names stored in user profiles. If a
    certain application is not there it is added.
    """
    app_list = [app_name for app_name in get_application_names()]
    profiles = profile and [profile] or UserProfile.select(connection=conn)
    for app_name in app_list:
        for profile in profiles:
            settings = profile.profile_settings
            app_names = [s.app_dir_name for s in settings]
            if not app_name in app_names:
                profile.add_application_reference(app_name)
