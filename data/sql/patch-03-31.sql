-- Remove te_created_id and te_modified_id from event

ALTER TABLE event DROP CONSTRAINT event_te_created_id_fkey;
ALTER TABLE event DROP CONSTRAINT event_te_modified_id_fkey;
DELETE FROM transaction_entry t USING event e
    WHERE e.te_created_id = t.id or e.te_modified_id = t.id;
ALTER TABLE event DROP COLUMN te_created_id;
ALTER TABLE event DROP COLUMN te_modified_id;
