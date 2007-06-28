-- #3445: Factor ECF out of stoqlib to plugin
ALTER TABLE fiscal_day_history ADD COLUMN station_id bigint REFERENCES branch_station(id);

UPDATE fiscal_day_history 
   SET station_id = device_settings.station_id
  FROM device_settings
 WHERE device_settings.id = fiscal_day_history.device_id;

ALTER TABLE fiscal_day_history DROP COLUMN device_id;

