-- Create a new column to allow configure baudrate.
ALTER TABLE ecf_printer ADD COLUMN baudrate integer;

-- Set baudrate according to existing fiscal printer model.
UPDATE ecf_printer SET baudrate = 9600;

UPDATE ecf_printer SET baudrate = 38400
    WHERE model = 'FBII';

UPDATE ecf_printer SET baudrate = 115200
    WHERE model in ('FBIII', 'Quick', 'Pay2023');

-- Change to not null
ALTER TABLE ecf_printer ALTER baudrate SET NOT NULL;

