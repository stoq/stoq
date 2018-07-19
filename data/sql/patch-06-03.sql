-- Dont fail if the column already exists (server database will have it)
-- Alternative to IF NOT EXISTS (that was introduced in postgres 9.6)
DO $$
BEGIN
    ALTER TABLE transaction_entry
        ADD COLUMN te_server timestamp DEFAULT statement_timestamp();
EXCEPTION
    WHEN duplicate_column THEN NULL;
END;
$$;

ALTER TABLE transaction_entry ADD COLUMN sync_status bit(1) NOT NULL DEFAULT 0::bit;
UPDATE transaction_entry SET sync_status = 1::bit where dirty = false;
ALTER TABLE transaction_entry DROP dirty;

-- Updates the transaction entry for the given id
CREATE OR REPLACE FUNCTION update_te(te_id bigint) RETURNS void AS $$
BEGIN
    UPDATE transaction_entry SET te_time = STATEMENT_TIMESTAMP(), sync_status = DEFAULT WHERE id = $1;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION new_te() RETURNS integer AS $$
    DECLARE te_id integer;
BEGIN
    INSERT INTO transaction_entry (te_time) VALUES (STATEMENT_TIMESTAMP()) RETURNING id INTO te_id;
    RETURN te_id;
END;
$$ LANGUAGE plpgsql;

