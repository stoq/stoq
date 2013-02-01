# -*- coding: utf-8 -*-
# #4504: Calendar application
from stoqlib.database.properties import UnicodeCol, BoolCol, IntCol
from stoqlib.migration.domainv1 import Domain


class ProfileSettings(Domain):
    __storm_table__ = 'profile_settings'
    app_dir_name = UnicodeCol()
    has_permission = BoolCol(default=False)
    user_profile_id = IntCol()


def apply_patch(store):
    profiles = store.find(ProfileSettings, app_dir_name=u'admin')
    for profile in profiles:
        ProfileSettings(app_dir_name=u'calendar',
                        has_permission=profile.has_permission,
                        user_profile_id=profile.user_profile_id,
                        store=store)
