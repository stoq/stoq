-- Make transfers in two phases: a creation and a receival phase.

ALTER TABLE transfer_order ALTER COLUMN destination_responsible_id DROP NOT NULL;
ALTER TABLE transfer_order DROP CONSTRAINT valid_status;
ALTER TABLE transfer_order ADD CONSTRAINT valid_status CHECK (status >= 0 AND status <= 2);

ALTER TABLE transfer_order_item ADD COLUMN stock_cost numeric(20, 8) NOT NULL DEFAULT 0;
ALTER TABLE transfer_order_item ADD CONSTRAINT positive_stock_cost CHECK (stock_cost >= 0);
