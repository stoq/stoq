-- Remove salesperson reference from commission.
-- The sale already has a reference and that should be used.

ALTER TABLE commission DROP COLUMN salesperson_id;
