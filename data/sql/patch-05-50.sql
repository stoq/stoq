CREATE TYPE certificate_type AS ENUM ('pkcs11', 'pkcs12');

CREATE TABLE certificate (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id BIGINT UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    active boolean DEFAULT true,
    name text DEFAULT '',
    type certificate_type NOT NULL,
    password bytea DEFAULT NULL,
    content bytea
);

CREATE RULE update_te AS ON UPDATE TO certificate DO ALSO SELECT update_te(old.te_id);
