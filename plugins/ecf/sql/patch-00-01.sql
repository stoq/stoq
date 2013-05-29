CREATE TABLE ecf_printer (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    is_valid_model boolean,
    te_id bigint UNIQUE REFERENCES transaction_entry(id),
    model text NOT NULL,
    brand text NOT NULL,
    device_name text NOT NULL,
    device_serial text UNIQUE NOT NULL,
    station_id uuid REFERENCES branch_station(id) NOT NULL,
    is_active boolean
);

ALTER TABLE device_constant ADD COLUMN printer_id uuid REFERENCES ecf_printer(id);
ALTER TABLE device_constant DROP COLUMN device_settings_id;

