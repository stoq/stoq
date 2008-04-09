-- #3679: Rename warehouse to stock

UPDATE profile_settings
    SET app_dir_name='stock'
    WHERE app_dir_name='warehouse';
