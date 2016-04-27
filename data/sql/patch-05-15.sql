CREATE TABLE plugin_egg (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id bigint UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    plugin_name text UNIQUE NOT NULL,
    egg_md5sum text DEFAULT NULL,
    egg_content bytea DEFAULT NULL
);
CREATE RULE update_te AS ON UPDATE TO plugin_egg DO ALSO SELECT update_te(old.te_id);
