# -*- coding: utf-8 -*-

# #4504: Calendar application
from stoqlib.domain.profile import ProfileSettings

def apply_patch(trans):
    profiles = ProfileSettings.selectBy(app_dir_name='admin',
                                        connection=trans)
    for profile in profiles:
        ProfileSettings(app_dir_name='calendar',
                       has_permission=profile.has_permission,
                       user_profile=profile.user_profile,
                       connection=trans)
