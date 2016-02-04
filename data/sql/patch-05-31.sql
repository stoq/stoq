-- this workaround is made because ADD VALUE cannot be used inside of a
-- transaction, so we are committing the transaction, add the new value and
-- opening a new transaction
commit;
ALTER TYPE transfer_order_status ADD VALUE 'cancelled';
begin;

ALTER TABLE transfer_order ADD COLUMN cancel_date timestamp;
ALTER TABLE transfer_order ADD COLUMN cancel_responsible_id uuid REFERENCES employee(id);
