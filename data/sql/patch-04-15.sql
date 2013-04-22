-- Update sellable statuses

-- Before:
--   AVAILABLE:   0
--   UNAVAILABLE: 1
--   CLOSED:      2
--   BLOCKED:     3
--
-- Now:
--   AVAILABLE:   0
--   CLOSED:      1

-- Old UNAVAILABLE will turn to AVAILABLE for products
-- For services it's already right since the user could choose and set
-- the service as UNAVAILABLE if he didn't want it to be sold, so let it
-- as 1 because it's the number for CLOSED.
UPDATE sellable SET status = 0 FROM product WHERE
    sellable.id = product.sellable_id AND sellable.status = 1;

-- Migrate CLOSED to it's new number for both products and services
UPDATE sellable SET status = 1 WHERE status = 2;

-- Old BLOCKED will turn to CLOSED for both products and services
UPDATE sellable SET status = 1 WHERE status = 3;

-- The valid_status now is 0 or 1
ALTER TABLE sellable DROP CONSTRAINT valid_status;
ALTER TABLE sellable
    ADD CONSTRAINT valid_status CHECK (status >= 0 AND status <= 1);
