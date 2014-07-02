-- There was a typo in patch 02-39
ALTER TABLE production_order DROP CONSTRAINT IF EXISTS valid_statuos;
ALTER TABLE production_order DROP CONSTRAINT IF EXISTS valid_status;
ALTER TABLE production_order
    ADD CONSTRAINT valid_status CHECK (status >= 0 and status < 6);

ALTER TABLE production_order ADD COLUMN cancel_date timestamp;
