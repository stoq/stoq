CREATE TYPE sale_token_status AS ENUM ('available', 'occupied');

CREATE TABLE sale_token (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v1(),
    te_id BIGINT UNIQUE REFERENCES transaction_entry(id) DEFAULT new_te(),
    status sale_token_status DEFAULT 'available',
    code TEXT UNIQUE
);

ALTER TABLE sale ADD COLUMN sale_token_id uuid REFERENCES sale_token(id);
