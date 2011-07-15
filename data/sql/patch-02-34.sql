-- Add column 'device_name' on device_settings table
-- Migrate the data from 'device' to 'device_name'
--   'device':1 => 'device_name':'/dev/ttyS0'
--   'device':2 => 'device_name':'/dev/ttyS1'
--   'device':3 => Ignored
-- Remove columns 'device' from device_settings table

ALTER TABLE device_settings
    ADD COLUMN device_name text;

UPDATE device_settings
    SET device_name = '/dev/ttyS0' WHERE device = 1;
UPDATE device_settings
    SET device_name = '/dev/ttyS1' WHERE device = 2;

ALTER TABLE device_settings
    DROP COLUMN device;

ALTER TABLE device_settings
    ADD UNIQUE (device_name, station_id);

