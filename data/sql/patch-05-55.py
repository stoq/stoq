# -*- coding: utf-8 -*-

from stoqlib.database.properties import UnicodeCol, IdCol, BoolCol
from stoqlib.migration.domainv4 import Domain


class ProfileSettings(Domain):
    __storm_table__ = 'profile_settings'

    app_dir_name = UnicodeCol()
    has_permission = BoolCol(default=False)
    user_profile_id = IdCol()


class UserProfile(Domain):
    __storm_table__ = 'user_profile'

    name = UnicodeCol()

    def add_application_reference(self, app_name, has_permission):
        store = self.store
        ProfileSettings(store=store, app_dir_name=app_name,
                        has_permission=has_permission, user_profile_id=self.id)

    def check_app_permission(self, app_name):
        store = self.store
        return bool(store.find(ProfileSettings, app_dir_name=app_name,
                               user_profile_id=self.id, has_permission=True).one())


def apply_patch(store):
    # Add permission to anyone with permission to admin or sales
    for profile in store.find(UserProfile):
        has_permission = any([profile.check_app_permission('admin'),
                              profile.check_app_permission('sales')])

        setting = store.find(ProfileSettings, user_profile_id=profile.id,
                             app_dir_name='delivery').one()
        if not setting:
            profile.add_application_reference('delivery', has_permission)
        else:
            setting.has_permission = setting.has_permission or has_permission
