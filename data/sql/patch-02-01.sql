ALTER TABLE purchase_order
    ADD COLUMN consigned boolean default false;

ALTER TABLE purchase_order DROP CONSTRAINT valid_status;
ALTER TABLE purchase_order ADD CONSTRAINT valid_status
    CHECK (status >= 0 AND status < 6);

ALTER TABLE purchase_item
    ADD COLUMN quantity_sold numeric(10, 2) DEFAULT 0 CONSTRAINT positive_quantity_sold CHECK (quantity_sold >= 0 and quantity_sold <= quantity_received),
    ADD COLUMN quantity_returned numeric(10, 2) DEFAULT 0 CONSTRAINT positive_quantity_returned CHECK (quantity_returned >= 0 and quantity_returned <= quantity_received - quantity_sold);
