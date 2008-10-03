CREATE TABLE ecf_printer (
    id bigserial NOT NULL PRIMARY KEY,
    is_valid_model boolean,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    model text NOT NULL,
    brand text NOT NULL,
    device_name text NOT NULL,
    device_serial text UNIQUE NOT NULL,
    station_id bigint REFERENCES branch_station(id) NOT NULL,
    is_active boolean
);

ALTER TABLE device_constant ADD COLUMN printer_id bigint REFERENCES ecf_printer(id);
ALTER TABLE device_constant DROP COLUMN device_settings_id;

