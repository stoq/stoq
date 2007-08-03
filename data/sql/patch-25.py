#2300: Implementar esqueleto inicial da aplicação de inventário.
# copy warehouse's profile to the inventory app
from stoqlib.domain.profile import ProfileSettings

def apply_patch(trans):
    profiles = ProfileSettings.selectBy(app_dir_name='warehouse',
                                        connection=trans)
    for profile in profiles:
        ProfileSettings(app_dir_name='inventory',
                       has_permission=profile.has_permission,
                       user_profile=profile.user_profile,
                       connection=trans)
