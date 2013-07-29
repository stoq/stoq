-- Rename 'maintenance' app to 'services'

UPDATE profile_settings
    SET app_dir_name = 'services' WHERE app_dir_name = 'maintenance';
