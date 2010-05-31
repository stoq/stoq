ALTER TABLE purchase_order
    ADD COLUMN consignment boolean default false;

ALTER TABLE purchase_order DROP CONSTRAINT valid_status;
ALTER TABLE purchase_order ADD CONSTRAINT valid_status
    CHECK (status >= 0 AND status < 6);
